from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

from fastapi import UploadFile

_DOC_ID_RE = re.compile(r"^[a-zA-Z0-9_-]{6,128}$")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _storage_base() -> Path:
    """
    Storage liegt absichtlich im Dateisystem (nicht in DB) und wird per .gitignore ausgeschlossen.
    Default: ./storage (relativ zum server/ working dir).
    """
    base = os.getenv("LTC_STORAGE_DIR", "storage")
    p = Path(base).resolve()
    p.mkdir(parents=True, exist_ok=True)

    (p / "documents" / "quarantine").mkdir(parents=True, exist_ok=True)
    (p / "documents" / "approved").mkdir(parents=True, exist_ok=True)
    (p / "documents" / "rejected").mkdir(parents=True, exist_ok=True)
    (p / "documents" / "meta").mkdir(parents=True, exist_ok=True)

    return p


def _paths() -> Dict[str, Path]:
    base = _storage_base()
    return {
        "base": base,
        "quarantine": base / "documents" / "quarantine",
        "approved": base / "documents" / "approved",
        "rejected": base / "documents" / "rejected",
        "meta": base / "documents" / "meta",
    }


def _require_doc_id(doc_id: str) -> str:
    if not isinstance(doc_id, str) or not _DOC_ID_RE.match(doc_id):
        raise ValueError("invalid_doc_id")
    return doc_id


def _new_doc_id() -> str:
    # Kurzer, URL-sicherer Identifier
    import secrets

    return "doc_" + secrets.token_urlsafe(12).replace("-", "_")


def _meta_file(doc_id: str) -> Path:
    doc_id = _require_doc_id(doc_id)
    return _paths()["meta"] / f"{doc_id}.json"


def _file_path(doc_id: str, status: str) -> Path:
    doc_id = _require_doc_id(doc_id)
    ps = _paths()
    if status == "quarantine":
        return ps["quarantine"] / doc_id
    if status == "approved":
        return ps["approved"] / doc_id
    if status == "rejected":
        return ps["rejected"] / doc_id
    raise ValueError("invalid_status")


def _write_meta(doc_id: str, meta: Dict[str, Any]) -> None:
    mf = _meta_file(doc_id)
    tmp = mf.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, mf)


def _read_meta(doc_id: str) -> Dict[str, Any]:
    mf = _meta_file(doc_id)
    if not mf.exists():
        raise FileNotFoundError(doc_id)
    return json.loads(mf.read_text(encoding="utf-8"))


def create_document_quarantine(owner_user_id: str, upload: UploadFile) -> Dict[str, Any]:
    """
    Speichert Upload immer in quarantine.
    Metadaten werden als JSON im Storage abgelegt.
    """
    if not isinstance(owner_user_id, str) or not owner_user_id.strip():
        raise ValueError("invalid_owner_user_id")

    doc_id = _new_doc_id()

    # Für _require_doc_id: doc_id muss passen
    _require_doc_id(doc_id)

    qpath = _file_path(doc_id, "quarantine")

    h = hashlib.sha256()
    size = 0

    # UploadFile.file ist ein file-like object
    upload.file.seek(0)

    with qpath.open("wb") as out:
        while True:
            chunk = upload.file.read(1024 * 1024)
            if not chunk:
                break
            out.write(chunk)
            h.update(chunk)
            size += len(chunk)

    meta: Dict[str, Any] = {
        "doc_id": doc_id,
        "owner_user_id": owner_user_id,
        "status": "quarantine",
        "created_at": _utc_now_iso(),
        "updated_at": _utc_now_iso(),
        "original_filename": upload.filename,
        "content_type": getattr(upload, "content_type", None),
        "size_bytes": size,
        "sha256": h.hexdigest(),
    }

    _write_meta(doc_id, meta)
    return meta


def get_document_meta(doc_id: str) -> Dict[str, Any]:
    _require_doc_id(doc_id)
    return _read_meta(doc_id)


def list_quarantine_documents() -> List[Dict[str, Any]]:
    ps = _paths()
    out: List[Dict[str, Any]] = []

    for mf in sorted(ps["meta"].glob("doc_*.json")):
        try:
            meta = json.loads(mf.read_text(encoding="utf-8"))
            if meta.get("status") == "quarantine":
                out.append(meta)
        except Exception:
            # Meta kaputt -> ignorieren (fail-safe: nicht anzeigen)
            continue

    return out


def approve_document(doc_id: str, actor_user_id: str) -> Dict[str, Any]:
    _require_doc_id(doc_id)
    meta = _read_meta(doc_id)

    if meta.get("status") != "quarantine":
        raise ValueError("not_in_quarantine")

    src = _file_path(doc_id, "quarantine")
    if not src.exists():
        raise FileNotFoundError(doc_id)

    dst = _file_path(doc_id, "approved")
    os.replace(src, dst)

    meta["status"] = "approved"
    meta["updated_at"] = _utc_now_iso()
    meta["approved_by"] = actor_user_id
    meta["approved_at"] = _utc_now_iso()
    _write_meta(doc_id, meta)
    return meta


def reject_document(doc_id: str, actor_user_id: str) -> Dict[str, Any]:
    _require_doc_id(doc_id)
    meta = _read_meta(doc_id)

    if meta.get("status") != "quarantine":
        raise ValueError("not_in_quarantine")

    src = _file_path(doc_id, "quarantine")
    if not src.exists():
        raise FileNotFoundError(doc_id)

    dst = _file_path(doc_id, "rejected")
    os.replace(src, dst)

    meta["status"] = "rejected"
    meta["updated_at"] = _utc_now_iso()
    meta["rejected_by"] = actor_user_id
    meta["rejected_at"] = _utc_now_iso()
    _write_meta(doc_id, meta)
    return meta


def get_document_path_for_download(doc_id: str) -> str:
    _require_doc_id(doc_id)
    meta = _read_meta(doc_id)

    status = meta.get("status")
    if status not in {"quarantine", "approved", "rejected"}:
        raise FileNotFoundError(doc_id)

    p = _file_path(doc_id, status)
    if not p.exists():
        raise FileNotFoundError(doc_id)

    return str(p)
