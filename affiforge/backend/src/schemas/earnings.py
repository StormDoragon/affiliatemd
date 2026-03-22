from pydantic import BaseModel, ConfigDict, Field


class EarningCreate(BaseModel):
    network: str
    amount: float = Field(gt=0)
    currency: str = "USD"
    content_item_id: int


class EarningRead(BaseModel):
    id: int
    network: str
    amount: float
    currency: str
    content_item_id: int
    owner_id: int

    model_config = ConfigDict(from_attributes=True)
