from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class AnalysisPosition(BaseModel):
    symbol: str
    quantity: Decimal
    average_cost: Decimal
    latest_price: Decimal
    market_value: Decimal
    gain_loss: Decimal
    allocation_percent: Decimal
    data_as_of: datetime


class AnalysisAlert(BaseModel):
    severity: str
    code: str
    message: str


class AnalysisPolicy(BaseModel):
    max_single_holding: Decimal
    minimum_cash: Decimal
    preferred_holdings: int


class AnalysisPreviewResponse(BaseModel):
    portfolio_id: int
    risk_profile: str
    total_value: Decimal
    cash_value: Decimal
    cash_percent: Decimal
    invested_value: Decimal
    total_gain_loss: Decimal
    positions: list[AnalysisPosition]
    alerts: list[AnalysisAlert]
    missing_symbols: list[str]
    policy: AnalysisPolicy
