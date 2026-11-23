from pydantic import BaseModel, Field


class CheckoutSessionRequest(BaseModel):
    price_id: str = Field(min_length=1, max_length=255)


class CheckoutSessionResponse(BaseModel):
    checkout_url: str


class ProfitShareToggleRequest(BaseModel):
    enabled: bool
