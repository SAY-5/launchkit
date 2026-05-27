"""Tenant scoping contract: a user from one tenant can never reach another's rows."""

from fastapi.testclient import TestClient

from tests.conftest import auth_header, register


def test_list_only_returns_own_tenant_notes(client: TestClient) -> None:
    token_a = register(client, "a@acme.example", "Acme")
    token_b = register(client, "b@globex.example", "Globex")

    client.post("/notes", json={"title": "A note", "body": ""}, headers=auth_header(token_a))
    client.post("/notes", json={"title": "B note", "body": ""}, headers=auth_header(token_b))

    list_a = client.get("/notes", headers=auth_header(token_a)).json()
    list_b = client.get("/notes", headers=auth_header(token_b)).json()

    assert [n["title"] for n in list_a] == ["A note"]
    assert [n["title"] for n in list_b] == ["B note"]


def test_cannot_read_other_tenant_note_by_id(client: TestClient) -> None:
    token_a = register(client, "a@acme.example", "Acme")
    token_b = register(client, "b@globex.example", "Globex")

    note_b = client.post(
        "/notes", json={"title": "secret", "body": "x"}, headers=auth_header(token_b)
    ).json()

    # Tenant A asks for tenant B's note id and is told it does not exist.
    resp = client.get(f"/notes/{note_b['id']}", headers=auth_header(token_a))
    assert resp.status_code == 404


def test_cannot_summarize_other_tenant_note(client: TestClient) -> None:
    token_a = register(client, "a@acme.example", "Acme")
    token_b = register(client, "b@globex.example", "Globex")

    note_b = client.post(
        "/notes", json={"title": "secret", "body": "x"}, headers=auth_header(token_b)
    ).json()

    resp = client.post(f"/notes/{note_b['id']}/summarize", headers=auth_header(token_a))
    assert resp.status_code == 404
