from uuid import uuid4

from cryptography.fernet import Fernet
from fastapi.testclient import TestClient
from src.config import settings
from src.db import SessionLocal
from src.models.site import Site
from src.services.provider_errors import IntegrationFailed
from src.services.wordpress_service import WordpressService
from test_feature_flow import _auth_headers


def _draft(client, headers, slug="manual-draft"):
    response = client.post(
        "/content/",
        json={
            "title": "A manual draft",
            "slug": slug,
            "body": "Draft body",
        },
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_account_isolation_and_accurate_earnings(client: TestClient):
    alice = _auth_headers(client)
    bob = _auth_headers(client)
    alice_post = _draft(client, alice)
    bob_post = _draft(client, bob)
    assert alice_post != bob_post
    assert client.get("/users/", headers=alice).json() == [
        client.get("/users/me", headers=alice).json()
    ]
    assert client.get(f"/content/{alice_post}", headers=bob).status_code == 404
    assert (
        client.patch(
            f"/content/{alice_post}", headers=bob, json={"title": "New", "body": "New"}
        ).status_code
        == 404
    )

    entry = {
        "network": "Amazon",
        "currency": "USD",
        "amount": "0.29",
        "content_item_id": alice_post,
        "entry_key": str(uuid4()),
    }
    assert client.post("/earnings/", headers=bob, json=entry).status_code == 404
    assert (
        client.post("/earnings/", headers=alice, json={**entry, "currency": "EUR"}).status_code
        == 422
    )
    assert (
        client.post("/earnings/", headers=alice, json={**entry, "amount": "0.291"}).status_code
        == 422
    )
    first = client.post("/earnings/", headers=alice, json=entry)
    second = client.post("/earnings/", headers=alice, json=entry)
    assert first.status_code == second.status_code == 201
    assert first.json()["id"] == second.json()["id"]
    assert (
        client.post("/earnings/", headers=alice, json={**entry, "amount": "1.00"}).status_code
        == 409
    )
    assert client.get("/earnings/dashboard", headers=alice).json()["summary"]["revenue"] == 0.29
    assert client.get("/earnings/dashboard", headers=bob).json()["summary"]["revenue"] == 0


def test_live_publish_requires_confirmation_and_reuses_remote_receipt(client, monkeypatch):
    monkeypatch.setattr(settings, "demo_mode", False)
    monkeypatch.setattr(settings, "credential_encryption_key", Fernet.generate_key().decode())
    remote_posts = {}
    requests = []

    def wordpress_request(_, url, username, password, method, path, payload=None):
        assert password == "actual-app-password"
        assert url == "https://wp.example.com"
        requests.append((method, path))
        if path.startswith("users/me"):
            return {"capabilities": {"publish_posts": True}}
        if method == "GET":
            slug = path.split("slug=")[1].split("&")[0]
            return [remote_posts[slug]] if slug in remote_posts else []
        slug = payload["slug"]
        remote_posts[slug] = {"slug": slug, "status": "publish", "link": f"{url}/{slug}"}
        # Simulate a lost response after WordPress creates the post.
        raise IntegrationFailed("WordPress")

    monkeypatch.setattr(WordpressService, "_request", wordpress_request)
    headers = _auth_headers(client)
    post_id = _draft(client, headers)
    site = client.post(
        "/sites/",
        headers=headers,
        json={
            "wp_url": "https://wp.example.com",
            "wp_username": "editor",
            "wp_app_password": "actual-app-password",
        },
    )
    assert site.status_code == 201
    assert "actual-app-password" not in site.text
    with SessionLocal() as db:
        assert db.get(Site, site.json()["id"]).wp_app_password.startswith("fernet:")
        assert "actual-app-password" not in db.get(Site, site.json()["id"]).wp_app_password

    route = f"/content/{post_id}/publish"
    data = {"site_id": site.json()["id"]}
    assert client.post(route, headers=headers, json=data).status_code == 502
    assert client.get(f"/content/{post_id}", headers=headers).json()["status"] == "draft"
    success = client.post(route, headers=headers, json=data)
    assert success.status_code == 200
    assert success.json()["status"] == "published"
    assert success.json() == client.post(route, headers=headers, json=data).json()
    assert len([request for request in requests if request[0] == "POST"]) == 1


def test_missing_providers_and_closed_registration(client, monkeypatch):
    headers = _auth_headers(client)
    monkeypatch.setattr(settings, "demo_mode", False)
    monkeypatch.setattr(settings, "openai_api_key", "")
    monkeypatch.setattr(settings, "reddit_client_id", "")
    monkeypatch.setattr(settings, "allow_registration", False)
    assert client.get("/users/registration").json() == {"enabled": False}
    assert (
        client.post(
            "/users/register",
            json={
                "email": "new@example.com",
                "full_name": "New Person",
                "password": "strong-pass-123",
            },
        ).status_code
        == 403
    )
    assert (
        client.post(
            "/generator/cluster",
            headers=headers,
            json={
                "seed_keyword": "keyboards",
                "audience": "office workers",
            },
        ).status_code
        == 503
    )
    assert (
        client.post(
            "/generator/reddit-scan", headers=headers, json={"query": "keyboards"}
        ).status_code
        == 503
    )


def test_readiness_and_private_wordpress_rejection(client, monkeypatch):
    import socket

    assert client.get("/readyz").json() == {"status": "ready"}
    monkeypatch.setattr(
        socket,
        "getaddrinfo",
        lambda *_args, **_kw: [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443)),
        ],
    )
    monkeypatch.setattr(settings, "demo_mode", False)
    monkeypatch.setattr(settings, "credential_encryption_key", Fernet.generate_key().decode())
    headers = _auth_headers(client)
    response = client.post(
        "/sites/",
        headers=headers,
        json={
            "wp_url": "https://wp.example.com",
            "wp_username": "editor",
            "wp_app_password": "secret example",
        },
    )
    assert response.status_code == 422
    assert client.get("/sites/", headers=headers).json() == []


