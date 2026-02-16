from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.documents import (
    DocumentApprovalStatus,
    DocumentPiiStatus,
    DocumentScanStatus,
)


class DocumentOut(BaseModel):
    """
    API-Response Schema für Dokumente.

    Erwartung / Mapping:
    - store liefert typischerweise Attribute wie:
      - id: str (uuid-like)
      - approval_status: Enum
      - scan_status: Enum
      - pii_status: Enum
      - created_at: datetime (naive oder aware)
      - checksum_sha256: optional (kann None sein)
      - owner_user_id: str (wird als created_by_user_id exposed)

    - API/Tests verwenden häufig "status" -> das mappen wir auf approval_status.
    """

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: str

    filename: str
    content_type: str
    size_bytes: int

    # Extern: "status" ; Intern (store): "approval_status"
    status: DocumentApprovalStatus = Field(alias="approval_status")

    scan_status: DocumentScanStatus
    pii_status: DocumentPiiStatus

    created_at: datetime

    checksum_sha256: Optional[str] = None

    # In einigen Records (noch) nicht gesetzt -> optional
    vehicle_id: Optional[str] = None

    # Extern: created_by_user_id ; Intern (store): owner_user_id
    created_by_user_id: Optional[str] = Field(default=None, alias="owner_user_id")

    approved_by_user_id: Optional[str] = None
    approved_at: Optional[datetime] = None

    rejected_by_user_id: Optional[str] = None
    rejected_at: Optional[datetime] = None
    reject_reason: Optional[str] = None

    pii_marked_by_user_id: Optional[str] = None
    pii_marked_at: Optional[datetime] = None
    pii_note: Optional[str] = None

    deleted_at: Optional[datetime] = None