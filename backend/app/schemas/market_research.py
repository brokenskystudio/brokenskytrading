from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel

from app.schemas.market_data import QuoteResponse
from app.schemas.security import SecurityResponse


class MarketOverviewResponse(BaseModel):
    benchmarks: list[QuoteResponse]
    limitations: list[str]


class HistoricalContextResponse(BaseModel):
    performance: dict[str, Decimal]
    recent_high: Decimal
    recent_low: Decimal
    annualized_volatility: Decimal
    period_start: datetime
    period_end: datetime


class ChartPoint(BaseModel):
    date: datetime
    close: Decimal


class ChartResponse(BaseModel):
    symbol: str
    range: str
    interval: str
    points: list[ChartPoint]
    provider: str


class SecurityResearchResponse(BaseModel):
    security: SecurityResponse
    quote: QuoteResponse | None
    signals: list[str]
    change_percent: Decimal | None
    historical: HistoricalContextResponse | None
    fundamentals: dict[str, str | Decimal | int | float] | None
    limitations: list[str]


class ComparisonSecurity(BaseModel):
    security: SecurityResponse
    quote: QuoteResponse | None
    historical: HistoricalContextResponse | None
    fundamentals: dict[str, str | Decimal | int | float] | None
