from __future__ import annotations

from functools import lru_cache
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.services.documents_store import DocumentStatus, DocumentsStore


# ---- Auth/RBAC deps (use existing project deps if present; otherwise safe-stub) ----
try:
    from app.auth.deps import require_actor as require_actor  # type: ignore
except Exception:  # pragma: no cover
    def require_actor() -> Any:  # type: ignore
        raise HTTPException(status_code=401, detail="auth_not_configured")


try:
    from app.auth.deps import forbid_moderator as forbid_moderator  # type: ignore
except Exception:  # pragma: no cover
    def forbid_moderator(actor: Any = Depends(require_actor)) -> None:  # type: ignore
        role = _actor_role(actor)
        if role == "moderator":
            raise HTTPException(status_code=403, detail="forbidden")


def _actor_role(actor: Any) -> Optional[str]:
    if isinstance(actor, dict):
        return (actor.get("role") or actor.get("user_role") or "").strip() or None
    return getattr(actor, "role", None) or getattr(actor, "user_role", None)


def _actor_id(actor: Any) -> str:
    if isinstance(actor, dict):
        return str(actor.get("id") or actor.get("user_id") or actor.get("sub") or "")
    return str(getattr(actor, "id", None) or getattr(actor, "user_id", None) or getattr(actor, "sub", None) or "")


def require_admin(actor: Any = Depends(require_actor)) -> Any:
    role = _actor_role(actor)
    if role not in {"admin", "superadmin"}:
        raise HTTPException(status_code=403, detail="forbidden")
    return actor


@lru_cache(maxsize=1)
def _default_store() -> DocumentsStore:
    return DocumentsStore.from_env()


def get_documents_store() -> DocumentsStore:
    return _default_store()


router = APIRouter(
    prefix="/documents",
    tags=["documents"],
    dependencies=[Depends(require_actor), Depends(forbid_moderator)],
)


# ---- Routes ----

@router.post("/upload")
def upload_document(
    file: UploadFile = File(...),
    actor: Any = Depends(require_actor),
    store: DocumentsStore = Depends(get_documents_store),
) -> Dict[str, Any]:
    owner_id = _actor_id(actor)
    if not owner_id:
        raise HTTPException(status_code=401, detail="unauthorized")

    try:
        row = store.ingest_upload(owner_id=owner_id, original_filename=file.filename or "upload.bin", fileobj=file.file)
    except ValueError as e:
        msg = str(e)
        if msg == "file_too_large":
            raise HTTPException(status_code=413, detail="file_too_large")
        if msg in {"file_extension_not_allowed", "file_mime_not_allowed"}:
            raise HTTPException(status_code=415, detail=msg)
        raise HTTPException(status_code=400, detail="upload_rejected")

    return {
        "id": row.id,
        "status": row.status,
        "content_type": row.content_type,
        "size_bytes": row.size_bytes,
        "created_at": row.created_at,
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

    role = _actor_role(actor)
    actor_id = _actor_id(actor)

    # own scope or admin
    if role not in {"admin", "superadmin"} and row.owner_id != actor_id:
        raise HTTPException(status_code=403, detail="forbidden")

    return {
        "id": row.id,
        "owner_id": row.owner_id if role in {"admin", "superadmin"} else None,
        "status": row.status,
        "original_filename": row.original_filename,
        "content_type": row.content_type,
        "size_bytes": row.size_bytes,
        "sha256": row.sha256 if role in {"admin", "superadmin"} else None,
        "created_at": row.created_at,
        "reviewed_at": row.reviewed_at,
        "reviewed_by": row.reviewed_by if role in {"admin", "superadmin"} else None,
        "rejected_reason": row.rejected_reason if role in {"admin", "superadmin"} else None,
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

    role = _actor_role(actor)
    actor_id = _actor_id(actor)

    # Admin/Superadmin: may review-download even while pending
    if role not in {"admin", "superadmin"}:
        # user/vip/dealer: only own + APPROVED
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
                "original_filename": r.original_filename,
                "content_type": r.content_type,
                "size_bytes": r.size_bytes,
                "created_at": r.created_at,
            }
            for r in rows
        ]
    }


@router.post("/{doc_id}/approve")
def admin_approve_document(
    doc_id: str,
    actor: Any = Depends(require_admin),
    store: DocumentsStore = Depends(get_documents_store),
) -> Dict[str, Any]:
    reviewer = _actor_id(actor) or "admin"
    try:
        row = store.approve(doc_id=doc_id, reviewed_by=reviewer)
    except KeyError:
        raise HTTPException(status_code=404, detail="not_found")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="file_missing")
    return {"id": row.id, "status": row.status, "reviewed_at": row.reviewed_at}


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