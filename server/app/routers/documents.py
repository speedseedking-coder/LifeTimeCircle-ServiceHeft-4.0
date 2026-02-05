# FILE: server/app/routers/documents.py
from __future__ import annotations

from typing import Callable, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from starlette.responses import FileResponse

from app.models.documents import DocumentOut, DocumentScanStatus
from app.services.documents_store import DocumentsStore, default_store


def _resolve_require_actor() -> Callable:
    try:
        from app.auth.deps import require_actor as dep  # type: ignore
        return dep
    except Exception:
        pass
    try:
        from app.deps import require_actor as dep  # type: ignore
        return dep
    except Exception:
        pass

    # Fallback (DEV/Tests): header-basiert
    from fastapi import Header

    class _Actor:
        def __init__(self, user_id: str, role: str) -> None:
            self.user_id = user_id
            self.role = role

    def _header_actor(
        x_user_id: Optional[str] = Header(default=None, alias="X-User-Id"),
        x_role: Optional[str] = Header(default=None, alias="X-Role"),
    ):
        if not x_user_id or not x_role:
            raise HTTPException(status_code=401, detail="actor_required")
        return _Actor(user_id=x_user_id, role=x_role)

    return _header_actor


require_actor = _resolve_require_actor()


def require_roles(*allowed_roles: str) -> Callable:
    allowed = {r.lower() for r in allowed_roles if r}

    try:
        from app.auth.deps import require_roles as dep  # type: ignore
        return dep(*allowed_roles)  # type: ignore
    except Exception:
        pass
    try:
        from app.deps import require_roles as dep  # type: ignore
        return dep(*allowed_roles)  # type: ignore
    except Exception:
        pass

    def _dep(actor=Depends(require_actor)):
        role = (getattr(actor, "role", "") or "").lower()
        if role not in allowed:
            raise HTTPException(status_code=403, detail="forbidden")
        return actor

    return _dep


def _block_moderator(actor) -> None:
    if (getattr(actor, "role", "") or "").lower() == "moderator":
        raise HTTPException(status_code=403, detail="forbidden")


router = APIRouter(
    prefix="/documents",
    tags=["documents"],
)


def get_documents_store() -> DocumentsStore:
    return default_store()


class ScanBody(BaseModel):
    scan_status: DocumentScanStatus


@router.post("/upload", response_model=DocumentOut)
async def upload_document(
    file: UploadFile = File(...),
    store: DocumentsStore = Depends(get_documents_store),
    actor=Depends(require_actor),
):
    _block_moderator(actor)

    data = await file.read()
    try:
        return store.upload(
            filename=file.filename or "upload.bin",
            content_type=file.content_type or "application/octet-stream",
            data=data,
            owner_user_id=getattr(actor, "user_id", None),
        )
    except ValueError as e:
        if str(e) == "too_large":
            raise HTTPException(status_code=413, detail="too_large")
        raise


@router.get("/{doc_id}", response_model=DocumentOut)
def get_document(
    doc_id: str,
    store: DocumentsStore = Depends(get_documents_store),
    actor=Depends(require_actor),
):
    _block_moderator(actor)

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
    actor=Depends(require_actor),
):
    _block_moderator(actor)

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


@router.get("/admin/quarantine", response_model=list[DocumentOut], dependencies=[Depends(require_roles("admin", "superadmin"))])
def admin_list_quarantine(
    store: DocumentsStore = Depends(get_documents_store),
    actor=Depends(require_actor),
):
    _block_moderator(actor)
    return store.list_quarantine()


@router.post("/{doc_id}/scan", response_model=DocumentOut, dependencies=[Depends(require_roles("admin", "superadmin"))])
def admin_set_scan(
    doc_id: str,
    body: ScanBody,
    store: DocumentsStore = Depends(get_documents_store),
    actor=Depends(require_actor),
):
    _block_moderator(actor)
    return store.set_scan_status(doc_id, body.scan_status)


@router.post("/{doc_id}/approve", response_model=DocumentOut, dependencies=[Depends(require_roles("admin", "superadmin"))])
def admin_approve(
    doc_id: str,
    store: DocumentsStore = Depends(get_documents_store),
    actor=Depends(require_actor),
):
    _block_moderator(actor)
    try:
        return store.approve(doc_id)
    except ValueError as e:
        if str(e) == "not_scanned_clean":
            raise HTTPException(status_code=409, detail="not_scanned_clean")
        raise


@router.post("/{doc_id}/reject", response_model=DocumentOut, dependencies=[Depends(require_roles("admin", "superadmin"))])
def admin_reject(
    doc_id: str,
    store: DocumentsStore = Depends(get_documents_store),
    actor=Depends(require_actor),
):
    _block_moderator(actor)
    return store.reject(doc_id)