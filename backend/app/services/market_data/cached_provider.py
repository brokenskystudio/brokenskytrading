from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.market_cache import MarketDataCache
from app.services.market_data.provider import Quote
from app.services.market_data.yfinance_provider import YFinanceProvider


class CachedMarketDataProvider:
    name = YFinanceProvider.name

    def __init__(self, provider: YFinanceProvider):
        self.provider = provider

    def _read(self, key: str) -> dict | list | None:
        with SessionLocal() as db:
            cached = db.get(MarketDataCache, key)
            expires_at = cached.expires_at.replace(tzinfo=timezone.utc) if cached and cached.expires_at.tzinfo is None else cached.expires_at if cached else None
            if cached and expires_at and expires_at > datetime.now(timezone.utc):
                return cached.payload
            if cached:
                db.delete(cached)
                db.commit()
        return None

    def _write(self, key: str, payload: dict | list, ttl_minutes: int) -> None:
        with SessionLocal() as db:
            cached = db.get(MarketDataCache, key)
            if cached:
                cached.payload = payload
                cached.expires_at = datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes)
            else:
                db.add(MarketDataCache(key=key, payload=payload, expires_at=datetime.now(timezone.utc) + timedelta(minutes=ttl_minutes)))
            db.commit()

    def get_quotes(self, symbols: list[str]) -> dict[str, Quote]:
        normalized = sorted(set(symbol.strip().upper() for symbol in symbols))
        key = f"quotes:{','.join(normalized)}"
        payload = self._read(key)
        if payload is None:
            quotes = self.provider.get_quotes(normalized)
            payload = [{"symbol": q.symbol, "price": str(q.price), "previous_close": str(q.previous_close) if q.previous_close is not None else None, "data_as_of": q.data_as_of.isoformat(), "provider": q.provider, "delayed": q.delayed} for q in quotes.values()]
            self._write(key, payload, 5)
        return {item["symbol"]: Quote(item["symbol"], Decimal(item["price"]), Decimal(item["previous_close"]) if item["previous_close"] else None, datetime.fromisoformat(item["data_as_of"]), item["provider"], item["delayed"]) for item in payload}

    def get_historical_context(self, symbol: str) -> dict:
        key = f"historical:{symbol.upper()}"
        payload = self._read(key)
        if payload is None:
            payload = self.provider.get_historical_context(symbol)
            self._write(key, {key: value.isoformat() if isinstance(value, datetime) else {name: str(item) for name, item in value.items()} if isinstance(value, dict) else str(value) for key, value in payload.items()}, 360)
            return payload
        return {key: {name: Decimal(item) for name, item in value.items()} if isinstance(value, dict) else datetime.fromisoformat(value) if key in {"period_start", "period_end"} else Decimal(value) for key, value in payload.items()}

    def get_chart(self, symbol: str, period: str, interval: str) -> list[dict]:
        key = f"chart:{symbol.upper()}:{period}:{interval}"
        payload = self._read(key)
        if payload is None:
            payload = [{"date": point["date"].isoformat(), "close": str(point["close"])} for point in self.provider.get_chart(symbol, period, interval)]
            self._write(key, payload, 60)
        return [{"date": datetime.fromisoformat(point["date"]), "close": Decimal(point["close"])} for point in payload]

    def get_fundamentals(self, symbol: str) -> dict:
        key = f"fundamentals:{symbol.upper()}"
        payload = self._read(key)
        if payload is None:
            payload = self.provider.get_fundamentals(symbol)
            self._write(key, payload, 1440)
        return payload
