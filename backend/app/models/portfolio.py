from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Portfolio(Base):
    __tablename__ = "portfolios"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    risk_profile: Mapped[str] = mapped_column(String(20), default="balanced")
    cash_balance: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=Decimal("0"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    holdings: Mapped[list["Holding"]] = relationship(
        back_populates="portfolio", cascade="all, delete-orphan", order_by="Holding.symbol"
    )


class Holding(Base):
    __tablename__ = "holdings"

    id: Mapped[int] = mapped_column(primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolios.id", ondelete="CASCADE"), index=True)
    symbol: Mapped[str] = mapped_column(String(12))
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 8))
    average_cost: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    portfolio: Mapped[Portfolio] = relationship(back_populates="holdings")
    purchases: Mapped[list["HoldingPurchase"]] = relationship(
        back_populates="holding", cascade="all, delete-orphan", order_by="HoldingPurchase.purchased_at.desc()"
    )


class HoldingPurchase(Base):
    __tablename__ = "holding_purchases"

    id: Mapped[int] = mapped_column(primary_key=True)
    holding_id: Mapped[int] = mapped_column(ForeignKey("holdings.id", ondelete="CASCADE"), index=True)
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 8))
    price: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    purchased_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    holding: Mapped[Holding] = relationship(back_populates="purchases")
