from decimal import Decimal

from ..config import settings

try:
    import stripe
except ImportError:  # pragma: no cover
    stripe = None


class BillingService:
    def create_checkout_session(
        self,
        customer_id: str | None,
        price_id: str,
        success_url: str,
        cancel_url: str,
        email: str,
    ) -> tuple[str, str | None]:
        if not settings.stripe_secret_key or stripe is None:
            return (f"{success_url}?checkout=mock", customer_id)

        stripe.api_key = settings.stripe_secret_key

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
        if not settings.stripe_secret_key or stripe is None or not customer_id:
            return "mock-invoice"

        stripe.api_key = settings.stripe_secret_key
        invoice_item = stripe.InvoiceItem.create(
            customer=customer_id,
            amount=int(amount * 100),
            currency="usd",
            description=description,
        )
        invoice = stripe.Invoice.create(customer=customer_id, auto_advance=True)
        _ = invoice_item
        return str(invoice["id"])
