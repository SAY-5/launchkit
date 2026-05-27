from fastapi.testclient import TestClient

from tests.conftest import auth_header, register


def test_signup_then_me_returns_tenant(client: TestClient) -> None:
    token = register(client, "owner@acme.example", "Acme")
    resp = client.get("/auth/me", headers=auth_header(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["email"] == "owner@acme.example"
    assert body["subscription_status"] == "inactive"


def test_duplicate_email_rejected(client: TestClient) -> None:
    register(client, "dup@acme.example", "Acme")
    resp = client.post(
        "/auth/signup",
        json={"email": "dup@acme.example", "password": "password123", "tenant_name": "Other"},
    )
    assert resp.status_code == 409


def test_signin_wrong_password(client: TestClient) -> None:
    register(client, "user@acme.example", "Acme")
    resp = client.post(
        "/auth/signin", json={"email": "user@acme.example", "password": "wrongpass1"}
    )
    assert resp.status_code == 401


def test_me_requires_token(client: TestClient) -> None:
    assert client.get("/auth/me").status_code == 401
