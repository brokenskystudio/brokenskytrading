from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RiskProfile(StrEnum):
    conservative = "conservative"
    balanced = "balanced"
    aggressive = "aggressive"


class HoldingBase(BaseModel):
    symbol: str = Field(min_length=1, max_length=12)
    quantity: Decimal = Field(gt=0)
    average_cost: Decimal = Field(gt=0)
    notes: str | None = Field(default=None, max_length=1000)

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, value: str) -> str:
        return value.strip().upper()


class HoldingCreate(HoldingBase):
    pass


class HoldingUpdate(HoldingBase):
    pass


class HoldingResponse(HoldingBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class PurchaseCreate(BaseModel):
    quantity: Decimal = Field(gt=0)
    price: Decimal = Field(gt=0)
    notes: str | None = Field(default=None, max_length=1000)


class PurchaseResponse(PurchaseCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    purchased_at: datetime


class HoldingDetailResponse(HoldingResponse):
    purchases: list[PurchaseResponse] = Field(default_factory=list)


class PortfolioCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    risk_profile: RiskProfile = RiskProfile.balanced
    cash_balance: Decimal = Field(default=Decimal("0"), ge=0)


class PortfolioUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    risk_profile: RiskProfile | None = None
    cash_balance: Decimal | None = Field(default=None, ge=0)


class PortfolioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    risk_profile: RiskProfile
    cash_balance: Decimal
    created_at: datetime
    updated_at: datetime
    holdings: list[HoldingResponse] = Field(default_factory=list)
