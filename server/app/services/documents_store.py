# FILE: server/app/services/documents_store.py
from __future__ import annotations

import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional, Set

from app.models.documents import DocumentApprovalStatus, DocumentOut, DocumentScanStatus


@dataclass(frozen=True)
class DocumentRecord:
    id: str
    filename: str
    content_type: str
    size_bytes: int
    storage_relpath: str
    owner_user_id: Optional[str]
    created_at: str
    approval_status: str
    scan_status: str


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_filename(name: str) -> str:
    name = (name or "upload.bin").strip()
    name = name.replace("\\", "_").replace("/", "_")
    out = []
    for ch in name:
        if ch.isalnum() or ch in {".", "-", "_"}:
            out.append(ch)
        else:
            out.append("_")
    safe = "".join(out).strip("._")
    return safe or "upload.bin"


def _file_ext_lower(filename: str) -> str:
    f = (filename or "").strip().lower()
    if "." not in f:
        return ""
    return f.rsplit(".", 1)[-1].strip().lstrip(".")


def _normalize_mime(m: str) -> str:
    return (m or "").split(";", 1)[0].strip().lower()


def _norm_set(vals: Optional[Iterable[str]]) -> Optional[Set[str]]:
    if vals is None:
        return None
    s = {str(v).strip().lower() for v in vals if str(v).strip()}
    return s if s else None


def _actor_get(actor, *keys: str) -> Optional[str]:
    if actor is None:
        return None
    if isinstance(actor, dict):
        for k in keys:
            v = actor.get(k)
            if v is not None and str(v).strip():
                return str(v)
        return None
    for k in keys:
        v = getattr(actor, k, None)
        if v is not None and str(v).strip():
            return str(v)
    return None


def _is_admin_role(role: Optional[str]) -> bool:
    return (role or "").lower() in {"admin", "superadmin"}


