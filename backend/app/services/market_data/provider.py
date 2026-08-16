from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True)
class Quote:
    symbol: str
    price: Decimal
    previous_close: Decimal | None
    data_as_of: datetime
    provider: str
    delayed: bool


class MarketDataProvider(Protocol):
    def get_quotes(self, symbols: list[str]) -> dict[str, Quote]: ...
