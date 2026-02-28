from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def _uuid4_str() -> str:
    return str(uuid.uuid4())


class VehicleEntry(Base):
    __tablename__ = "vehicle_entries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid4_str)
    vehicle_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("vehicles.public_id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    owner_user_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    entry_group_id: Mapped[str] = mapped_column(String(36), index=True, nullable=False)
    supersedes_entry_id: Mapped[Optional[str]] = mapped_column(String(36), index=True, nullable=True)

    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_latest: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)

    entry_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    entry_type: Mapped[str] = mapped_column(String(64), nullable=False)
    performed_by: Mapped[str] = mapped_column(String(64), nullable=False)
    km: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cost_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    trust_level: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
