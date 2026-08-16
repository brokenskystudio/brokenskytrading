from scripts.update_security_catalog import catalog_rows


def test_catalog_rows_normalizes_active_listings_and_excludes_test_symbols() -> None:
    rows = catalog_rows(
        [
            {"Symbol": "QQQ", "Security Name": "Invesco QQQ Trust", "ETF": "Y", "Test Issue": "N"},
            {"Symbol": "ZTEST", "Security Name": "Test Symbol", "ETF": "N", "Test Issue": "Y"},
        ],
        [
            {
                "ACT Symbol": "SCCO",
                "Security Name": "Southern Copper Corporation Common Stock",
                "Exchange": "N",
                "ETF": "N",
                "Test Issue": "N",
            },
            {
                "ACT Symbol": "SPY",
                "Security Name": "SPDR S&P 500 ETF Trust",
                "Exchange": "P",
                "ETF": "Y",
                "Test Issue": "N",
            },
            {
                "ACT Symbol": "XTEST",
                "Security Name": "Test Symbol",
                "Exchange": "Z",
                "ETF": "N",
                "Test Issue": "Y",
            },
        ],
        "nasdaq_trader_2026-08-15",
    )

    assert rows == [
        {
            "symbol": "QQQ",
            "name": "Invesco QQQ Trust",
            "exchange": "NASDAQ",
            "asset_type": "etf",
            "is_active": "true",
            "source": "nasdaq_trader_2026-08-15",
        },
        {
            "symbol": "SCCO",
            "name": "Southern Copper Corporation Common Stock",
            "exchange": "NYSE",
            "asset_type": "equity",
            "is_active": "true",
            "source": "nasdaq_trader_2026-08-15",
        },
        {
            "symbol": "SPY",
            "name": "SPDR S&P 500 ETF Trust",
            "exchange": "NYSE Arca",
            "asset_type": "etf",
            "is_active": "true",
            "source": "nasdaq_trader_2026-08-15",
        },
    ]