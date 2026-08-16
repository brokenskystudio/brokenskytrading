from dataclasses import dataclass
from decimal import Decimal

from app.models.portfolio import Portfolio
from app.services.market_data.provider import Quote


@dataclass(frozen=True)
class RiskPolicy:
    max_single_holding: Decimal
    minimum_cash: Decimal
    preferred_holdings: int


POLICIES = {
    "conservative": RiskPolicy(Decimal("10"), Decimal("10"), 8),
    "balanced": RiskPolicy(Decimal("15"), Decimal("5"), 6),
    "aggressive": RiskPolicy(Decimal("25"), Decimal("0"), 4),
}


def build_analysis(portfolio: Portfolio, quotes: dict[str, Quote]) -> dict:
    policy = POLICIES[portfolio.risk_profile]
    cash = portfolio.cash_balance
    positions = []
    missing_symbols = []
    invested_value = Decimal("0")

    for holding in portfolio.holdings:
        quote = quotes.get(holding.symbol)
        if quote is None:
            missing_symbols.append(holding.symbol)
            continue
        market_value = holding.quantity * quote.price
        cost_value = holding.quantity * holding.average_cost
        invested_value += market_value
        positions.append({
            "symbol": holding.symbol,
            "quantity": holding.quantity,
            "average_cost": holding.average_cost,
            "latest_price": quote.price,
            "market_value": market_value,
            "gain_loss": market_value - cost_value,
            "data_as_of": quote.data_as_of,
        })

    total_value = cash + invested_value
    for position in positions:
        position["allocation_percent"] = (position["market_value"] / total_value * 100) if total_value else Decimal("0")
    cash_percent = (cash / total_value * 100) if total_value else Decimal("0")
    alerts = []
    for position in positions:
        if position["allocation_percent"] > policy.max_single_holding:
            alerts.append({
                "severity": "warning",
                "code": "single_holding_concentration",
                "message": f"{position['symbol']} is {position['allocation_percent']:.2f}% of the portfolio, above the {policy.max_single_holding}% policy limit.",
            })
    if cash_percent < policy.minimum_cash:
        alerts.append({
            "severity": "warning",
            "code": "cash_below_target",
            "message": f"Cash is {cash_percent:.2f}% of the portfolio, below the {policy.minimum_cash}% policy target.",
        })
    if len(portfolio.holdings) < policy.preferred_holdings:
        alerts.append({
            "severity": "info",
            "code": "few_holdings",
            "message": f"This portfolio has {len(portfolio.holdings)} holdings; the selected profile prefers {policy.preferred_holdings} or more.",
        })
    return {
        "portfolio_id": portfolio.id,
        "risk_profile": portfolio.risk_profile,
        "total_value": total_value,
        "cash_value": cash,
        "cash_percent": cash_percent,
        "invested_value": invested_value,
        "total_gain_loss": sum((position["gain_loss"] for position in positions), Decimal("0")),
        "positions": positions,
        "alerts": alerts,
        "missing_symbols": sorted(missing_symbols),
        "policy": {
            "max_single_holding": policy.max_single_holding,
            "minimum_cash": policy.minimum_cash,
            "preferred_holdings": policy.preferred_holdings,
        },
    }
