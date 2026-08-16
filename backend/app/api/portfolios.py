from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.seed import seed_security_catalog
from app.models.portfolio import Holding, HoldingPurchase, Portfolio, utc_now
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
from app.schemas.analysis import AnalysisPreviewResponse
from app.services.portfolio_analysis import build_analysis
from app.services.market_data.yfinance_provider import YFinanceProvider
from app.models.security import Security
from app.schemas.security import SecurityResponse


router = APIRouter(prefix="/portfolios", tags=["portfolios"])
holdings_router = APIRouter(prefix="/holdings", tags=["holdings"])
market_data_router = APIRouter(prefix="/market-data", tags=["market-data"])
market_data_provider = YFinanceProvider()


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


@router.get("/{portfolio_id}/analysis-preview", response_model=AnalysisPreviewResponse)
def get_analysis_preview(portfolio_id: int, db: Session = Depends(get_db)) -> dict:
    portfolio = get_portfolio_or_404(portfolio_id, db)
    symbols = [holding.symbol for holding in portfolio.holdings]
    quotes = market_data_provider.get_quotes(symbols)
    return build_analysis(portfolio, quotes)


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
