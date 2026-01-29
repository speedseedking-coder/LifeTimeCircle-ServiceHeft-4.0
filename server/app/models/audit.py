import json
import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    module_id: Mapped[str] = mapped_column(String(64), index=True)
    event_name: Mapped[str] = mapped_column(String(128), index=True)
    schema_version: Mapped[str] = mapped_column(String(32))

    correlation_id: Mapped[str] = mapped_column(String(64), index=True)
    idempotency_key: Mapped[str] = mapped_column(String(128), index=True)

    actor_role: Mapped[str] = mapped_column(String(32))
    actor_subject_id: Mapped[str] = mapped_column(String(64))
    actor_scope_ref: Mapped[str] = mapped_column(String(64))

    payload_json: Mapped[str] = mapped_column(Text)  # redacted-by-default; KEINE PII
    emitted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        UniqueConstraint("correlation_id", "idempotency_key", "event_name", name="uq_audit_idem"),
    )

    @staticmethod
    def dump_payload(payload: dict) -> str:
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    key: Mapped[str] = mapped_column(String(160), unique=True, index=True)

    status_code: Mapped[int] = mapped_column()
    response_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
