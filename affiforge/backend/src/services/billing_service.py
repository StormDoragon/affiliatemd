"""
Billing service: Handle subscriptions, payouts, and customer management.
Supports Stripe subscriptions (Starter $19, Pro $49, Elite $99) + 12% revenue share.
"""

from decimal import Decimal
from datetime import datetime

try:
    import stripe
except ImportError:
    stripe = None

from ..config import settings


class BillingService:
    """Stripe-based subscription and payout management."""
    
    def __init__(self):
        if stripe and settings.stripe_secret_key:
            stripe.api_key = settings.stripe_secret_key
    
    def create_checkout_session(
        self,
        customer_id: str | None,
        price_id: str,
        success_url: str,
        cancel_url: str,
        email: str,
    ) -> tuple[str, str | None]:
        """Create Stripe checkout session for subscription signup."""
        if not settings.stripe_secret_key or stripe is None:
            return (f"{success_url}?checkout=mock", customer_id)

        resolved_customer_id = customer_id
        if not resolved_customer_id:
            customer = stripe.Customer.create(email=email)
            resolved_customer_id = customer["id"]

        session = stripe.checkout.Session.create(
            customer=resolved_customer_id,
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url=success_url,
            cancel_url=cancel_url,
        )

        return (session["url"], resolved_customer_id)

    def create_profitshare_invoice(self, customer_id: str | None, amount: Decimal, description: str) -> str:
        """Create revenue-share credit/invoice for Elite user."""
        if not settings.stripe_secret_key or stripe is None or not customer_id:
            return "mock-invoice"

        try:
            invoice_item = stripe.InvoiceItem.create(
                customer=customer_id,
                amount=int(amount * 100),
                currency="usd",
                description=description,
            )
            invoice = stripe.Invoice.create(customer=customer_id, auto_advance=True)
            return str(invoice["id"])
        except Exception:
            return "invoice-failed"
    
    def process_refund(self, subscription_id: str, reason: str = "User earnings < $1 in 30 days") -> dict:
        """Issue refund for users who earned <$1 in first 30 days."""
        if not stripe or not subscription_id:
            return {"status": "error", "message": "Invalid subscription"}
        
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            latest_invoice = stripe.Invoice.retrieve(subscription.latest_invoice)
            
            # Create credit note (refund)
            credit_note = stripe.CreditNote.create(
                invoice=latest_invoice.id,
                reason="order_change",
                memo=reason,
                refund_amount=latest_invoice.amount_due,
            )
            
            return {
                "status": "success",
                "credit_note_id": credit_note.id,
                "refund_amount": latest_invoice.amount_due / 100,
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
