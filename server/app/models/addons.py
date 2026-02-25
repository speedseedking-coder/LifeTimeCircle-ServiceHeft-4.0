from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AddonConfig(Base):
    __tablename__ = "addon_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    addon_key: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)

    # Admin switches (deny-by-default)
    allow_new: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    requires_payment: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    admin_only: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class AccountAddonEntitlement(Base):
    __tablename__ = "account_addon_entitlements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    addon_key: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (UniqueConstraint("user_id", "addon_key", name="uq_account_addon_entitlement"),)


class VehicleAddonState(Base):
    __tablename__ = "vehicle_addon_states"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # Vehicle.public_id is a UUID-ish string in this repo
    vehicle_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    addon_key: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # Grandfathering: once set => re-enable always allowed
    addon_first_enabled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (UniqueConstraint("vehicle_id", "addon_key", name="uq_vehicle_addon_state"),)
