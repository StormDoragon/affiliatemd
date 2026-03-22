import uuid

from fastapi.testclient import TestClient


def _auth_headers(client: TestClient) -> dict[str, str]:
    email = f"flow-{uuid.uuid4().hex[:8]}@example.com"
    password = "strong-pass-123"

    register = client.post(
        "/users/register",
        json={"email": email, "full_name": "Flow User", "password": password},
    )
    assert register.status_code == 201

    token = client.post("/users/token", json={"email": email, "password": password})
    assert token.status_code == 200
    return {"Authorization": f"Bearer {token.json()['access_token']}"}


def test_auth_site_scan_generate_publish_and_billing_flow(client: TestClient) -> None:
    headers = _auth_headers(client)

    site_resp = client.post(
        "/sites/",
        headers=headers,
        json={
            "wp_url": "https://example.com",
            "wp_username": "admin",
            "wp_app_password": "app-pass",
            "amazon_tag": "affiforge123",
        },
    )
    assert site_resp.status_code == 201
    site_id = site_resp.json()["id"]

    scan_resp = client.post(
        "/generator/reddit-scan",
        headers=headers,
        json={"query": "best espresso machine", "subreddit": "coffee", "limit": 3},
    )
    assert scan_resp.status_code == 200
    assert len(scan_resp.json()["topics"]) == 3
    first_topic = scan_resp.json()["topics"][0]

    gen_resp = client.post(
        "/generator/generate",
        headers=headers,
        json={
            "site_id": site_id,
            "primary_keyword": "best espresso machine",
            "reddit_thread_id": first_topic["thread_id"],
            "pain_point": first_topic["pain_point"],
        },
    )
    assert gen_resp.status_code == 201
    post_id = gen_resp.json()["post_id"]

    publish_resp = client.post(
        f"/content/{post_id}/publish",
        headers=headers,
        json={"site_id": site_id},
    )
    assert publish_resp.status_code == 200
    assert publish_resp.json()["status"] == "published"

    checkout_resp = client.post(
        "/billing/checkout-session",
        headers=headers,
        json={
            "price_id": "price_demo",
            "success_url": "https://app.example.com/success",
            "cancel_url": "https://app.example.com/cancel",
        },
    )
    assert checkout_resp.status_code == 200
    assert "checkout_url" in checkout_resp.json()

    toggle_resp = client.post("/billing/profitshare/toggle", headers=headers, json={"enabled": True})
    assert toggle_resp.status_code == 200
    assert toggle_resp.json()["profitshare_enabled"] is True

    invoice_resp = client.post(
        "/billing/profitshare/invoice",
        headers=headers,
        json={"amount": "42.50", "description": "March profit share"},
    )
    assert invoice_resp.status_code == 200
    assert invoice_resp.json()["status"] == "created"
