from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.seed import seed_security_catalog
from app.models.portfolio import Holding, HoldingPurchase, Portfolio, utc_now
from app.models.analysis import AnalysisSnapshot
from app.schemas.portfolio import (
    HoldingCreate,
    HoldingResponse,
    HoldingDetailResponse,
    HoldingUpdate,
    PortfolioCreate,
    PortfolioResponse,
    PortfolioUpdate,
    PurchaseCreate,
    PurchaseResponse,
)
from app.schemas.market_data import PortfolioQuotesResponse, QuoteResponse
from app.schemas.analysis import AnalysisPreviewResponse, SavedAnalysisResponse
from app.services.portfolio_analysis import build_analysis
from app.services.ai.local_provider import LocalAnalysisProvider
from app.services.market_data.yfinance_provider import YFinanceProvider
from app.services.market_data.cached_provider import CachedMarketDataProvider
from app.models.security import Security
from app.schemas.security import SecurityResponse
from app.schemas.market_research import ChartResponse, ComparisonSecurity, MarketOverviewResponse, SecurityResearchResponse
from app.schemas.portfolio_fit import PortfolioFitResponse
from typing import Literal


router = APIRouter(prefix="/portfolios", tags=["portfolios"])
holdings_router = APIRouter(prefix="/holdings", tags=["holdings"])
market_data_router = APIRouter(prefix="/market-data", tags=["market-data"])
market_data_provider = CachedMarketDataProvider(YFinanceProvider())
analysis_provider = LocalAnalysisProvider()


@market_data_router.get("/overview", response_model=MarketOverviewResponse)
def market_overview() -> dict:
    benchmark_symbols = ["SPY", "QQQ", "IWM", "BND"]
    quotes = market_data_provider.get_quotes(benchmark_symbols)
    return {
        "benchmarks": [QuoteResponse.model_validate(quote, from_attributes=True) for quote in quotes.values()],
        "limitations": ["Market data is supplied by Yahoo Finance through the unofficial yfinance library.", "Prices may be delayed and are for research context only."],
    }


@market_data_router.get("/securities/{symbol}", response_model=SecurityResearchResponse)
def security_research(symbol: str, db: Session = Depends(get_db)) -> dict:
    security = db.scalar(select(Security).where(Security.symbol == symbol.strip().upper(), Security.is_active.is_(True)))
    if security is None:
        raise HTTPException(status_code=404, detail="Security not found in local catalog")
    quote = market_data_provider.get_quotes([security.symbol]).get(security.symbol)
    historical = market_data_provider.get_historical_context(security.symbol)
    fundamentals = market_data_provider.get_fundamentals(security.symbol)
    change_percent = None
    signals = ["Insufficient recent price data"]
    if quote and quote.previous_close:
        change_percent = (quote.price - quote.previous_close) / quote.previous_close * 100
        signals = ["Price increased from the previous close"] if change_percent > 0 else ["Price decreased from the previous close"] if change_percent < 0 else ["Price is unchanged from the previous close"]
    return {
        "security": security,
        "quote": QuoteResponse.model_validate(quote, from_attributes=True) if quote else None,
        "signals": signals,
        "change_percent": change_percent,
        "historical": historical or None,
        "fundamentals": fundamentals or None,
        "limitations": ["This view uses recent price context only; it is not a valuation or suitability assessment."],
    }


@market_data_router.get("/securities/{symbol}/chart", response_model=ChartResponse)
def security_chart(symbol: str, range: Literal["1m", "6m", "1y", "2y"] = Query("1m"), db: Session = Depends(get_db)) -> dict:
    security = db.scalar(select(Security).where(Security.symbol == symbol.strip().upper(), Security.is_active.is_(True)))
    if security is None:
        raise HTTPException(status_code=404, detail="Security not found in local catalog")
    period, interval = {"1m": ("1mo", "1d"), "6m": ("6mo", "1wk"), "1y": ("1y", "1mo"), "2y": ("2y", "1mo")}[range]
    return {"symbol": security.symbol, "range": range, "interval": interval, "points": market_data_provider.get_chart(security.symbol, period, interval), "provider": market_data_provider.name}


@market_data_router.get("/compare", response_model=list[ComparisonSecurity])
def compare_securities(symbols: str = Query(..., min_length=1), db: Session = Depends(get_db)) -> list[dict]:
    requested = list(dict.fromkeys(symbol.strip().upper() for symbol in symbols.split(",") if symbol.strip()))[:4]
    securities = list(db.scalars(select(Security).where(Security.symbol.in_(requested), Security.is_active.is_(True))).all())
    quote_map = market_data_provider.get_quotes([security.symbol for security in securities])
    return [{"security": security, "quote": QuoteResponse.model_validate(quote_map[security.symbol], from_attributes=True) if security.symbol in quote_map else None, "historical": market_data_provider.get_historical_context(security.symbol) or None, "fundamentals": market_data_provider.get_fundamentals(security.symbol) or None} for security in securities]


