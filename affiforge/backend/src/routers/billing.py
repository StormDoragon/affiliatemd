from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..config import settings
from ..dependencies import enforce_provider_use, get_current_user, get_db
from ..models.user import User
from ..schemas.billing import (
    CheckoutSessionRequest,
    CheckoutSessionResponse,
    ProfitShareToggleRequest,
)
from ..services.billing_service import SubscriptionBilling

router = APIRouter(prefix="/billing", tags=["billing"])


@router.get("/status")
def billing_status(current_user: User = Depends(get_current_user)) -> dict:
    service = SubscriptionBilling()
    if not service.enabled:
        return {"enabled": False, "subscriptions": [], "prices": [], "portal_available": False}
    enforce_provider_use(current_user.id)
    return {
        "enabled": True,
        "prices": service.prices(),
        "subscriptions": service.subscriptions(current_user.stripe_customer_id),
        "portal_available": bool(current_user.stripe_customer_id),
    }


@router.post("/checkout-session", response_model=CheckoutSessionResponse)
def create_checkout_session(
    payload: CheckoutSessionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CheckoutSessionResponse:
    owner_id = current_user.id
    enforce_provider_use(owner_id)
    service = SubscriptionBilling()
    service.require_configuration()
    if payload.price_id not in settings.billing_prices:
        raise HTTPException(422, "Choose a configured subscription")
    user = db.query(User).filter(User.id == owner_id).populate_existing().with_for_update().one()
    if not user.stripe_customer_id:
        user.stripe_customer_id = service.create_customer(user.id, user.email)
        db.commit()
        user = (
            db.query(User).filter(User.id == owner_id).populate_existing().with_for_update().one()
        )
    checkout_url = service.checkout(user.stripe_customer_id, payload.price_id)
    db.commit()
    return CheckoutSessionResponse(checkout_url=checkout_url)


@router.post("/portal")
def billing_portal(current_user: User = Depends(get_current_user)) -> dict[str, str]:
    enforce_provider_use(current_user.id)
    service = SubscriptionBilling()
    service.require_configuration()
    if not current_user.stripe_customer_id:
        raise HTTPException(409, "Start checkout before opening the billing portal")
    return {"url": service.portal(current_user.stripe_customer_id)}


@router.post("/profitshare/toggle")
def toggle_profitshare(
    payload: ProfitShareToggleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, bool]:
    current_user.profitshare_enabled = payload.enabled
    db.commit()
    return {"profitshare_enabled": current_user.profitshare_enabled}


@router.post("/profitshare/invoice")
def retired_profitshare_invoicing(_: User = Depends(get_current_user)):
    raise HTTPException(
        410, "Self-reported earnings are for reporting and cannot create Stripe invoices"
    )
