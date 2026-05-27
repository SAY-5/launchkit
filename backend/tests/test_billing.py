from fastapi.testclient import TestClient

from app.models import Tenant
from app.services import billing
from tests.conftest import auth_header, register


def test_webhook_marks_tenant_active(client: TestClient, db_session) -> None:
    register(client, "a@acme.example", "Acme")
    tenant = db_session.query(Tenant).first()
    event = {
        "id": "evt_1",
        "type": "checkout.session.completed",
        "data": {"object": {"metadata": {"tenant_id": str(tenant.id)}, "customer": "cus_1"}},
    }
    applied = billing.process_event(db_session, event)
    assert applied is True
    db_session.refresh(tenant)
    assert tenant.subscription_status == "active"


def test_checkout_requires_stripe_config(client: TestClient) -> None:
    token = register(client, "a@acme.example", "Acme")
    resp = client.post("/billing/checkout", headers=auth_header(token))
    assert resp.status_code == 503
