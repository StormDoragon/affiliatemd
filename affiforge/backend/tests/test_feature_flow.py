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

    cluster_resp = client.post(
        "/generator/cluster",
        headers=headers,
        json={"seed_keyword": "best mechanical keyboard", "audience": "remote workers", "cluster_size": 4},
    )
    assert cluster_resp.status_code == 200
    assert len(cluster_resp.json()["items"]) == 4

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

    earning_resp = client.post(
        "/earnings/",
        headers=headers,
        json={
            "network": "amazon",
            "amount": 18.75,
            "currency": "USD",
            "content_item_id": post_id,
        },
    )
    assert earning_resp.status_code == 201

    impact_resp = client.post(
        "/earnings/",
        headers=headers,
        json={
            "network": "impact",
            "amount": 12.25,
            "currency": "USD",
            "content_item_id": post_id,
        },
    )
    assert impact_resp.status_code == 201

    summary_resp = client.get("/earnings/summary", headers=headers)
    assert summary_resp.status_code == 200
    assert summary_resp.json()["revenue"] == 31.0

    profitshare_resp = client.get("/earnings/profitshare", headers=headers)
    assert profitshare_resp.status_code == 200
    assert profitshare_resp.json()["enabled"] is True
    assert profitshare_resp.json()["platform_share"] > 0

    suggestions_resp = client.get("/earnings/suggestions", headers=headers)
    assert suggestions_resp.status_code == 200
    assert len(suggestions_resp.json()["suggestions"]) >= 1

    programs_resp = client.get("/earnings/programs", headers=headers)
    assert programs_resp.status_code == 200
    assert len(programs_resp.json()["programs"]) >= 2

    ad_opt_resp = client.post(
        "/earnings/ad-optimizer",
        headers=headers,
        json={"ga4_sessions": 2500, "pageviews": 4200, "adsense_revenue": 39.5, "adsense_ctr": 0.008},
    )
    assert ad_opt_resp.status_code == 200
    assert "rpm" in ad_opt_resp.json()

    dashboard_resp = client.get("/earnings/dashboard", headers=headers)
    assert dashboard_resp.status_code == 200
    assert "summary" in dashboard_resp.json()
