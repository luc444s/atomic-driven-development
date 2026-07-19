from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from apps.api.app.core.database import Base


def new_uuid() -> str:
    return str(uuid4())


def utc_now() -> datetime:
    return datetime.now(UTC)


class LogisticsSessionWaybillVersion(Base):
    __tablename__ = "lg_session_waybill_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_uuid)
    tenant_id: Mapped[str] = mapped_column(ForeignKey("tenants.id"), nullable=False, index=True)
    session_id: Mapped[str] = mapped_column(
        ForeignKey("lg_vehicle_sessions.id"), nullable=False, index=True
    )
    previous_version_id: Mapped[str | None] = mapped_column(
        ForeignKey("lg_session_waybill_versions.id"), nullable=True, index=True
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ACTIVE", index=True)
    regulatory_context: Mapped[str] = mapped_column(
        String(40), nullable=False, default="ES_HACIENDA", index=True
    )
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    generated_by: Mapped[str | None] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    operational_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    snapshot_schema_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    movement_ids_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    snapshot_json: Mapped[str] = mapped_column(Text, nullable=False)
    change_event: Mapped[str] = mapped_column(String(40), nullable=False)
    change_reason: Mapped[str] = mapped_column(Text, nullable=False)
    idempotency_key: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )
