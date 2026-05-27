"""Request dependencies for authentication and tenant scoping.

``get_current_user`` decodes the bearer token. ``TenantScope`` is the data
access guard: it wraps a session bound to the caller's tenant id and is the
only sanctioned way for routes to read or write tenant-scoped rows. Every query
goes through ``query`` / ``get_owned``, which inject the tenant filter and
enforce row ownership, so isolation does not rely on each route remembering to
add a ``WHERE tenant_id`` clause.
"""

from __future__ import annotations

from typing import Annotated, TypeVar

import jwt
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import inspect as sa_inspect
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import Base, get_db
from app.core.security import decode_access_token
from app.models import Tenant, User

# Bound to Base; only tenant-scoped models (those carrying a tenant_id column,
# see app.models.TenantScoped) are passed in by routes.
T = TypeVar("T", bound=Base)

_CREDENTIALS_ERROR = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    db: Annotated[Session, Depends(get_db)],
    authorization: Annotated[str | None, Header()] = None,
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise _CREDENTIALS_ERROR
    token = authorization.split(" ", 1)[1]
    try:
        payload = decode_access_token(token)
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired"
        ) from exc
    except jwt.PyJWTError as exc:
        raise _CREDENTIALS_ERROR from exc

    user_id = payload.get("sub")
    if user_id is None:
        raise _CREDENTIALS_ERROR
    user = db.get(User, int(user_id))
    if user is None or user.tenant_id != payload.get("tenant_id"):
        raise _CREDENTIALS_ERROR
    return user


class TenantScope:
    """A tenant-bound view over the database session.

    Routes receive a ``TenantScope`` instead of a raw session. All reads and
    writes pass through here, which guarantees the tenant filter is applied and
    that a row fetched by id belongs to the caller's tenant.
    """

    def __init__(self, db: Session, tenant_id: int) -> None:
        self._db = db
        self.tenant_id = tenant_id

    @property
    def session(self) -> Session:
        return self._db

    def query(self, model: type[T]) -> list[T]:
        column = sa_inspect(model).columns["tenant_id"]
        return list(self._db.scalars(select(model).where(column == self.tenant_id)))

    def get_owned(self, model: type[T], obj_id: int) -> T | None:
        obj = self._db.get(model, obj_id)
        if obj is None or getattr(obj, "tenant_id", None) != self.tenant_id:
            return None
        return obj

    def add(self, obj: T) -> T:
        if getattr(obj, "tenant_id", None) not in (None, self.tenant_id):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tenant mismatch")
        obj.tenant_id = self.tenant_id  # type: ignore[attr-defined]
        self._db.add(obj)
        self._db.commit()
        self._db.refresh(obj)
        return obj


def get_scope(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> TenantScope:
    return TenantScope(db, user.tenant_id)


def get_tenant(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> Tenant:
    tenant = db.get(Tenant, user.tenant_id)
    if tenant is None:
        raise _CREDENTIALS_ERROR
    return tenant
