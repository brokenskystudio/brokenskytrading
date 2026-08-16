from fastapi.testclient import TestClient
from datetime import datetime, timezone
from decimal import Decimal

from app.api.portfolios import market_data_provider
from app.services.market_data.provider import Quote


def create_portfolio(client: TestClient) -> dict:
    response = client.post(
        "/portfolios",
        json={"name": "Long Term", "risk_profile": "balanced", "cash_balance": "1250.50"},
    )
    assert response.status_code == 201
    return response.json()


def test_portfolio_survives_a_fresh_list_request(client: TestClient) -> None:
    created = create_portfolio(client)

    # A second request models a browser reload with no client-side state.
    response = client.get("/portfolios")

    assert response.status_code == 200
    assert response.json()[0]["id"] == created["id"]
    assert response.json()[0]["name"] == "Long Term"
    assert response.json()[0]["cash_balance"] == "1250.5000"


def test_portfolio_update_is_persisted(client: TestClient) -> None:
    portfolio = create_portfolio(client)

    response = client.put(
        f"/portfolios/{portfolio['id']}",
        json={"name": "Updated Research", "risk_profile": "aggressive", "cash_balance": "800"},
    )

    assert response.status_code == 200
    reloaded = client.get(f"/portfolios/{portfolio['id']}").json()
    assert reloaded["name"] == "Updated Research"
    assert reloaded["risk_profile"] == "aggressive"
    assert reloaded["cash_balance"] == "800.0000"


def test_holdings_survive_reload_and_are_normalized(client: TestClient) -> None:
    portfolio = create_portfolio(client)

    holding_response = client.post(
        f"/portfolios/{portfolio['id']}/holdings",
        json={"symbol": " voo ", "quantity": "2.5", "average_cost": "400", "notes": "Core ETF"},
    )

    assert holding_response.status_code == 201
    reloaded = client.get(f"/portfolios/{portfolio['id']}").json()
    assert reloaded["holdings"] == [
        {
            "id": holding_response.json()["id"],
            "symbol": "VOO",
            "quantity": "2.50000000",
            "average_cost": "400.0000",
            "notes": "Core ETF",
        }
    ]


def test_invalid_financial_values_are_rejected(client: TestClient) -> None:
    response = client.post(
        "/portfolios",
        json={"name": "Invalid", "cash_balance": "-1"},
    )
    assert response.status_code == 422

    portfolio = create_portfolio(client)
    response = client.post(
        f"/portfolios/{portfolio['id']}/holdings",
        json={"symbol": "AAPL", "quantity": "0", "average_cost": "100"},
    )
    assert response.status_code == 422

    portfolio = create_portfolio(client)
    response = client.post(
        f"/portfolios/{portfolio['id']}/holdings",
        json={"symbol": "NOTREAL", "quantity": "1", "average_cost": "100"},
    )
    assert response.status_code == 422


def test_security_search_is_local_and_returns_catalog_matches(client: TestClient) -> None:
    response = client.get("/market-data/search", params={"q": "microsoft"})

    assert response.status_code == 200
    matches = {security["symbol"]: security for security in response.json()}
    assert matches["MSFT"]["exchange"] == "NASDAQ"
    assert matches["MSFT"]["name"] == "Microsoft Corporation - Common Stock"


def test_deleting_portfolio_deletes_its_holdings(client: TestClient) -> None:
    portfolio = create_portfolio(client)
    client.post(
        f"/portfolios/{portfolio['id']}/holdings",
        json={"symbol": "AAPL", "quantity": "1", "average_cost": "100"},
    )

    response = client.delete(f"/portfolios/{portfolio['id']}")

    assert response.status_code == 204
    assert client.get(f"/portfolios/{portfolio['id']}").status_code == 404
    assert client.get("/portfolios").json() == []


def test_portfolio_quotes_use_provider_and_report_missing_symbols(client: TestClient, monkeypatch) -> None:
    portfolio = create_portfolio(client)
    client.post(
        f"/portfolios/{portfolio['id']}/holdings",
        json={"symbol": "AAPL", "quantity": "1", "average_cost": "100"},
    )
    client.post(
        f"/portfolios/{portfolio['id']}/holdings",
        json={"symbol": "MSFT", "quantity": "1", "average_cost": "100"},
    )

    monkeypatch.setattr(
        market_data_provider,
        "get_quotes",
        lambda symbols: {
            "AAPL": Quote(
                symbol="AAPL",
                price=Decimal("200.25"),
                previous_close=Decimal("199.00"),
                data_as_of=datetime.now(timezone.utc),
                provider="test-provider",
                delayed=True,
            )
        },
    )
    response = client.get(f"/portfolios/{portfolio['id']}/quotes")

    assert response.status_code == 200
    assert response.json()["quotes"][0]["symbol"] == "AAPL"
    assert response.json()["missing_symbols"] == ["MSFT"]
    assert response.json()["limitations"]


def test_adding_purchase_updates_weighted_average_and_history(client: TestClient) -> None:
    portfolio = create_portfolio(client)
    holding = client.post(
        f"/portfolios/{portfolio['id']}/holdings",
        json={"symbol": "AAPL", "quantity": "2", "average_cost": "100"},
    ).json()

    response = client.post(
        f"/holdings/{holding['id']}/purchases",
        json={"quantity": "2", "price": "120", "notes": "Second buy"},
    )

    assert response.status_code == 201
    detail = client.get(f"/holdings/{holding['id']}").json()
    assert detail["quantity"] == "4.00000000"
    assert detail["average_cost"] == "110.0000"
    assert len(detail["purchases"]) == 1


def test_analysis_preview_calculates_value_allocation_and_alerts(client: TestClient, monkeypatch) -> None:
    portfolio = create_portfolio(client)
    client.post(
        f"/portfolios/{portfolio['id']}/holdings",
        json={"symbol": "AAPL", "quantity": "2", "average_cost": "100"},
    )
    monkeypatch.setattr(
        market_data_provider,
        "get_quotes",
        lambda symbols: {"AAPL": Quote("AAPL", Decimal("120"), Decimal("119"), datetime.now(timezone.utc), "test", True)},
    )

    response = client.get(f"/portfolios/{portfolio['id']}/analysis-preview")

    assert response.status_code == 200
    body = response.json()
    assert body["total_value"] == "1490.50000000"
    assert body["positions"][0]["market_value"] == "240.00000000"
    assert body["positions"][0]["gain_loss"] == "40.000000000000"
    assert body["alerts"]


def test_analysis_is_saved_and_available_in_history(client: TestClient, monkeypatch) -> None:
    portfolio = create_portfolio(client)
    monkeypatch.setattr(market_data_provider, "get_quotes", lambda symbols: {})

    response = client.post(f"/portfolios/{portfolio['id']}/analyze")

    assert response.status_code == 201
    assert response.json()["id"] > 0
    history = client.get(f"/portfolios/{portfolio['id']}/analyses")
    assert history.status_code == 200
    assert len(history.json()) == 1
    assert history.json()[0]["metrics"]["portfolio_id"] == portfolio["id"]
