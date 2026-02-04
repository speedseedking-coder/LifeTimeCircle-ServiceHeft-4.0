server/app/routers/documents.py
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from app.deps import require_admin, require_user
from app.rbac import Actor
from app.services.documents_store import (
    create_quarantine_document,
    get_document,
    list_quarantine,
    mark_approved,
    mark_rejected,
)

router = APIRouter(prefix="/documents", tags=["documents"])


def _storage_base() -> Path:
    # lokal, nicht in Git: server/storage/...
    base = os.getenv("LTC_STORAGE_DIR", os.path.join(".", "storage"))
    return Path(base).resolve()


def _quarantine_dir() -> Path:
    p = _storage_base() / "quarantine"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _approved_dir() -> Path:
    p = _storage_base() / "approved"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _max_bytes() -> int:
    # Default: 10MB
    try:
        return int(os.getenv("LTC_UPLOAD_MAX_BYTES", "10000000"))
    except Exception:
        return 10000000


_ALLOWED_EXT = {".pdf", ".png", ".jpg", ".jpeg"}
_ALLOWED_CT = {"application/pdf", "image/png", "image/jpeg"}


def _sniff_ok(content_type: str, head: bytes) -> bool:
    # minimal signature checks (kein Magic dependency)
    if content_type == "application/pdf":
        return head.startswith(b"%PDF-")
    if content_type == "image/png":
        return head.startswith(b"\x89PNG\r\n\x1a\n")
    if content_type == "image/jpeg":
        return head.startswith(b"\xff\xd8\xff")
    return False


def _is_admin(actor: Actor) -> bool:
    return actor["role"] in {"admin", "superadmin"}


@router.post("/upload")
async def upload_document(
    user: Actor = Depends(require_user),
    file: UploadFile = File(...),
    title: Optional[str] = Form(default=None),
) -> dict:
    # moderator/public sind durch require_user ausgeschlossen
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="missing_filename")

    ext = Path(file.filename).suffix.lower()
    if ext not in _ALLOWED_EXT:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="filetype_not_allowed")

    ct = (file.content_type or "").lower().strip()
    if ct not in _ALLOWED_CT:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="content_type_not_allowed")

    head = await file.read(16)
    await file.seek(0)
    if not _sniff_ok(ct, head):
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="content_signature_mismatch")

    doc_id = f"doc_{uuid4().hex}"
    stored_name = f"{doc_id}{ext}"

    qdir = _quarantine_dir()
    tmp_path = qdir / f"tmp_{doc_id}{ext}"
    final_path = qdir / stored_name

    max_b = _max_bytes()
    size = 0

    try:
        with tmp_path.open("wb") as f:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > max_b:
                    raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="file_too_large")
                f.write(chunk)
    finally:
        await file.close()

    # DB-Eintrag anlegen (Quarantine)
    doc = create_quarantine_document(
        doc_id=doc_id,
        owner_user_id=user["user_id"],
        original_filename=file.filename,
        stored_name=stored_name,
        content_type=ct,
        size_bytes=size,
    )

    tmp_path.replace(final_path)

    return {
        "doc_id": doc.doc_id,
        "status": "quarantine",
        "content_type": ct,
        "size_bytes": size,
        "original_filename": file.filename,
        "title": title,
    }


@router.get("/{doc_id}")
def get_document_meta(doc_id: str, user: Actor = Depends(require_user)) -> dict:
    doc = get_document(doc_id)
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")

    # deny-by-default: user/vip/dealer nur eigene Dokumente; admin/superadmin alles
    if not _is_admin(user) and doc.owner_user_id != user["user_id"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")

    d = doc.to_dict()
    d.pop("stored_name", None)  # keine internen Dateinamen raus
    return d


@router.get("/{doc_id}/download")
def download_document(doc_id: str, user: Actor = Depends(require_user)):
    doc = get_document(doc_id)
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")

    if not _is_admin(user) and doc.owner_user_id != user["user_id"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")

    # Quarantine ist nicht downloadbar für normale User (nur admin/superadmin)
    if doc.status != "approved" and not _is_admin(user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="not_approved")

    base = _approved_dir() if doc.status == "approved" else _quarantine_dir()
    path = (base / doc.stored_name).resolve()

    # safety: path muss unter storage base liegen
    if _storage_base() not in path.parents:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="storage_path_invalid")

    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="file_missing")

    return FileResponse(
        path=str(path),
        media_type=doc.content_type,
        filename=doc.original_filename,
    )


@router.get("/admin/quarantine")
def admin_list_quarantine(limit: int = 50, user: Actor = Depends(require_admin)) -> dict:
    items = [d.to_dict() for d in list_quarantine(limit=limit)]
    for it in items:
        it.pop("stored_name", None)
    return {"items": items}


@router.post("/{doc_id}/approve")
def admin_approve(doc_id: str, user: Actor = Depends(require_admin)) -> dict:
    doc = get_document(doc_id)
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")

    if doc.status == "approved":
        d = doc.to_dict()
        d.pop("stored_name", None)
        return d

    if doc.status != "quarantine":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="not_in_quarantine")

    src = (_quarantine_dir() / doc.stored_name).resolve()
    if not src.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="file_missing")

    dst = (_approved_dir() / doc.stored_name).resolve()
    src.replace(dst)

    updated = mark_approved(doc_id, approved_by=user["user_id"])
    assert updated is not None
    d = updated.to_dict()
    d.pop("stored_name", None)
    return d


@router.post("/{doc_id}/reject")
def admin_reject(
    doc_id: str,
    reason: str = Form(...),
    user: Actor = Depends(require_admin),
) -> dict:
    doc = get_document(doc_id)
    if doc is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")

    if doc.status == "rejected":
        d = doc.to_dict()
        d.pop("stored_name", None)
        return d

    if doc.status != "quarantine":
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="not_in_quarantine")

    # Datei löschen (Quarantine) – keine Aufbewahrung von potentiell schädlichem Content
    p = (_quarantine_dir() / doc.stored_name).resolve()
    try:
        if p.exists():
            p.unlink()
    except Exception:
        pass

    updated = mark_rejected(doc_id, rejected_by=user["user_id"], reason=reason)
    assert updated is not None
    d = updated.to_dict()
    d.pop("stored_name", None)
    return d
