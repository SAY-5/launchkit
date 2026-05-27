"""Webhook idempotency and subscription lifecycle.

A replayed event must not apply its transition twice, and the subscription
state must follow the lifecycle implied by the event types.
"""

from app.models import ProcessedEvent, Tenant
from app.services import billing
from tests.conftest import register


def _event(event_id: str, event_type: str, tenant_id: int, status: str | None = None) -> dict:
    obj: dict = {"metadata": {"tenant_id": str(tenant_id)}, "customer": "cus_1"}
    if status is not None:
        obj["status"] = status
    return {"id": event_id, "type": event_type, "data": {"object": obj}}


def test_replayed_event_applies_once(client, db_session) -> None:
    register(client, "a@acme.example", "Acme")
    tenant = db_session.query(Tenant).first()
    event = _event("evt_dup", "checkout.session.completed", tenant.id)

    first = billing.process_event(db_session, event)
    second = billing.process_event(db_session, event)

    assert first is True
    assert second is False
    db_session.refresh(tenant)
    assert tenant.subscription_status == "active"
    # Exactly one record of the event id exists.
    assert db_session.query(ProcessedEvent).filter_by(event_id="evt_dup").count() == 1


def test_replay_does_not_overwrite_a_later_transition(client, db_session) -> None:
    register(client, "a@acme.example", "Acme")
    tenant = db_session.query(Tenant).first()

    billing.process_event(db_session, _event("evt_1", "checkout.session.completed", tenant.id))
    billing.process_event(db_session, _event("evt_2", "customer.subscription.deleted", tenant.id))
    db_session.refresh(tenant)
    assert tenant.subscription_status == "canceled"

    # Replaying the original activation event must not revive the subscription.
    replayed = billing.process_event(
        db_session, _event("evt_1", "checkout.session.completed", tenant.id)
    )
    assert replayed is False
    db_session.refresh(tenant)
    assert tenant.subscription_status == "canceled"


def test_lifecycle_transitions(client, db_session) -> None:
    register(client, "a@acme.example", "Acme")
    tenant = db_session.query(Tenant).first()

    billing.process_event(db_session, _event("e1", "checkout.session.completed", tenant.id))
    db_session.refresh(tenant)
    assert tenant.subscription_status == "active"

    billing.process_event(db_session, _event("e2", "invoice.payment_failed", tenant.id))
    db_session.refresh(tenant)
    assert tenant.subscription_status == "past_due"

    billing.process_event(
        db_session, _event("e3", "customer.subscription.updated", tenant.id, status="active")
    )
    db_session.refresh(tenant)
    assert tenant.subscription_status == "active"

    billing.process_event(db_session, _event("e4", "customer.subscription.deleted", tenant.id))
    db_session.refresh(tenant)
    assert tenant.subscription_status == "canceled"
