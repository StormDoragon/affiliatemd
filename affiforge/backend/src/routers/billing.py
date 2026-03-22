from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..dependencies import get_current_user, get_db
from ..models.user import User
from ..schemas.billing import (
    CheckoutSessionRequest,
    CheckoutSessionResponse,
    ProfitShareInvoiceRequest,
    ProfitShareInvoiceResponse,
    ProfitShareToggleRequest,
)
from ..services.billing_service import BillingService

router = APIRouter(prefix="/billing", tags=["billing"])


@router.post("/checkout-session", response_model=CheckoutSessionResponse)
def create_checkout_session(
    payload: CheckoutSessionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CheckoutSessionResponse:
    billing = BillingService()
    checkout_url, stripe_customer_id = billing.create_checkout_session(
        customer_id=current_user.stripe_customer_id,
        price_id=payload.price_id,
        success_url=payload.success_url,
        cancel_url=payload.cancel_url,
        email=current_user.email,
    )
    if stripe_customer_id and stripe_customer_id != current_user.stripe_customer_id:
        current_user.stripe_customer_id = stripe_customer_id
        db.add(current_user)
        db.commit()

    return CheckoutSessionResponse(checkout_url=checkout_url)


@router.post("/profitshare/toggle")
def toggle_profitshare(
    payload: ProfitShareToggleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, bool]:
    current_user.profitshare_enabled = payload.enabled
    db.add(current_user)
    db.commit()
    return {"profitshare_enabled": current_user.profitshare_enabled}


@router.post("/profitshare/invoice", response_model=ProfitShareInvoiceResponse)
def create_profitshare_invoice(
    payload: ProfitShareInvoiceRequest,
    _: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProfitShareInvoiceResponse:
    billing = BillingService()
    invoice_id = billing.create_profitshare_invoice(
        customer_id=current_user.stripe_customer_id,
        amount=payload.amount,
        description=payload.description,
    )
    return ProfitShareInvoiceResponse(invoice_id=invoice_id, status="created")
