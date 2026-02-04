from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from app.deps import require_admin, require_user
from app.guards import forbid_moderator
from app.rbac import Actor
from app.services.documents_store import (
    approve_document,
    create_document_quarantine,
    get_document_meta,
    get_document_path_for_download,
    list_quarantine_documents,
    reject_document,
)

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
    # Wichtig für Test: jede deny-route muss forbid_moderator tragen
    dependencies=[Depends(forbid_moderator)],
)


@router.post("/upload", status_code=status.HTTP_201_CREATED)
def upload_document(
    file: UploadFile = File(...),
    user: Actor = Depends(require_user),
) -> dict:
    """
    Upload -> immer Quarantine-by-default.
    Kein "public upload". Freigabe nur via Admin.
    """
    if file is None or not getattr(file, "filename", None):
        raise HTTPException(status_code=400, detail="missing_file")

    meta = create_document_quarantine(owner_user_id=user["user_id"], upload=file)
    return {"doc": meta}


@router.get("/{doc_id}")
def get_document(
    doc_id: str,
    user: Actor = Depends(require_user),
) -> dict:
    try:
        meta = get_document_meta(doc_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="not_found")

    # Owner oder Admin/Superadmin
    if meta.get("owner_user_id") != user["user_id"] and user["role"] not in {"admin", "superadmin"}:
        raise HTTPException(status_code=403, detail="forbidden")

    return {"doc": meta}


@router.get("/{doc_id}/download")
def download_document(
    doc_id: str,
    user: Actor = Depends(require_user),
):
    try:
        meta = get_document_meta(doc_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="not_found")

    if meta.get("owner_user_id") != user["user_id"] and user["role"] not in {"admin", "superadmin"}:
        raise HTTPException(status_code=403, detail="forbidden")

    try:
        # Quarantine-by-default: Download für non-admin nur bei Status APPROVED (deny-by-default)
        __doc = meta
        if isinstance(__doc, dict) and isinstance(__doc.get('doc'), dict):
            __doc = __doc['doc']
        __st = str((__doc.get('status') or '')).strip().lower() if isinstance(__doc, dict) else ''
        __role = ''
        try:
            if isinstance(user, dict):
                __role = str((user.get('role') or '')).strip().lower()
            else:
                __role = str(getattr(user, 'role', '')).strip().lower()
        except Exception:
            __role = ''
        if __role not in ('admin', 'superadmin') and __st != 'approved':
            raise HTTPException(status_code=404, detail='not_found')
        path = get_document_path_for_download(doc_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="file_missing")

    filename = meta.get("original_filename") or f"{doc_id}.bin"
    media_type = meta.get("content_type") or "application/octet-stream"
    return FileResponse(path=path, filename=filename, media_type=media_type)


@router.get("/admin/quarantine")
def admin_list_quarantine(
    admin: Actor = Depends(require_admin),
) -> dict:
    docs = list_quarantine_documents()
    return {"quarantine": docs, "count": len(docs)}


@router.post("/{doc_id}/approve")
def admin_approve(
    doc_id: str,
    admin: Actor = Depends(require_admin),
) -> dict:
    try:
        meta = approve_document(doc_id=doc_id, actor_user_id=admin["user_id"])
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="not_found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"doc": meta}


@router.post("/{doc_id}/reject")
def admin_reject(
    doc_id: str,
    admin: Actor = Depends(require_admin),
) -> dict:
    try:
        meta = reject_document(doc_id=doc_id, actor_user_id=admin["user_id"])
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="not_found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"doc": meta}

