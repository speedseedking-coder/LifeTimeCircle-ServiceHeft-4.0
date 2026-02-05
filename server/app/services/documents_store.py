# FILE: server/app/services/documents_store.py
from __future__ import annotations

import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

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
    # allow only a conservative set
    out = []
    for ch in name:
        if ch.isalnum() or ch in {".", "-", "_"}:
            out.append(ch)
        else:
            out.append("_")
    safe = "".join(out).strip("._")
    return safe or "upload.bin"


def _is_admin_role(role: Optional[str]) -> bool:
    return (role or "").lower() in {"admin", "superadmin"}


class DocumentsStore:
    def __init__(
        self,
        storage_root: Path,
        db_path: Path,
        max_upload_bytes: int,
        scan_mode: str = "stub",
    ) -> None:
        self.storage_root = Path(storage_root)
        self.db_path = Path(db_path)
        self.max_upload_bytes = int(max_upload_bytes)
        self.scan_mode = str(scan_mode or "stub")

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

        doc_id = uuid.uuid4().hex
        safe = _safe_filename(filename)
        rel = f"documents/{doc_id}_{safe}"
        abs_path = self.storage_root / rel
        abs_path.parent.mkdir(parents=True, exist_ok=True)

        abs_path.write_bytes(data)

        rec = DocumentRecord(
            id=doc_id,
            filename=safe,
            content_type=content_type or "application/octet-stream",
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
        if not isinstance(status, DocumentScanStatus):
            status = DocumentScanStatus(str(status))

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
        role = getattr(actor, "role", None)
        if _is_admin_role(role):
            return True
        if rec.approval_status != DocumentApprovalStatus.APPROVED.value:
            return False
        # MVP-scope: owner-only (object-level)
        return bool(rec.owner_user_id) and getattr(actor, "user_id", None) == rec.owner_user_id

    def can_download(self, actor, rec: DocumentRecord) -> bool:
        return self.can_read(actor, rec)

    def _to_out(self, rec: DocumentRecord) -> DocumentOut:
        created = datetime.fromisoformat(rec.created_at.replace("Z", "+00:00"))
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
    # .../server/app/services/documents_store.py -> parents[3] == server/
    server_root = Path(__file__).resolve().parents[3]
    storage_root = server_root / "storage"
    db_path = server_root / "data" / "documents.sqlite"
    return DocumentsStore(
        storage_root=storage_root,
        db_path=db_path,
        max_upload_bytes=10 * 1024 * 1024,
        scan_mode="stub",
    )