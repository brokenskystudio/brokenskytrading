from datetime import datetime, timezone
from decimal import Decimal

import yfinance as yf

from app.services.market_data.provider import Quote


class YFinanceProvider:
    name = "Yahoo Finance via yfinance"

    def get_quotes(self, symbols: list[str]) -> dict[str, Quote]:
        quotes: dict[str, Quote] = {}
        for raw_symbol in dict.fromkeys(symbols):
            symbol = raw_symbol.strip().upper()
            if not symbol:
                continue
            try:
                history = yf.Ticker(symbol).history(period="5d", interval="1d", auto_adjust=False)
            except Exception:
                # A single invalid symbol or provider failure should not hide other quotes.
                continue
            if history.empty or "Close" not in history:
                continue
            closes = history["Close"].dropna()
            if closes.empty:
                continue
            latest_timestamp = closes.index[-1].to_pydatetime()
            if latest_timestamp.tzinfo is None:
                latest_timestamp = latest_timestamp.replace(tzinfo=timezone.utc)
            quotes[symbol] = Quote(
                symbol=symbol,
                price=Decimal(str(closes.iloc[-1])),
                previous_close=Decimal(str(closes.iloc[-2])) if len(closes) > 1 else None,
                data_as_of=latest_timestamp,
                provider=self.name,
                delayed=True,
            )
        return quotes
