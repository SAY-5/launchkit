from fastapi.testclient import TestClient

from tests.conftest import auth_header, register


def test_create_and_list_note(client: TestClient) -> None:
    token = register(client, "a@acme.example", "Acme")
    created = client.post(
        "/notes", json={"title": "First", "body": "Hello world."}, headers=auth_header(token)
    )
    assert created.status_code == 201
    listing = client.get("/notes", headers=auth_header(token))
    assert listing.status_code == 200
    assert [n["title"] for n in listing.json()] == ["First"]


def test_summarize_uses_fake_provider(client: TestClient) -> None:
    token = register(client, "a@acme.example", "Acme")
    note = client.post(
        "/notes",
        json={"title": "Note", "body": "Ship the starter. Then write docs."},
        headers=auth_header(token),
    ).json()
    resp = client.post(f"/notes/{note['id']}/summarize", headers=auth_header(token))
    assert resp.status_code == 200
    assert resp.json()["summary"] == "Ship the starter. (6 words)"
