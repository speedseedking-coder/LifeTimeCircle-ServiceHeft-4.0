# server/app/services/documents_service.py
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import BinaryIO, Optional

from fastapi import HTTPException

from app.models.documents import (
    Document,
    DocumentApprovalStatus,
    DocumentPiiStatus,
    DocumentScanStatus,
)


def _utcnow() -> datetime:
    # timezone-aware UTC timestamp (Python 3.12+ friendly)
    return datetime.now(timezone.utc)


def sha256_stream(fp: BinaryIO) -> str:
    h = hashlib.sha256()
    while True:
        chunk = fp.read(1024 * 1024)
        if not chunk:
            break
        h.update(chunk)
    return h.hexdigest()


def is_valid_trust_evidence(doc: Document) -> bool:
    return (
        doc.approval_status == DocumentApprovalStatus.APPROVED
        and doc.scan_status == DocumentScanStatus.CLEAN
        and doc.pii_status == DocumentPiiStatus.OK
        and doc.deleted_at is None
    )


def ensure_can_approve(doc: Document) -> None:
    if doc.deleted_at is not None:
        raise HTTPException(status_code=409, detail="document_deleted")

    if doc.approval_status == DocumentApprovalStatus.APPROVED:
        return

    if doc.approval_status == DocumentApprovalStatus.REJECTED:
        raise HTTPException(status_code=409, detail="document_rejected")

    if doc.scan_status != DocumentScanStatus.CLEAN:
        raise HTTPException(status_code=409, detail="scan_not_clean")

    if doc.pii_status != DocumentPiiStatus.OK:
        raise HTTPException(status_code=409, detail="pii_not_cleared")


def approve_document(doc: Document, admin_user_id: int) -> Document:
    ensure_can_approve(doc)
    doc.approval_status = DocumentApprovalStatus.APPROVED
    doc.approved_by_user_id = admin_user_id
    doc.approved_at = _utcnow()
    # clear reject fields
    doc.rejected_by_user_id = None
    doc.rejected_at = None
    doc.reject_reason = None
    return doc


def reject_document(doc: Document, admin_user_id: int, reason: str) -> Document:
    if doc.deleted_at is not None:
        raise HTTPException(status_code=409, detail="document_deleted")

    doc.approval_status = DocumentApprovalStatus.REJECTED
    doc.rejected_by_user_id = admin_user_id
    doc.rejected_at = _utcnow()
    doc.reject_reason = reason[:500]

    # Once rejected, it should not be approvable anymore (hard)
    doc.approved_by_user_id = None
    doc.approved_at = None
    return doc


def set_scan_status(doc: Document, scan_status: DocumentScanStatus, admin_user_id: int) -> Document:
    if doc.deleted_at is not None:
        raise HTTPException(status_code=409, detail="document_deleted")

    doc.scan_status = scan_status

    # Hard rule: INFECTED => auto reject
    if scan_status == DocumentScanStatus.INFECTED:
        reject_document(doc, admin_user_id=admin_user_id, reason="infected_auto_reject")

    return doc


def mark_pii_status(
    doc: Document,
    new_status: DocumentPiiStatus,
    marker_user_id: int,
    note: Optional[str],
) -> Document:
    if doc.deleted_at is not None:
        raise HTTPException(status_code=409, detail="document_deleted")

    doc.pii_status = new_status
    doc.pii_marked_by_user_id = marker_user_id
    doc.pii_marked_at = _utcnow()
    doc.pii_note = (note or "")[:500] or None

    # PII confirmed: Trust must not reach T3; deletion policy handled elsewhere (cron/config)
    return doc