def create_analysis(portfolio: Portfolio, quotes: dict) -> dict:
    metrics = build_analysis(portfolio, quotes)
    metrics.update(analysis_provider.explain(metrics))
    return metrics


def get_portfolio_or_404(portfolio_id: int, db: Session) -> Portfolio:
    portfolio = db.get(Portfolio, portfolio_id)
    if portfolio is None:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return portfolio


@market_data_router.get("/search", response_model=list[SecurityResponse])
def search_securities(q: str, db: Session = Depends(get_db)) -> list[Security]:
    if db.scalar(select(Security.id).limit(1)) is None:
        seed_security_catalog(db)
    query = q.strip().upper()
    if len(query) < 2:
        return []
    return list(
        db.scalars(
            select(Security)
            .where(Security.is_active.is_(True))
            .where(or_(Security.symbol.like(f"{query}%"), Security.name.ilike(f"%{q.strip()}%")))
            .order_by(Security.symbol)
            .limit(12)
        ).all()
    )


@router.get("", response_model=list[PortfolioResponse])
def list_portfolios(db: Session = Depends(get_db)) -> list[Portfolio]:
    return list(db.scalars(select(Portfolio).order_by(Portfolio.updated_at.desc())).all())


@router.post("", response_model=PortfolioResponse, status_code=status.HTTP_201_CREATED)
def create_portfolio(payload: PortfolioCreate, db: Session = Depends(get_db)) -> Portfolio:
    portfolio = Portfolio(**payload.model_dump())
    db.add(portfolio)
    db.commit()
    db.refresh(portfolio)
    return portfolio


@router.get("/{portfolio_id}", response_model=PortfolioResponse)
def get_portfolio(portfolio_id: int, db: Session = Depends(get_db)) -> Portfolio:
    return get_portfolio_or_404(portfolio_id, db)


@router.get("/{portfolio_id}/quotes", response_model=PortfolioQuotesResponse)
def get_portfolio_quotes(portfolio_id: int, db: Session = Depends(get_db)) -> PortfolioQuotesResponse:
    portfolio = get_portfolio_or_404(portfolio_id, db)
    symbols = [holding.symbol for holding in portfolio.holdings]
    quotes = market_data_provider.get_quotes(symbols)
    return PortfolioQuotesResponse(
        quotes=[QuoteResponse.model_validate(quote, from_attributes=True) for quote in quotes.values()],
        missing_symbols=sorted(set(symbols) - quotes.keys()),
        limitations=[
            "Data is supplied by Yahoo Finance through the unofficial yfinance library.",
            "Quotes may be delayed and are intended for local research, not trade execution.",
        ],
    )


@router.get("/{portfolio_id}/security-fit/{symbol}", response_model=PortfolioFitResponse)
def portfolio_security_fit(portfolio_id: int, symbol: str, db: Session = Depends(get_db)) -> dict:
    portfolio = get_portfolio_or_404(portfolio_id, db)
    security = db.scalar(select(Security).where(Security.symbol == symbol.strip().upper(), Security.is_active.is_(True)))
    if security is None:
        raise HTTPException(status_code=404, detail="Security not found in local catalog")
    holding_symbols = [holding.symbol for holding in portfolio.holdings]
    quotes = market_data_provider.get_quotes(holding_symbols)
    metrics = build_analysis(portfolio, quotes)
    existing = next((position for position in metrics["positions"] if position["symbol"] == security.symbol), None)
    fundamentals = market_data_provider.get_fundamentals(security.symbol)
    current_types = {item.asset_type for item in [db.scalar(select(Security).where(Security.symbol == holding.symbol)) for holding in portfolio.holdings] if item}
    sector = fundamentals.get("sector")
    context = ["This view describes portfolio overlap; it does not assess whether the security should be purchased."]
    if existing:
        context.append("This security is already held in the portfolio.")
    if security.asset_type in current_types:
        context.append(f"The portfolio already contains {security.asset_type} exposure.")
    if sector:
        context.append(f"The catalog provider reports this security in the {sector} sector.")
    return {"symbol": security.symbol, "portfolio_id": portfolio.id, "already_held": existing is not None, "current_quantity": next((holding.quantity for holding in portfolio.holdings if holding.symbol == security.symbol), Decimal("0")), "current_allocation_percent": existing["allocation_percent"] if existing else Decimal("0"), "asset_type": security.asset_type, "sector": sector, "portfolio_asset_type_overlap": security.asset_type in current_types, "portfolio_sector_overlap": False, "context": context}


@router.get("/{portfolio_id}/analysis-preview", response_model=AnalysisPreviewResponse)
def get_analysis_preview(portfolio_id: int, db: Session = Depends(get_db)) -> dict:
    portfolio = get_portfolio_or_404(portfolio_id, db)
    symbols = [holding.symbol for holding in portfolio.holdings]
    quotes = market_data_provider.get_quotes(symbols)
    return create_analysis(portfolio, quotes)


