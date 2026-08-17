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

    def get_historical_context(self, symbol: str) -> dict:
        try:
            history = yf.Ticker(symbol.strip().upper()).history(period="1y", interval="1d", auto_adjust=False)
            closes = history["Close"].dropna()
        except Exception:
            return {}
        if len(closes) < 2:
            return {}
        latest = Decimal(str(closes.iloc[-1]))
        periods = {"1_week": 5, "1_month": 21, "6_months": 126, "1_year": len(closes) - 1}
        performance = {}
        for name, offset in periods.items():
            start = Decimal(str(closes.iloc[max(0, len(closes) - 1 - offset)]))
            performance[name] = ((latest - start) / start * 100) if start else Decimal("0")
        daily_returns = closes.pct_change().dropna()
        volatility = Decimal(str(float(daily_returns.std() * (252 ** 0.5) * 100)))
        return {"performance": performance, "recent_high": Decimal(str(closes.max())), "recent_low": Decimal(str(closes.min())), "annualized_volatility": volatility, "period_start": closes.index[0].to_pydatetime(), "period_end": closes.index[-1].to_pydatetime()}

    def get_chart(self, symbol: str, period: str, interval: str) -> list[dict]:
        try:
            source_interval = "1wk" if interval == "2wk" else interval
            history = yf.Ticker(symbol.strip().upper()).history(period=period, interval=source_interval, auto_adjust=True)
            closes = history["Close"].dropna()
        except Exception:
            return []
        points = list(closes.items())[::2] if interval == "2wk" else list(closes.items())
        return [{"date": index.to_pydatetime(), "close": Decimal(str(value))} for index, value in points]

    def get_fundamentals(self, symbol: str) -> dict:
        try:
            info = yf.Ticker(symbol.strip().upper()).info
        except Exception:
            return {}
        fields = {
            "sector": info.get("sector"),
            "industry": info.get("industry"),
            "market_cap": info.get("marketCap"),
            "trailing_pe": info.get("trailingPE"),
            "forward_pe": info.get("forwardPE"),
            "dividend_yield": info.get("dividendYield"),
            "expense_ratio": info.get("annualReportExpenseRatio"),
        }
        return {key: value for key, value in fields.items() if value is not None}
