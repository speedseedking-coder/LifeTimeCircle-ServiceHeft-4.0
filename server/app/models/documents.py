from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field


class DocumentApprovalStatus(str, Enum):
    QUARANTINED = "QUARANTINED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class DocumentScanStatus(str, Enum):
    PENDING = "PENDING"
    CLEAN = "CLEAN"
    INFECTED = "INFECTED"


class DocumentOut(BaseModel):
    id: str = Field(..., min_length=6)
    owner_user_id: str
    filename: str
    content_type: str
    size_bytes: int = Field(..., ge=0)
    approval_status: DocumentApprovalStatus
    scan_status: DocumentScanStatus
    created_at: str  # ISO-8601 (UTC)