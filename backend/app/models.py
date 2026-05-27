from datetime import UTC, datetime
from typing import Protocol

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


def _now() -> datetime:
    return datetime.now(UTC)


class TenantScoped(Protocol):
    """Structural type for rows that carry a tenant id.

    The data-access guard is generic over this protocol so that any
    tenant-scoped model is automatically subject to the tenant filter.
    """

    id: int
    tenant_id: int


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    stripe_customer_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    subscription_status: Mapped[str] = mapped_column(String(32), default="inactive")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    users: Mapped[list["User"]] = relationship(back_populates="tenant")
    notes: Mapped[list["Note"]] = relationship(back_populates="tenant")


class User(Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("email", name="uq_users_email"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    email: Mapped[str] = mapped_column(String(255))
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    tenant: Mapped[Tenant] = relationship(back_populates="users")


class Note(Base):
    """A tenant-scoped resource used by the dashboard and the feature endpoint."""

    __tablename__ = "notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    tenant_id: Mapped[int] = mapped_column(ForeignKey("tenants.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(String(4000), default="")
    summary: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    tenant: Mapped[Tenant] = relationship(back_populates="notes")


class ProcessedEvent(Base):
    """Records Stripe webhook event ids to make delivery idempotent."""

    __tablename__ = "processed_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
