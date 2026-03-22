import uuid

from fastapi.testclient import TestClient


def test_register_login_and_access_protected_routes(client: TestClient) -> None:
    email = f"user-{uuid.uuid4().hex[:8]}@example.com"
    password = "strong-pass-123"

    register_response = client.post(
        "/users/register",
        json={"email": email, "full_name": "Test User", "password": password},
    )
    assert register_response.status_code == 201

    token_response = client.post("/users/token", json={"email": email, "password": password})
    assert token_response.status_code == 200
    token = token_response.json()["access_token"]

    headers = {"Authorization": f"Bearer {token}"}

    me_response = client.get("/users/me", headers=headers)
    assert me_response.status_code == 200
    assert me_response.json()["email"] == email

    content_response = client.post(
        "/content/",
        headers=headers,
        json={"title": "Hello", "slug": f"hello-{uuid.uuid4().hex[:8]}", "body": "World"},
    )
    assert content_response.status_code == 201


def test_protected_endpoint_requires_token(client: TestClient) -> None:
    response = client.get("/users/")
    assert response.status_code == 401
