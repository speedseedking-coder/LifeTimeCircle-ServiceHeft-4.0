# server/app/models/documents.py
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from sqlalchemy import Index, String
from sqlmodel import Field, SQLModel


def _utcnow_naive() -> datetime:
    # naive UTC (SQLite-friendly): aware -> strip tzinfo
    return datetime.now(timezone.utc).replace(tzinfo=None)


class DocumentApprovalStatus(str, Enum):
    QUARANTINED = "QUARANTINED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class DocumentScanStatus(str, Enum):
    PENDING = "PENDING"
    CLEAN = "CLEAN"
    INFECTED = "INFECTED"
    ERROR = "ERROR"


class DocumentPiiStatus(str, Enum):
    OK = "OK"
    SUSPECTED = "SUSPECTED"
    CONFIRMED = "CONFIRMED"


class Document(SQLModel, table=True):
    """
    Trust-relevantes Dokument (Evidence-Quelle).
    Harte Regeln:
    - Upload: QUARANTINED + PENDING
    - Approve: nur wenn CLEAN + PII_OK
    - INFECTED => REJECTED (serverseitig erzwingen)
    - PII != OK => Sichtbarkeit nur Owner/Admin; Trust darf daraus kein T3 machen
    """

    __tablename__ = "documents"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Scope / Ownership (object-level)
    vehicle_id: int = Field(index=True)
    created_by_user_id: int = Field(index=True)

    # Original filename / metadata (datenarm)
    filename: str = Field(sa_type=String(255))
    content_type: str = Field(sa_type=String(120))
    size_bytes: int = Field(default=0)

    # Storage (Pfad/Key – nie öffentlich als "full path" ausgeben)
    storage_key: str = Field(sa_type=String(500), index=True)

    # Integrity (Trusted Upload)
    checksum_sha256: str = Field(sa_type=String(64), index=True)

    approval_status: DocumentApprovalStatus = Field(
        default=DocumentApprovalStatus.QUARANTINED, index=True
    )
    scan_status: DocumentScanStatus = Field(default=DocumentScanStatus.PENDING, index=True)
    pii_status: DocumentPiiStatus = Field(default=DocumentPiiStatus.OK, index=True)

    # Audit fields
    created_at: datetime = Field(default_factory=_utcnow_naive, index=True)

    approved_by_user_id: Optional[int] = Field(default=None, index=True)
    approved_at: Optional[datetime] = Field(default=None, index=True)

    rejected_by_user_id: Optional[int] = Field(default=None, index=True)
    rejected_at: Optional[datetime] = Field(default=None, index=True)
    reject_reason: Optional[str] = Field(default=None, sa_type=String(500))

    pii_marked_by_user_id: Optional[int] = Field(default=None, index=True)
    pii_marked_at: Optional[datetime] = Field(default=None, index=True)
    pii_note: Optional[str] = Field(default=None, sa_type=String(500))

    # Soft delete (optional, falls euer Projekt das nutzt)
    deleted_at: Optional[datetime] = Field(default=None, index=True)


# Helpful indices
Index(
    "ix_documents_vehicle_status",
    Document.vehicle_id,
    Document.approval_status,
    Document.scan_status,
    Document.pii_status,
)

# --- Backwards-compatible export for existing routers ---
DocumentOut = Document