@router.post("/{portfolio_id}/analyze", response_model=SavedAnalysisResponse, status_code=status.HTTP_201_CREATED)
def analyze_portfolio(portfolio_id: int, db: Session = Depends(get_db)) -> dict:
    portfolio = get_portfolio_or_404(portfolio_id, db)
    symbols = [holding.symbol for holding in portfolio.holdings]
    quotes = market_data_provider.get_quotes(symbols)
    metrics = create_analysis(portfolio, quotes)
    data_as_of = max((quote.data_as_of for quote in quotes.values()), default=utc_now())
    snapshot = AnalysisSnapshot(
        portfolio_id=portfolio.id,
        data_as_of=data_as_of,
        market_provider=next(iter(quotes.values())).provider if quotes else "Yahoo Finance via yfinance",
        metrics_json=jsonable_encoder(metrics),
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return {"id": snapshot.id, "created_at": snapshot.created_at, "data_as_of": snapshot.data_as_of, "market_provider": snapshot.market_provider, "metrics": metrics}


@router.get("/{portfolio_id}/analyses", response_model=list[SavedAnalysisResponse])
def list_analyses(portfolio_id: int, db: Session = Depends(get_db)) -> list[dict]:
    get_portfolio_or_404(portfolio_id, db)
    snapshots = db.scalars(select(AnalysisSnapshot).where(AnalysisSnapshot.portfolio_id == portfolio_id).order_by(AnalysisSnapshot.created_at.desc())).all()
    return [{"id": snapshot.id, "created_at": snapshot.created_at, "data_as_of": snapshot.data_as_of, "market_provider": snapshot.market_provider, "metrics": snapshot.metrics_json} for snapshot in snapshots]


@router.put("/{portfolio_id}", response_model=PortfolioResponse)
def update_portfolio(portfolio_id: int, payload: PortfolioUpdate, db: Session = Depends(get_db)) -> Portfolio:
    portfolio = get_portfolio_or_404(portfolio_id, db)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(portfolio, field, value)
    portfolio.updated_at = utc_now()
    db.commit()
    db.refresh(portfolio)
    return portfolio


@router.delete("/{portfolio_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_portfolio(portfolio_id: int, db: Session = Depends(get_db)) -> None:
    portfolio = get_portfolio_or_404(portfolio_id, db)
    db.delete(portfolio)
    db.commit()


@router.post("/{portfolio_id}/holdings", response_model=HoldingResponse, status_code=status.HTTP_201_CREATED)
def create_holding(portfolio_id: int, payload: HoldingCreate, db: Session = Depends(get_db)) -> Holding:
    portfolio = get_portfolio_or_404(portfolio_id, db)
    if db.scalar(select(Security.id).where(Security.symbol == payload.symbol, Security.is_active.is_(True))) is None:
        raise HTTPException(status_code=422, detail="Select a valid security from the local catalog")
    holding = Holding(portfolio=portfolio, **payload.model_dump())
    db.add(holding)
    portfolio.updated_at = utc_now()
    db.commit()
    db.refresh(holding)
    return holding


@holdings_router.put("/{holding_id}", response_model=HoldingResponse)
def update_holding(holding_id: int, payload: HoldingUpdate, db: Session = Depends(get_db)) -> Holding:
    holding = db.get(Holding, holding_id)
    if holding is None:
        raise HTTPException(status_code=404, detail="Holding not found")
    for field, value in payload.model_dump().items():
        setattr(holding, field, value)
    holding.portfolio.updated_at = utc_now()
    db.commit()
    db.refresh(holding)
    return holding


@holdings_router.get("/{holding_id}", response_model=HoldingDetailResponse)
def get_holding(holding_id: int, db: Session = Depends(get_db)) -> Holding:
    holding = db.get(Holding, holding_id)
    if holding is None:
        raise HTTPException(status_code=404, detail="Holding not found")
    return holding


@holdings_router.post("/{holding_id}/purchases", response_model=PurchaseResponse, status_code=status.HTTP_201_CREATED)
def add_purchase(holding_id: int, payload: PurchaseCreate, db: Session = Depends(get_db)) -> HoldingPurchase:
    holding = db.get(Holding, holding_id)
    if holding is None:
        raise HTTPException(status_code=404, detail="Holding not found")
    old_quantity = holding.quantity
    old_value = old_quantity * holding.average_cost
    new_value = payload.quantity * payload.price
    holding.quantity = old_quantity + payload.quantity
    holding.average_cost = (old_value + new_value) / holding.quantity
    holding.portfolio.updated_at = utc_now()
    purchase = HoldingPurchase(holding=holding, **payload.model_dump())
    db.add(purchase)
    db.commit()
    db.refresh(purchase)
    return purchase


@holdings_router.delete("/{holding_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_holding(holding_id: int, db: Session = Depends(get_db)) -> None:
    holding = db.get(Holding, holding_id)
    if holding is None:
        raise HTTPException(status_code=404, detail="Holding not found")
    portfolio = holding.portfolio
    db.delete(holding)
    portfolio.updated_at = utc_now()
    db.commit()
