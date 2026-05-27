"""Contract tests for the Stripe webhook endpoint.

These build a real Stripe signature header so the endpoint's verification path
is exercised, and assert the subscription state implied by each event type.
"""

import hashlib
import hmac
import json
import time

from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.models import Tenant
from tests.conftest import register

WEBHOOK_SECRET = "whsec_test_secret"


def _signed(payload: dict) -> tuple[bytes, str]:
    settings = get_settings()
    settings.stripe_webhook_secret = WEBHOOK_SECRET
    body = json.dumps(payload).encode()
    timestamp = int(time.time())
    signed_payload = f"{timestamp}.".encode() + body
    signature = hmac.new(
        WEBHOOK_SECRET.encode(), signed_payload, hashlib.sha256
    ).hexdigest()
    header = f"t={timestamp},v1={signature}"
    return body, header


def _event(event_id: str, event_type: str, tenant_id: int, status: str | None = None) -> dict:
    obj: dict = {"metadata": {"tenant_id": str(tenant_id)}, "customer": "cus_1"}
    if status is not None:
        obj["status"] = status
    return {"id": event_id, "object": "event", "type": event_type, "data": {"object": obj}}


def test_invalid_signature_is_rejected(client: TestClient) -> None:
    resp = client.post(
        "/billing/webhook",
        content=b"{}",
        headers={"stripe-signature": "t=1,v1=bad"},
    )
    assert resp.status_code == 400


def test_checkout_completed_activates(client: TestClient, db_session) -> None:
    register(client, "a@acme.example", "Acme")
    tenant = db_session.query(Tenant).first()
    body, header = _signed(_event("evt_a", "checkout.session.completed", tenant.id))
    resp = client.post("/billing/webhook", content=body, headers={"stripe-signature": header})
    assert resp.status_code == 200
    assert resp.text == "applied"
    db_session.refresh(tenant)
    assert tenant.subscription_status == "active"


def test_payment_failed_sets_past_due(client: TestClient, db_session) -> None:
    register(client, "a@acme.example", "Acme")
    tenant = db_session.query(Tenant).first()
    body, header = _signed(_event("evt_b", "invoice.payment_failed", tenant.id))
    client.post("/billing/webhook", content=body, headers={"stripe-signature": header})
    db_session.refresh(tenant)
    assert tenant.subscription_status == "past_due"
