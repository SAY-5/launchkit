from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_tenant
from app.core.config import get_settings
from app.core.db import get_db
from app.models import Tenant
from app.schemas import CheckoutResponse
from app.services import billing

router = APIRouter(prefix="/billing", tags=["billing"])


@router.post("/checkout", response_model=CheckoutResponse)
def checkout(tenant: Annotated[Tenant, Depends(get_tenant)]) -> CheckoutResponse:
    settings = get_settings()
    if not settings.stripe_secret_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Billing not configured"
        )
    url = billing.create_checkout_session(
        tenant,
        success_url="http://localhost:3000/dashboard?upgraded=1",
        cancel_url="http://localhost:3000/billing",
    )
    return CheckoutResponse(checkout_url=url)


@router.post("/webhook")
async def webhook(request: Request, db: Annotated[Session, Depends(get_db)]) -> Response:
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    try:
        event = billing.verify_signature(payload, sig)
    except Exception as exc:  # stripe raises SignatureVerificationError / ValueError
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid signature"
        ) from exc
    applied = billing.process_event(db, event)
    return Response(
        status_code=status.HTTP_200_OK,
        content="applied" if applied else "duplicate",
        media_type="text/plain",
    )
