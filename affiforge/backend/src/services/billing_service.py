from hashlib import sha256

import stripe
from fastapi import HTTPException

from ..config import settings
from .provider_errors import IntegrationFailed, IntegrationUnavailable


class SubscriptionBilling:
    def __init__(self):
        self.enabled = not settings.demo_mode and bool(
            settings.stripe_secret_key and settings.billing_prices
        )
        self.client = stripe.StripeClient(
            settings.stripe_secret_key,
            http_client=stripe.RequestsClient(timeout=8),
        )

    def require_configuration(self):
        if not self.enabled:
            raise IntegrationUnavailable("Stripe")

    def create_customer(self, user_id: int, email: str) -> str:
        # The key ties recovery after an interrupted request to the local account.
        customer_key = sha256(f"{settings.app_origin}|{user_id}|{email}".encode()).hexdigest()
        try:
            customer = self.client.v1.customers.create(
                {"email": email, "metadata": {"affiforge_user_id": str(user_id)}},
                options={"idempotency_key": f"affiforge-customer-{customer_key}"},
            )
            return customer.id
        except stripe.StripeError as exc:
            raise IntegrationFailed("Stripe") from exc

    def prices(self) -> list[dict]:
        plans = []
        try:
            for price_id in sorted(settings.billing_prices):
                price = self.client.v1.prices.retrieve(price_id, {"expand": ["product"]})
                if price.active and price.recurring and price.unit_amount is not None:
                    plans.append(
                        {
                            "id": price.id,
                            "name": price.nickname
                            or getattr(price.product, "name", "Subscription"),
                            "amount": price.unit_amount,
                            "currency": price.currency.upper(),
                            "interval": price.recurring.interval,
                            "interval_count": price.recurring.interval_count,
                        }
                    )
        except stripe.StripeError as exc:
            raise IntegrationFailed("Stripe") from exc
        return plans

    def subscriptions(self, customer_id: str | None) -> list[dict]:
        if customer_id is None:
            return []
        try:
            page = self.client.v1.subscriptions.list(
                {"customer": customer_id, "status": "all", "limit": 20}
            )
            return [
                {"id": subscription.id, "status": subscription.status} for subscription in page.data
            ]
        except stripe.StripeError as exc:
            raise IntegrationFailed("Stripe") from exc

    def checkout(self, customer_id: str, price_id: str) -> str:
        try:
            configured_price = self.client.v1.prices.retrieve(price_id)
            if not configured_price.active or not configured_price.recurring:
                raise HTTPException(422, "This subscription is unavailable")
            if any(
                item["status"] not in {"canceled", "incomplete_expired"}
                for item in self.subscriptions(customer_id)
            ):
                raise HTTPException(409, "Manage your existing subscription in the billing portal")
            sessions = self.client.v1.checkout.sessions.list(
                {"customer": customer_id, "status": "open", "limit": 10},
            )
            for session in sessions.data:
                if session.mode != "subscription":
                    continue
                if session.metadata.get("affiforge_price_id") == price_id and session.url:
                    return session.url
                self.client.v1.checkout.sessions.expire(session.id)
            session = self.client.v1.checkout.sessions.create(
                {
                    "customer": customer_id,
                    "line_items": [{"price": price_id, "quantity": 1}],
                    "mode": "subscription",
                    "success_url": f"{settings.app_origin}/dashboard?billing=return#billing",
                    "cancel_url": f"{settings.app_origin}/dashboard#billing",
                    "metadata": {"affiforge_price_id": price_id},
                }
            )
            if not session.url:
                raise IntegrationFailed("Stripe")
            return session.url
        except stripe.StripeError as exc:
            raise IntegrationFailed("Stripe") from exc

    def portal(self, customer_id: str) -> str:
        try:
            session = self.client.v1.billing_portal.sessions.create(
                {
                    "customer": customer_id,
                    "return_url": f"{settings.app_origin}/dashboard#billing",
                }
            )
            return session.url
        except stripe.StripeError as exc:
            raise IntegrationFailed("Stripe") from exc
