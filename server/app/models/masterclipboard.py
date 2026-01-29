import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class MasterClipboardSession(Base):
    __tablename__ = "mc_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_id: Mapped[str] = mapped_column(String(64), index=True)
    vehicle_public_id: Mapped[str] = mapped_column(String(64), index=True)

    is_closed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    speech_chunks = relationship("MasterClipboardSpeechChunk", back_populates="session", cascade="all,delete-orphan")
    triage_items = relationship("MasterClipboardTriageItem", back_populates="session", cascade="all,delete-orphan")
    board_snapshots = relationship("MasterClipboardBoardSnapshot", back_populates="session", cascade="all,delete-orphan")


class MasterClipboardSpeechChunk(Base):
    __tablename__ = "mc_speech_chunks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("mc_sessions.id"), index=True)
    source: Mapped[str] = mapped_column(String(16))
    content_redacted: Mapped[str] = mapped_column(Text)  # redacted input

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    session = relationship("MasterClipboardSession", back_populates="speech_chunks")


class MasterClipboardTriageItem(Base):
    __tablename__ = "mc_triage_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("mc_sessions.id"), index=True)

    kind: Mapped[str] = mapped_column(String(16))
    title: Mapped[str] = mapped_column(String(160))
    details_redacted: Mapped[str | None] = mapped_column(Text, nullable=True)

    severity: Mapped[str] = mapped_column(String(16))
    status: Mapped[str] = mapped_column(String(16))

    evidence_refs_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list[str]

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    session = relationship("MasterClipboardSession", back_populates="triage_items")


class MasterClipboardBoardSnapshot(Base):
    __tablename__ = "mc_board_snapshots"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[str] = mapped_column(String(36), ForeignKey("mc_sessions.id"), index=True)

    ordered_item_ids_json: Mapped[str] = mapped_column(Text)  # JSON list[str]
    notes_redacted: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    session = relationship("MasterClipboardSession", back_populates="board_snapshots")
