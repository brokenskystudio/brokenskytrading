from pydantic import BaseModel, ConfigDict


class SecurityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    symbol: str
    name: str
    exchange: str
    asset_type: str
