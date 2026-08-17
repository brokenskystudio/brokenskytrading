from decimal import Decimal

from pydantic import BaseModel


class PortfolioFitResponse(BaseModel):
    symbol: str
    portfolio_id: int
    already_held: bool
    current_quantity: Decimal
    current_allocation_percent: Decimal
    asset_type: str
    sector: str | None
    portfolio_asset_type_overlap: bool
    portfolio_sector_overlap: bool
    context: list[str]
