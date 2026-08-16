from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class QuoteResponse(BaseModel):
    symbol: str
    price: Decimal
    previous_close: Decimal | None
    data_as_of: datetime
    provider: str
    delayed: bool


class PortfolioQuotesResponse(BaseModel):
    quotes: list[QuoteResponse]
    missing_symbols: list[str]
    limitations: list[str]
