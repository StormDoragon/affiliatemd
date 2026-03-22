from decimal import Decimal

from pydantic import BaseModel, Field


class CheckoutSessionRequest(BaseModel):
    price_id: str
    success_url: str
    cancel_url: str


class CheckoutSessionResponse(BaseModel):
    checkout_url: str


class ProfitShareToggleRequest(BaseModel):
    enabled: bool


class ProfitShareInvoiceRequest(BaseModel):
    amount: Decimal = Field(gt=0)
    description: str


class ProfitShareInvoiceResponse(BaseModel):
    invoice_id: str
    status: str