class DocumentsStore:
    def __init__(
        self,
        storage_root: Path,
        db_path: Path,
        max_upload_bytes: int,
        allowed_ext: Optional[set[str]] = None,
        allowed_mime: Optional[set[str]] = None,
        scan_mode: str = "stub",
    ) -> None:
        self.storage_root = Path(storage_root)
        self.db_path = Path(db_path)
        self.max_upload_bytes = int(max_upload_bytes)

        self.allowed_ext = _norm_set({str(e).lstrip(".") for e in (allowed_ext or set())}) if allowed_ext is not None else None
        self.allowed_mime = _norm_set({_normalize_mime(m) for m in (allowed_mime or set())}) if allowed_mime is not None else None

        self.scan_mode = str(scan_mode or "stub").strip().lower()

        self.storage_root.mkdir(parents=True, exist_ok=True)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.db_path)
        con.row_factory = sqlite3.Row
        return con

    def _init_db(self) -> None:
        with self._connect() as con:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                  id TEXT PRIMARY KEY,
                  filename TEXT NOT NULL,
                  content_type TEXT NOT NULL,
                  size_bytes INTEGER NOT NULL,
                  storage_relpath TEXT NOT NULL,
                  owner_user_id TEXT,
                  created_at TEXT NOT NULL,
                  approval_status TEXT NOT NULL,
                  scan_status TEXT NOT NULL
                )
                """
            )
            con.execute(
                "CREATE INDEX IF NOT EXISTS idx_documents_approval_status ON documents(approval_status)"
            )
            con.execute(
                "CREATE INDEX IF NOT EXISTS idx_documents_owner_user_id ON documents(owner_user_id)"
            )

    def upload(
        self,
        *,
        filename: str,
        content_type: str,
        data: bytes,
        owner_user_id: Optional[str],
    ) -> DocumentOut:
        if data is None:
            data = b""
        if len(data) > self.max_upload_bytes:
            raise ValueError("too_large")

        safe = _safe_filename(filename)
        ext = _file_ext_lower(safe)
        mime = _normalize_mime(content_type or "application/octet-stream")

        if self.allowed_ext is not None:
            if not ext or ext not in self.allowed_ext:
                raise ValueError("ext_not_allowed")

        if self.allowed_mime is not None:
            if not mime or mime not in self.allowed_mime:
                raise ValueError("mime_not_allowed")

        doc_id = uuid.uuid4().hex
        rel = f"documents/{doc_id}_{safe}"
        abs_path = self.storage_root / rel
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        abs_path.write_bytes(data)

        rec = DocumentRecord(
            id=doc_id,
            filename=safe,
            content_type=mime or "application/octet-stream",
            size_bytes=len(data),
            storage_relpath=rel,
            owner_user_id=owner_user_id,
            created_at=_utc_now_iso(),
            approval_status=DocumentApprovalStatus.QUARANTINED.value,
            scan_status=DocumentScanStatus.PENDING.value,
        )

        with self._connect() as con:
            con.execute(
                """
                INSERT INTO documents (
                  id, filename, content_type, size_bytes,
                  storage_relpath, owner_user_id,
                  created_at, approval_status, scan_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    rec.id,
                    rec.filename,
                    rec.content_type,
                    rec.size_bytes,
                    rec.storage_relpath,
                    rec.owner_user_id,
                    rec.created_at,
                    rec.approval_status,
                    rec.scan_status,
                ),
            )

        return self._to_out(rec)

    def _get_record(self, doc_id: str) -> DocumentRecord:
        with self._connect() as con:
            row = con.execute(
                """
                SELECT id, filename, content_type, size_bytes, storage_relpath,
                       owner_user_id, created_at, approval_status, scan_status
                FROM documents WHERE id = ?
                """,
                (doc_id,),
            ).fetchone()
        if not row:
            raise KeyError("not_found")
        return DocumentRecord(
            id=row["id"],
            filename=row["filename"],
            content_type=row["content_type"],
            size_bytes=int(row["size_bytes"]),
            storage_relpath=row["storage_relpath"],
            owner_user_id=row["owner_user_id"],
            created_at=row["created_at"],
            approval_status=row["approval_status"],
            scan_status=row["scan_status"],
        )

    def get_out(self, doc_id: str) -> DocumentOut:
        return self._to_out(self._get_record(doc_id))

    def list_quarantine(self) -> list[DocumentOut]:
        with self._connect() as con:
            rows = con.execute(
                """
                SELECT id, filename, content_type, size_bytes, storage_relpath,
                       owner_user_id, created_at, approval_status, scan_status
                FROM documents
                WHERE approval_status = ?
                ORDER BY created_at DESC
                """,
                (DocumentApprovalStatus.QUARANTINED.value,),
            ).fetchall()

        outs: list[DocumentOut] = []
        for row in rows:
            outs.append(
                self._to_out(
                    DocumentRecord(
                        id=row["id"],
                        filename=row["filename"],
                        content_type=row["content_type"],
                        size_bytes=int(row["size_bytes"]),
                        storage_relpath=row["storage_relpath"],
                        owner_user_id=row["owner_user_id"],
                        created_at=row["created_at"],
                        approval_status=row["approval_status"],
                        scan_status=row["scan_status"],
                    )
                )
            )
        return outs

    def set_scan_status(self, doc_id: str, status: DocumentScanStatus) -> DocumentOut:
        if self.scan_mode in {"disabled", "off", "none"}:
            raise ValueError("scan_disabled")

        if not isinstance(status, DocumentScanStatus):
            status = DocumentScanStatus(str(status).upper())

        approval = None
        if status == DocumentScanStatus.INFECTED:
            approval = DocumentApprovalStatus.REJECTED.value

        with self._connect() as con:
            if approval is None:
                con.execute(
                    "UPDATE documents SET scan_status = ? WHERE id = ?",
                    (status.value, doc_id),
                )
            else:
                con.execute(
                    "UPDATE documents SET scan_status = ?, approval_status = ? WHERE id = ?",
                    (status.value, approval, doc_id),
                )

        return self.get_out(doc_id)

    def approve(self, doc_id: str) -> DocumentOut:
        rec = self._get_record(doc_id)
        if rec.scan_status != DocumentScanStatus.CLEAN.value:
            raise ValueError("not_scanned_clean")

        with self._connect() as con:
            con.execute(
                "UPDATE documents SET approval_status = ? WHERE id = ?",
                (DocumentApprovalStatus.APPROVED.value, doc_id),
            )
        return self.get_out(doc_id)

    def reject(self, doc_id: str) -> DocumentOut:
        with self._connect() as con:
            con.execute(
                "UPDATE documents SET approval_status = ? WHERE id = ?",
                (DocumentApprovalStatus.REJECTED.value, doc_id),
            )
        return self.get_out(doc_id)

    def resolve_path(self, doc_id: str) -> Path:
        rec = self._get_record(doc_id)
        return self.storage_root / rec.storage_relpath

    def can_read(self, actor, rec: DocumentRecord) -> bool:
        role = _actor_get(actor, "role")
        if _is_admin_role(role):
            return True
        if rec.approval_status != DocumentApprovalStatus.APPROVED.value:
            return False
        actor_id = _actor_get(actor, "user_id", "uid", "id")
        return bool(rec.owner_user_id) and actor_id == rec.owner_user_id

    def can_download(self, actor, rec: DocumentRecord) -> bool:
        # Admin darf immer (auch quarantined), user nur wenn approved+owner
        role = _actor_get(actor, "role")
        if _is_admin_role(role):
            return True
        return self.can_read(actor, rec)

    def _to_out(self, rec: DocumentRecord) -> DocumentOut:
        s = rec.created_at or _utc_now_iso()
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        created = datetime.fromisoformat(s)
        return DocumentOut(
            id=rec.id,
            filename=rec.filename,
            content_type=rec.content_type,
            size_bytes=int(rec.size_bytes),
            created_at=created,
            owner_user_id=rec.owner_user_id,
            approval_status=DocumentApprovalStatus(rec.approval_status),
            scan_status=DocumentScanStatus(rec.scan_status),
        )


def default_store() -> DocumentsStore:
    server_root = Path(__file__).resolve().parents[3]
    storage_root = server_root / "storage"
    db_path = server_root / "data" / "documents.sqlite"
    return DocumentsStore(
        storage_root=storage_root,
        db_path=db_path,
        max_upload_bytes=10 * 1024 * 1024,
        allowed_ext={"pdf"},
        allowed_mime={"application/pdf"},
        scan_mode="stub",
    )