# FILE: server/app/routers/documents.py
from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from starlette.responses import FileResponse

from app.deps import get_actor, require_roles
from app.models.documents import DocumentOut, DocumentScanStatus
from app.services.documents_store import DocumentsStore, default_store


def forbid_moderator(actor=Depends(get_actor)):
    role = None
    if isinstance(actor, dict):
        role = actor.get("role")
    else:
        role = getattr(actor, "role", None)
    if (role or "").lower() == "moderator":
        raise HTTPException(status_code=403, detail="forbidden")
    return actor


router = APIRouter(
    prefix="/documents",
    tags=["documents"],
    dependencies=[Depends(get_actor), Depends(forbid_moderator)],
)


def get_documents_store() -> DocumentsStore:
    return default_store()


def _actor_id(actor) -> str | None:
    if actor is None:
        return None
    if isinstance(actor, dict):
        return (actor.get("user_id") or actor.get("uid") or actor.get("id"))
    return getattr(actor, "user_id", None) or getattr(actor, "uid", None) or getattr(actor, "id", None)


class ScanBody(BaseModel):
    scan_status: DocumentScanStatus


@router.post("/upload", response_model=DocumentOut)
async def upload_document(
    file: UploadFile = File(...),
    store: DocumentsStore = Depends(get_documents_store),
    actor=Depends(get_actor),
):
    data = await file.read()
    try:
        return store.upload(
            filename=file.filename or "upload.pdf",
            content_type=file.content_type or "application/octet-stream",
            data=data,
            owner_user_id=_actor_id(actor),
        )
    except ValueError as e:
        if str(e) == "too_large":
            raise HTTPException(status_code=413, detail="too_large")
        if str(e) in {"ext_not_allowed", "mime_not_allowed"}:
            raise HTTPException(status_code=415, detail="filetype_not_allowed")
        raise


@router.get("/{doc_id}", response_model=DocumentOut)
def get_document(
    doc_id: str,
    store: DocumentsStore = Depends(get_documents_store),
    actor=Depends(get_actor),
):
    try:
        rec = store._get_record(doc_id)  # pylint: disable=protected-access
    except KeyError:
        raise HTTPException(status_code=404, detail="not_found")

    if not store.can_read(actor, rec):
        raise HTTPException(status_code=403, detail="forbidden")

    return store._to_out(rec)  # pylint: disable=protected-access


@router.get("/{doc_id}/download")
def download_document(
    doc_id: str,
    store: DocumentsStore = Depends(get_documents_store),
    actor=Depends(get_actor),
):
    try:
        rec = store._get_record(doc_id)  # pylint: disable=protected-access
    except KeyError:
        raise HTTPException(status_code=404, detail="not_found")

    if not store.can_download(actor, rec):
        raise HTTPException(status_code=403, detail="forbidden")

    path = store.resolve_path(doc_id)
    if not path.exists():
        raise HTTPException(status_code=500, detail="storage_missing")

    return FileResponse(path=path, filename=rec.filename, media_type=rec.content_type)


@router.get(
    "/admin/quarantine",
    response_model=list[DocumentOut],
    dependencies=[Depends(require_roles("admin", "superadmin"))],
)
def admin_list_quarantine(
    store: DocumentsStore = Depends(get_documents_store),
):
    return store.list_quarantine()


@router.post(
    "/{doc_id}/scan",
    response_model=DocumentOut,
    dependencies=[Depends(require_roles("admin", "superadmin"))],
)
def admin_set_scan(
    doc_id: str,
    body: ScanBody,
    store: DocumentsStore = Depends(get_documents_store),
):
    try:
        return store.set_scan_status(doc_id, body.scan_status)
    except ValueError as e:
        if str(e) == "scan_disabled":
            raise HTTPException(status_code=409, detail="scan_disabled")
        raise


@router.post(
    "/{doc_id}/approve",
    response_model=DocumentOut,
    dependencies=[Depends(require_roles("admin", "superadmin"))],
)
def admin_approve(
    doc_id: str,
    store: DocumentsStore = Depends(get_documents_store),
):
    try:
        return store.approve(doc_id)
    except ValueError as e:
        if str(e) == "not_scanned_clean":
            raise HTTPException(status_code=409, detail="not_scanned_clean")
        raise


@router.post(
    "/{doc_id}/reject",
    response_model=DocumentOut,
    dependencies=[Depends(require_roles("admin", "superadmin"))],
)
def admin_reject(
    doc_id: str,
    store: DocumentsStore = Depends(get_documents_store),
):
    return store.reject(doc_id)