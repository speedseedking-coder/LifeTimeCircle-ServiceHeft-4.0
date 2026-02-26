from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TrustFolder(Base):
    __tablename__ = "trust_folders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vehicle_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    owner_user_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    addon_key: Mapped[str] = mapped_column(String(64), nullable=False, index=True, default="restauration")
    title: Mapped[str] = mapped_column(String(255), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (UniqueConstraint("vehicle_id", "owner_user_id", "title", name="uq_trust_folder_title_per_owner"),)