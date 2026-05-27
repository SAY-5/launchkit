from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_tenant
from app.core.db import get_db
from app.core.security import create_access_token, hash_password, verify_password
from app.models import Tenant, User
from app.schemas import SignInRequest, SignUpRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignUpRequest, db: Annotated[Session, Depends(get_db)]) -> TokenResponse:
    existing = db.scalars(select(User).where(User.email == payload.email)).first()
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    tenant = Tenant(name=payload.tenant_name)
    db.add(tenant)
    db.flush()
    user = User(
        tenant_id=tenant.id,
        email=payload.email,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return TokenResponse(access_token=create_access_token(str(user.id), user.tenant_id))


@router.post("/signin", response_model=TokenResponse)
def signin(payload: SignInRequest, db: Annotated[Session, Depends(get_db)]) -> TokenResponse:
    user = db.scalars(select(User).where(User.email == payload.email)).first()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )
    return TokenResponse(access_token=create_access_token(str(user.id), user.tenant_id))


@router.get("/me", response_model=UserResponse)
def me(
    user: Annotated[User, Depends(get_current_user)],
    tenant: Annotated[Tenant, Depends(get_tenant)],
) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        tenant_id=user.tenant_id,
        subscription_status=tenant.subscription_status,
    )
