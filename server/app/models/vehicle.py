from __future__ import annotations

import hashlib
import hmac
import os
import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import DateTime, Integer, String, JSON, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def _uuid4_str() -> str:
    return str(uuid.uuid4())


def normalize_vin(vin: str) -> str:
    return (vin or "").strip().upper().replace(" ", "")


def mask_vin(vin: Optional[str]) -> Optional[str]:
    if not vin:
        return None
    v = normalize_vin(vin)
    if len(v) <= 7:
        return "***"
    return f"{v[:3]}***{v[-4:]}"


def _vin_hmac(secret: str, vin: str) -> str:
    return hmac.new(secret.encode("utf-8"), vin.encode("utf-8"), hashlib.sha256).hexdigest()


class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    public_id: Mapped[str] = mapped_column(String(36), unique=True, index=True, nullable=False, default=_uuid4_str)

    owner_user_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)

    # Nie Roh-VIN speichern
    vin_prefix3: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)
    vin_last4: Mapped[Optional[str]] = mapped_column(String(4), nullable=True)
    vin_hmac: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)

    meta: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    @property
    def vin_masked(self) -> Optional[str]:
        if self.vin_prefix3 and self.vin_last4:
            return f"{self.vin_prefix3}***{self.vin_last4}"
        return None

    def set_vin_from_raw(self, vin_raw: Optional[str]) -> None:
        v = normalize_vin(vin_raw or "")
        if not v:
            self.vin_prefix3 = None
            self.vin_last4 = None
            self.vin_hmac = None
            return

        self.vin_prefix3 = v[:3]
        self.vin_last4 = v[-4:]

        secret = os.environ.get("LTC_SECRET_KEY", "")
        self.vin_hmac = _vin_hmac(secret, v) if len(secret) >= 16 else None
