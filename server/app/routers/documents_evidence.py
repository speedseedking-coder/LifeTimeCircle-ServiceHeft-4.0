# server/app/routers/documents_evidence.py
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlmodel import Session, select

from app.models.documents import (
    Document,
    DocumentApprovalStatus,
    DocumentPiiStatus,
    DocumentScanStatus,
)
from app.schemas.documents import (
    AdminRejectIn,
    AdminSetScanStatusIn,
    DocumentOut,
    PiiMarkIn,
)
from app.services.documents_service import (
    approve_document,
    is_valid_trust_evidence,
    mark_pii_status,
    reject_document,
    set_scan_status,
    sha256_stream,
)

# --- Integration placeholders: replace with your real deps ---
def get_db() -> Session:  # pragma: no cover
    raise RuntimeError("wire get_db to your project")

class Actor:  # pragma: no cover
    def __init__(self, user_id: int, role: str, is_admin: bool = False):
        self.user_id = user_id
        self.role = role
        self.is_admin = is_admin

def require_actor() -> Actor:  # pragma: no cover
    raise RuntimeError("wire require_actor to your project")

def require_admin(actor: Actor = Depends(require_actor)) -> Actor:  # pragma: no cover
    if actor.role not in ("admin", "superadmin"):
        raise HTTPException(status_code=403, detail="forbidden")
    actor.is_admin = True
    return actor

def require_vehicle_access(vehicle_id: int, actor: Actor):  # pragma: no cover
    # object-level check must be enforced in your project
    return
# --- end integration placeholders ---

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/upload", response_model=DocumentOut)
def upload_document(
    vehicle_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_actor),
):
    require_vehicle_access(vehicle_id, actor)

    # Read file stream for checksum; we also need size.
    # (We do not store raw bytes here; storage handled by your infra.)
    # We'll read fully once; for large files you may stream to storage and hash during upload.
    data = file.file.read()
    size = len(data)

    checksum = __import__("hashlib").sha256(data).hexdigest()

    doc = Document(
        vehicle_id=vehicle_id,
        created_by_user_id=actor.user_id,
        filename=file.filename or "upload",
        content_type=file.content_type or "application/octet-stream",
        size_bytes=size,
        storage_key=f"vehicle/{vehicle_id}/{checksum}",  # replace with your storage key strategy
        checksum_sha256=checksum,
        approval_status=DocumentApprovalStatus.QUARANTINED,
        scan_status=DocumentScanStatus.PENDING,
        pii_status=DocumentPiiStatus.OK,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


@router.get("/admin/quarantine", response_model=List[DocumentOut])
def admin_list_quarantine(
    db: Session = Depends(get_db),
    admin: Actor = Depends(require_admin),
):
    q = (
        select(Document)
        .where(Document.approval_status == DocumentApprovalStatus.QUARANTINED)
        .where(Document.deleted_at.is_(None))
        .order_by(Document.created_at.desc())
    )
    return list(db.exec(q))


@router.post("/{doc_id}/admin/scan", response_model=DocumentOut)
def admin_set_scan(
    doc_id: int,
    body: AdminSetScanStatusIn,
    db: Session = Depends(get_db),
    admin: Actor = Depends(require_admin),
):
    doc = db.get(Document, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="not_found")

    set_scan_status(doc, body.scan_status, admin_user_id=admin.user_id)
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


@router.post("/{doc_id}/admin/approve", response_model=DocumentOut)
def admin_approve(
    doc_id: int,
    db: Session = Depends(get_db),
    admin: Actor = Depends(require_admin),
):
    doc = db.get(Document, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="not_found")

    approve_document(doc, admin_user_id=admin.user_id)
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


@router.post("/{doc_id}/admin/reject", response_model=DocumentOut)
def admin_reject(
    doc_id: int,
    body: AdminRejectIn,
    db: Session = Depends(get_db),
    admin: Actor = Depends(require_admin),
):
    doc = db.get(Document, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="not_found")

    reject_document(doc, admin_user_id=admin.user_id, reason=body.reason)
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


@router.post("/{doc_id}/pii/mark", response_model=DocumentOut)
def mark_pii(
    doc_id: int,
    body: PiiMarkIn,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_actor),
):
    doc = db.get(Document, doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="not_found")

    # Only owner (created_by) or admin may mark.
    if actor.user_id != doc.created_by_user_id and actor.role not in ("admin", "superadmin"):
        raise HTTPException(status_code=403, detail="forbidden")

    # constrain: allow OK/SUSPECTED/CONFIRMED; if OK => means "cleared" (MVP: allowed, but trust only uses approved+ok)
    mark_pii_status(doc, new_status=body.status, marker_user_id=actor.user_id, note=body.note)
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


@router.get("/{doc_id}", response_model=DocumentOut)
def get_document(
    doc_id: int,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_actor),
):
    doc = db.get(Document, doc_id)
    if not doc or doc.deleted_at is not None:
        raise HTTPException(status_code=404, detail="not_found")

    # object-level: require vehicle access
    require_vehicle_access(doc.vehicle_id, actor)

    # PII visibility: only owner/admin if PII != OK
    if doc.pii_status != DocumentPiiStatus.OK and actor.user_id != doc.created_by_user_id and actor.role not in ("admin", "superadmin"):
        raise HTTPException(status_code=403, detail="forbidden")

    return doc


@router.get("/{doc_id}/download")
def download_document(
    doc_id: int,
    db: Session = Depends(get_db),
    actor: Actor = Depends(require_actor),
):
    doc = db.get(Document, doc_id)
    if not doc or doc.deleted_at is not None:
        raise HTTPException(status_code=404, detail="not_found")

    require_vehicle_access(doc.vehicle_id, actor)

    # Non-admin: only valid trust evidence may be downloaded
    if actor.role not in ("admin", "superadmin"):
        if not is_valid_trust_evidence(doc):
            raise HTTPException(status_code=403, detail="forbidden")

    # In MVP we return metadata only; your project should stream from storage here.
    return {
        "storage_key": doc.storage_key,
        "filename": doc.filename,
        "content_type": doc.content_type,
        "checksum_sha256": doc.checksum_sha256,
    }