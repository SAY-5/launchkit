"""Stripe billing integration.

Runs in Stripe test mode. The checkout call is only exercised against the real
Stripe API when a secret key is configured; tests stub it. Webhook handling
verifies the signature, deduplicates by event id, and drives the tenant
subscription state from the event type.
"""

from __future__ import annotations

import json

import stripe
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import ProcessedEvent, Tenant

# Maps Stripe event types to the subscription state they imply.
_EVENT_STATUS = {
    "checkout.session.completed": "active",
    "customer.subscription.updated": None,  # status read from payload
    "invoice.payment_failed": "past_due",
    "customer.subscription.deleted": "canceled",
}


def create_checkout_session(tenant: Tenant, success_url: str, cancel_url: str) -> str:
    settings = get_settings()
    stripe.api_key = settings.stripe_secret_key
    session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": settings.stripe_price_id, "quantity": 1}],
        success_url=success_url,
        cancel_url=cancel_url,
        client_reference_id=str(tenant.id),
        metadata={"tenant_id": str(tenant.id)},
    )
    return str(session["url"])


def verify_signature(payload: bytes, sig_header: str) -> dict:
    settings = get_settings()
    event = stripe.Webhook.construct_event(payload, sig_header, settings.stripe_webhook_secret)
    # Convert the Stripe object to a plain nested dict for downstream handling.
    return json.loads(str(event))


def _tenant_for_event(db: Session, event: dict) -> Tenant | None:
    obj = event.get("data", {}).get("object", {})
    tenant_id = obj.get("metadata", {}).get("tenant_id") or obj.get("client_reference_id")
    if tenant_id is None:
        customer = obj.get("customer")
        if customer is None:
            return None
        return db.scalars(
            select(Tenant).where(Tenant.stripe_customer_id == customer)
        ).first()
    return db.get(Tenant, int(tenant_id))


def _resolve_status(event: dict) -> str | None:
    event_type = event.get("type", "")
    if event_type not in _EVENT_STATUS:
        return None
    explicit = _EVENT_STATUS[event_type]
    if explicit is not None:
        return explicit
    # customer.subscription.updated carries the status on the object.
    return event.get("data", {}).get("object", {}).get("status")


def process_event(db: Session, event: dict) -> bool:
    """Apply a webhook event. Returns True if newly applied, False if duplicate.

    Idempotency has two layers. The event id is checked against
    ``processed_events`` up front, and the column carries a unique constraint so
    that a concurrent duplicate that slips past the check fails on insert; that
    ``IntegrityError`` is caught and reported as a duplicate. Either way the
    subscription state is mutated at most once per distinct event id, so a
    replayed delivery never double-applies a transition.
    """

    event_id = event.get("id")
    if event_id is None:
        return False

    already = db.scalars(
        select(ProcessedEvent).where(ProcessedEvent.event_id == event_id)
    ).first()
    if already is not None:
        return False

    db.add(ProcessedEvent(event_id=event_id))

    status = _resolve_status(event)
    if status is not None:
        tenant = _tenant_for_event(db, event)
        if tenant is not None:
            tenant.subscription_status = status
            obj = event.get("data", {}).get("object", {})
            customer = obj.get("customer")
            if customer is not None and tenant.stripe_customer_id is None:
                tenant.stripe_customer_id = customer

    try:
        db.commit()
    except IntegrityError:
        # A concurrent delivery recorded this event id first; treat as duplicate.
        db.rollback()
        return False
    return True
