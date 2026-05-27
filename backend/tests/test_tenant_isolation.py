"""Tenant scoping contract.

A user from one tenant must never read or mutate another tenant's rows. These
tests drive every note operation across a tenant boundary and assert the API
rejects the cross-tenant attempt, so isolation is proven at the API rather than
assumed by convention.
"""

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.api.deps import TenantScope
from app.models import Note
from tests.conftest import auth_header, register


def _make_two_tenants(client: TestClient) -> tuple[str, str, int]:
    token_a = register(client, "a@acme.example", "Acme")
    token_b = register(client, "b@globex.example", "Globex")
    note_b = client.post(
        "/notes", json={"title": "secret", "body": "owned by B"}, headers=auth_header(token_b)
    ).json()
    return token_a, token_b, note_b["id"]


def test_list_only_returns_own_tenant_notes(client: TestClient) -> None:
    token_a, token_b, _ = _make_two_tenants(client)
    client.post("/notes", json={"title": "A note", "body": ""}, headers=auth_header(token_a))

    list_a = client.get("/notes", headers=auth_header(token_a)).json()
    list_b = client.get("/notes", headers=auth_header(token_b)).json()

    assert [n["title"] for n in list_a] == ["A note"]
    assert [n["title"] for n in list_b] == ["secret"]


@pytest.mark.parametrize(
    ("method", "suffix", "body"),
    [
        ("get", "", None),
        ("patch", "", {"title": "hijacked"}),
        ("delete", "", None),
        ("post", "/summarize", None),
    ],
)
def test_cross_tenant_access_is_rejected(
    client: TestClient, method: str, suffix: str, body: dict | None
) -> None:
    token_a, _, note_b_id = _make_two_tenants(client)
    call = getattr(client, method)
    kwargs = {"headers": auth_header(token_a)}
    if body is not None:
        kwargs["json"] = body
    resp = call(f"/notes/{note_b_id}{suffix}", **kwargs)
    assert resp.status_code == 404


def test_cross_tenant_patch_does_not_mutate(client: TestClient) -> None:
    token_a, token_b, note_b_id = _make_two_tenants(client)
    client.patch(
        f"/notes/{note_b_id}", json={"title": "hijacked"}, headers=auth_header(token_a)
    )
    # Tenant B still sees the original title.
    note = client.get(f"/notes/{note_b_id}", headers=auth_header(token_b)).json()
    assert note["title"] == "secret"


def test_scope_rejects_non_tenant_scoped_model(client: TestClient, db_session) -> None:
    from app.models import ProcessedEvent

    scope = TenantScope(db_session, tenant_id=1)
    with pytest.raises(ValueError):
        scope.query(ProcessedEvent)


def test_save_rejects_foreign_object(client: TestClient, db_session) -> None:
    token_a, token_b, note_b_id = _make_two_tenants(client)
    foreign = db_session.get(Note, note_b_id)
    scope = TenantScope(db_session, tenant_id=foreign.tenant_id + 100)
    with pytest.raises(HTTPException) as exc:
        scope.save(foreign)
    assert exc.value.status_code == 404
