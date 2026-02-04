from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.services.documents_store import DocumentStatus, DocumentsStore, ScanStatus

try:
    from app.deps import get_current_user  # type: ignore
except ImportError:  # pragma: no cover
    from app.rbac import get_current_user  # type: ignore


def _actor_role(actor: Any) -> Optional[str]:
    if isinstance(actor, dict):
        v = actor.get("role") or actor.get("user_role")
        return str(v).strip() if v is not None else None
    v = getattr(actor, "role", None) or getattr(actor, "user_role", None)
    return str(v).strip() if v is not None else None


def _actor_id(actor: Any) -> str:
    if isinstance(actor, dict):
        return str(actor.get("id") or actor.get("user_id") or actor.get("sub") or "")
    return str(getattr(actor, "id", None) or getattr(actor, "user_id", None) or getattr(actor, "sub", None) or "")


def require_actor(actor: Any = Depends(get_current_user)) -> Any:
    if actor is None or not _actor_id(actor):
        raise HTTPException(status_code=401, detail="unauthorized")
    return actor


def forbid_moderator(actor: Any = Depends(require_actor)) -> None:
    role = (_actor_role(actor) or "").lower()
    if role == "moderator":
        raise HTTPException(status_code=403, detail="forbidden")


def require_admin(actor: Any = Depends(require_actor)) -> Any:
    role = (_actor_role(actor) or "").lower()
    if role not in {"admin", "superadmin"}:
        raise HTTPException(status_code=403, detail="forbidden")
    return actor


def get_documents_store() -> DocumentsStore:
    return DocumentsStore.from_env()


router = APIRouter(
    prefix="/documents",
    tags=["documents"],
    dependencies=[Depends(require_actor), Depends(forbid_moderator)],
)


@router.post("/upload")
def upload_document(
    file: UploadFile = File(...),
    actor: Any = Depends(require_actor),
    store: DocumentsStore = Depends(get_documents_store),
) -> Dict[str, Any]:
    owner_id = _actor_id(actor)

    try:
        row = store.ingest_upload(
            owner_id=owner_id,
            original_filename=file.filename or "upload.bin",
            fileobj=file.file,
        )
    except ValueError as e:
        msg = str(e)
        if msg == "file_too_large":
            raise HTTPException(status_code=413, detail="file_too_large")
        if msg in {"file_extension_not_allowed", "file_mime_not_allowed"}:
            raise HTTPException(status_code=415, detail=msg)
        raise HTTPException(status_code=400, detail="upload_rejected")

    # scan_status exposed to owner (no PII), useful UX
    return {
        "id": row.id,
        "status": row.status,
        "scan_status": row.scan_status,
        "content_type": row.content_type,
        "size_bytes": row.size_bytes,
        "created_at": row.created_at,
        "scanned_at": row.scanned_at,
    }


@router.get("/{doc_id}")
def get_document_metadata(
    doc_id: str,
    actor: Any = Depends(require_actor),
    store: DocumentsStore = Depends(get_documents_store),
) -> Dict[str, Any]:
    row = store.get(doc_id)
    if row is None:
        raise HTTPException(status_code=404, detail="not_found")

    role = (_actor_role(actor) or "").lower()
    actor_id = _actor_id(actor)

    if role not in {"admin", "superadmin"} and row.owner_id != actor_id:
        raise HTTPException(status_code=403, detail="forbidden")

    is_admin = role in {"admin", "superadmin"}
    return {
        "id": row.id,
        "owner_id": row.owner_id if is_admin else None,
        "status": row.status,
        "scan_status": row.scan_status,
        "scanned_at": row.scanned_at,
        "scan_engine": row.scan_engine if is_admin else None,
        "scan_error": row.scan_error if is_admin else None,
        "original_filename": row.original_filename,
        "content_type": row.content_type,
        "size_bytes": row.size_bytes,
        "sha256": row.sha256 if is_admin else None,
        "created_at": row.created_at,
        "reviewed_at": row.reviewed_at,
        "reviewed_by": row.reviewed_by if is_admin else None,
        "rejected_reason": row.rejected_reason if is_admin else None,
    }


