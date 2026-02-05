# FILE: server/app/models/documents.py
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class DocumentApprovalStatus(str, Enum):
    QUARANTINED = "QUARANTINED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class DocumentScanStatus(str, Enum):
    PENDING = "PENDING"
    CLEAN = "CLEAN"
    INFECTED = "INFECTED"


class DocumentOut(BaseModel):
    id: str
    filename: str
    content_type: str
    size_bytes: int
    created_at: datetime
    owner_user_id: Optional[str] = None
    approval_status: DocumentApprovalStatus
    scan_status: DocumentScanStatus