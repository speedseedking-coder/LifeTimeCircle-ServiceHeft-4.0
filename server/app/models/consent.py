from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ConsentAcceptance(Base):
    __tablename__ = "consent_acceptances"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # UUID stored as string (SQLite-friendly)
    user_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)

    doc_type: Mapped[str] = mapped_column(String(32), nullable=False)
    doc_version: Mapped[str] = mapped_column(String(32), nullable=False)

    accepted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Contract: source ∈ {ui, api}
    source: Mapped[str] = mapped_column(String(16), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "doc_type", "doc_version", name="uq_consent_user_doc_ver"),
        Index("ix_consent_user_doc_type", "user_id", "doc_type"),
    )