@router.get("/{doc_id}/download")
def download_document(
    doc_id: str,
    actor: Any = Depends(require_actor),
    store: DocumentsStore = Depends(get_documents_store),
):
    row = store.get(doc_id)
    if row is None:
        raise HTTPException(status_code=404, detail="not_found")

    role = (_actor_role(actor) or "").lower()
    actor_id = _actor_id(actor)

    if role not in {"admin", "superadmin"}:
        if row.owner_id != actor_id:
            raise HTTPException(status_code=403, detail="forbidden")
        if row.status != DocumentStatus.APPROVED.value:
            raise HTTPException(status_code=403, detail="not_approved")

    path = store.resolve_download_path(doc_id, row.status)
    if not path.exists():
        raise HTTPException(status_code=404, detail="file_missing")

    return FileResponse(
        path=str(path),
        media_type=row.content_type,
        filename=row.original_filename,
        headers={"X-Content-Type-Options": "nosniff"},
    )


@router.get("/admin/quarantine")
def admin_list_quarantine(
    actor: Any = Depends(require_admin),
    store: DocumentsStore = Depends(get_documents_store),
) -> Dict[str, Any]:
    rows = store.list_quarantine(limit=200)
    return {
        "items": [
            {
                "id": r.id,
                "owner_id": r.owner_id,
                "status": r.status,
                "scan_status": r.scan_status,
                "scanned_at": r.scanned_at,
                "original_filename": r.original_filename,
                "content_type": r.content_type,
                "size_bytes": r.size_bytes,
                "created_at": r.created_at,
            }
            for r in rows
        ]
    }


@router.post("/{doc_id}/scan")
def admin_rescan_document(
    doc_id: str,
    actor: Any = Depends(require_admin),
    store: DocumentsStore = Depends(get_documents_store),
) -> Dict[str, Any]:
    try:
        row = store.rescan(doc_id=doc_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="not_found")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="file_missing")

    return {
        "id": row.id,
        "status": row.status,
        "scan_status": row.scan_status,
        "scanned_at": row.scanned_at,
        "scan_engine": row.scan_engine,
        "scan_error": row.scan_error,
    }


@router.post("/{doc_id}/approve")
def admin_approve_document(
    doc_id: str,
    actor: Any = Depends(require_admin),
    store: DocumentsStore = Depends(get_documents_store),
) -> Dict[str, Any]:
    reviewer = _actor_id(actor) or "admin"

    row = store.get(doc_id)
    if row is None:
        raise HTTPException(status_code=404, detail="not_found")

    if row.scan_status != ScanStatus.CLEAN.value:
        # Scan muss CLEAN sein, sonst keine Freigabe
        raise HTTPException(status_code=409, detail="not_scanned_clean")

    try:
        row2 = store.approve(doc_id=doc_id, reviewed_by=reviewer)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="file_missing")
    except ValueError as e:
        if str(e) == "not_scanned_clean":
            raise HTTPException(status_code=409, detail="not_scanned_clean")
        raise HTTPException(status_code=400, detail="approve_failed")

    return {"id": row2.id, "status": row2.status, "reviewed_at": row2.reviewed_at}


@router.post("/{doc_id}/reject")
def admin_reject_document(
    doc_id: str,
    reason: str = "",
    actor: Any = Depends(require_admin),
    store: DocumentsStore = Depends(get_documents_store),
) -> Dict[str, Any]:
    reviewer = _actor_id(actor) or "admin"
    try:
        row = store.reject(doc_id=doc_id, reviewed_by=reviewer, reason=reason or "")
    except KeyError:
        raise HTTPException(status_code=404, detail="not_found")
    return {"id": row.id, "status": row.status, "reviewed_at": row.reviewed_at}