def test_stripe_checkout_rejects_unknown_prices_and_uses_configured_origin(client, monkeypatch):
    from types import SimpleNamespace

    from src.services import billing_service

    class FakeStripe:
        def __init__(self, *args, **kwargs):
            self.v1 = SimpleNamespace(
                customers=SimpleNamespace(create=self.create_customer),
                prices=SimpleNamespace(retrieve=self.get_price),
                subscriptions=SimpleNamespace(list=lambda _: SimpleNamespace(data=[])),
                checkout=SimpleNamespace(sessions=self),
            )

        def create_customer(self, payload, options):
            assert payload["email"].endswith("@example.com")
            assert options["idempotency_key"].startswith("affiforge-customer-")
            return SimpleNamespace(id="cus_configured")

        def get_price(self, price):
            assert price == "price_configured"
            return SimpleNamespace(active=True, recurring=True)

        def list(self, filters):
            assert filters["customer"] == "cus_configured"
            return SimpleNamespace(data=[])

        def create(self, payload):
            assert (
                payload["success_url"] == "https://app.example.com/dashboard?billing=return#billing"
            )
            assert payload["cancel_url"] == "https://app.example.com/dashboard#billing"
            assert payload["line_items"] == [{"price": "price_configured", "quantity": 1}]
            return SimpleNamespace(url="https://checkout.stripe.com/c/pay/test")

    monkeypatch.setattr(settings, "demo_mode", False)
    monkeypatch.setattr(settings, "stripe_secret_key", "test-configured-key")
    monkeypatch.setattr(settings, "stripe_price_ids", "price_configured")
    monkeypatch.setattr(settings, "app_origin", "https://app.example.com")
    monkeypatch.setattr(billing_service.stripe, "StripeClient", FakeStripe)
    auth = _auth_headers(client)
    assert (
        client.post(
            "/billing/checkout-session", headers=auth, json={"price_id": "unknown"}
        ).status_code
        == 422
    )
    checkout = client.post(
        "/billing/checkout-session",
        headers=auth,
        json={
            "price_id": "price_configured",
            "success_url": "https://untrusted.example.com",
        },
    )
    assert checkout.status_code == 200
    assert checkout.json()["checkout_url"] == "https://checkout.stripe.com/c/pay/test"


def test_live_generation_accepts_valid_provider_output(client, monkeypatch):
    import httpx
    from src.services import draft_generation

    monkeypatch.setattr(settings, "demo_mode", False)
    monkeypatch.setattr(settings, "openai_api_key", "test-configured-key")

    def generate(url, headers, json, timeout):
        assert url == "https://api.openai.com/v1/chat/completions"
        assert headers["Authorization"] == "Bearer test-configured-key"
        assert json["response_format"] == {"type": "json_object"}
        payload = (
            '{"items": ['
            + ",".join(
                '{"title":"Guide '
                + str(number)
                + '","keyword":"keyboard","search_intent":"research","brief":"Check sizes."}'
                for number in range(3)
            )
            + "]}"
        )
        return httpx.Response(
            200,
            request=httpx.Request("POST", url),
            json={
                "choices": [{"message": {"content": payload}, "finish_reason": "stop"}],
            },
        )

    monkeypatch.setattr(draft_generation.httpx, "post", generate)
    response = client.post(
        "/generator/cluster",
        headers=_auth_headers(client),
        json={
            "seed_keyword": "keyboards",
            "audience": "office workers",
            "cluster_size": 3,
        },
    )
    assert response.status_code == 200
    assert len(response.json()["items"]) == 3
    assert response.json()["demo"] is False
