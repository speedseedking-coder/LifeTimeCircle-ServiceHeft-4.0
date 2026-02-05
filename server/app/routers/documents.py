from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from pydantic import BaseModel
from starlette.responses import FileResponse

from app.models.documents import DocumentOut, DocumentScanStatus
from app.services.documents_store import DocumentsStore, default_store

# singleton store (can be overridden in tests via dependency_overrides)
_STORE: DocumentsStore = default_store()


def get_documents_store() -> DocumentsStore:
    return _STORE


def require_actor(request: Request):
    # Production: actor sollte durch Auth-Middleware gesetzt sein.
    actor = getattr(request.state, "actor", None) or request.scope.get("actor")
    if actor is not None:
        return actor

    # Dev/Smoke: Header-Fallback
    role = request.headers.get("X-Role") or request.headers.get("x-role")
    user_id = request.headers.get("X-User-Id") or request.headers.get("x-user-id")
    if role and user_id:
        return {"role": role, "user_id": user_id}

    raise HTTPException(status_code=401, detail="unauthorized")


def forbid_moderator(actor=Depends(require_actor)) -> None:
    role = DocumentsStore.actor_role(actor).lower()
    if role == "moderator":
        raise HTTPException(status_code=403, detail="forbidden")


router = APIRouter(
    prefix="/documents",
    tags=["documents"],
    dependencies=[Depends(forbid_moderator)],
)


class ScanIn(BaseModel):
    scan_status: DocumentScanStatus


@router.post("/upload", response_model=DocumentOut)
async def upload_document(
    file: UploadFile = File(...),
    actor=Depends(require_actor),
    store: DocumentsStore = Depends(get_documents_store),
):
    uid = store.actor_user_id(actor)
    if not uid:
        raise HTTPException(status_code=401, detail="unauthorized")

    content = await file.read()
    try:
        return store.upload(
            owner_user_id=str(uid),
            filename=file.filename or "upload.bin",
            content_type=file.content_type or "application/octet-stream",
            content_bytes=content,
        )
    except ValueError as e:
        msg = str(e)
        if msg == "too_large":
            raise HTTPException(status_code=413, detail="too_large")
        if msg in ("ext_not_allowed", "mime_not_allowed"):
            raise HTTPException(status_code=415, detail=msg)
        raise


@router.get("/{doc_id}", response_model=DocumentOut)
def get_document(
    doc_id: str,
    actor=Depends(require_actor),
    store: DocumentsStore = Depends(get_documents_store),
):
    try:
        rec = store.get(doc_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="not_found")

    if not store.can_read_meta(actor, rec):
        raise HTTPException(status_code=403, detail="forbidden")

    return store._to_out(rec)  # type: ignore[attr-defined]


@router.get("/{doc_id}/download")
def download_document(
    doc_id: str,
    actor=Depends(require_actor),
    store: DocumentsStore = Depends(get_documents_store),
):
    try:
        rec = store.get(doc_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="not_found")

    if not store.can_download(actor, rec):
        raise HTTPException(status_code=403, detail="forbidden")

    path: Path = store.file_path(rec)
    if not path.exists():
        raise HTTPException(status_code=500, detail="storage_missing")

    return FileResponse(path=path, filename=rec.filename, media_type=rec.content_type)


@router.get("/admin/quarantine", response_model=list[DocumentOut])
def admin_list_quarantine(
    actor=Depends(require_actor),
    store: DocumentsStore = Depends(get_documents_store),
):
    if not store.is_admin(actor):
        raise HTTPException(status_code=403, detail="forbidden")
    return store.list_quarantine()


@router.post("/{doc_id}/scan", response_model=DocumentOut)
def admin_set_scan(
    doc_id: str,
    body: ScanIn,
    actor=Depends(require_actor),
    store: DocumentsStore = Depends(get_documents_store),
):
    if not store.is_admin(actor):
        raise HTTPException(status_code=403, detail="forbidden")
    try:
        return store.set_scan_status(doc_id, body.scan_status)
    except KeyError:
        raise HTTPException(status_code=404, detail="not_found")


@router.post("/{doc_id}/approve", response_model=DocumentOut)
def admin_approve(
    doc_id: str,
    actor=Depends(require_actor),
    store: DocumentsStore = Depends(get_documents_store),
):
    if not store.is_admin(actor):
        raise HTTPException(status_code=403, detail="forbidden")
    try:
        return store.approve(doc_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="not_found")
    except ValueError as e:
        if str(e) == "not_scanned_clean":
            raise HTTPException(status_code=409, detail="not_scanned_clean")
        raise


@router.post("/{doc_id}/reject", response_model=DocumentOut)
def admin_reject(
    doc_id: str,
    actor=Depends(require_actor),
    store: DocumentsStore = Depends(get_documents_store),
):
    if not store.is_admin(actor):
        raise HTTPException(status_code=403, detail="forbidden")
    try:
        return store.reject(doc_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="not_found")