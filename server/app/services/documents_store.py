# FILE: server/app/services/documents_store.py
from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Set
from uuid import uuid4

from app.models.documents import DocumentApprovalStatus, DocumentOut, DocumentScanStatus


@dataclass(frozen=True)
class DocumentRecord:
    id: str
    owner_user_id: str
    filename: str
    content_type: str
    size_bytes: int
    storage_relpath: str
    created_at: str
    approval_status: str
    scan_status: str


class DocumentsStore:
    def __init__(
        self,
        *,
        storage_root: Path,
        db_path: Path,
        max_upload_bytes: int,
        allowed_ext: Optional[Set[str]] = None,
        allowed_mime: Optional[Set[str]] = None,
        scan_mode: str = "stub",
    ) -> None:
        self.storage_root = storage_root
        self.db_path = db_path
        self.max_upload_bytes = int(max_upload_bytes)
        self.allowed_ext = {e.lower().lstrip(".") for e in (allowed_ext or set())}
        self.allowed_mime = {m.lower() for m in (allowed_mime or set())}
        self.scan_mode = scan_mode

        self.storage_root.mkdir(parents=True, exist_ok=True)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        # Wichtig für Windows: Connections IMMER explizit schließen (sonst file-locks)
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        con = self._connect()
        try:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                  id TEXT PRIMARY KEY,
                  owner_user_id TEXT NOT NULL,
                  filename TEXT NOT NULL,
                  content_type TEXT NOT NULL,
                  size_bytes INTEGER NOT NULL,
                  storage_relpath TEXT NOT NULL,
                  created_at TEXT NOT NULL,
                  approval_status TEXT NOT NULL,
                  scan_status TEXT NOT NULL
                );
                """
            )
            con.commit()
        finally:
            con.close()

    @staticmethod
    def _now_iso_utc() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        name = (name or "").strip().replace("\\", "_").replace("/", "_")
        name = re.sub(r"[^A-Za-z0-9._-]+", "_", name)
        if not name:
            return "upload.bin"
        return name[:180]

    @staticmethod
    def _ext(name: str) -> str:
        n = name.lower()
        if "." not in n:
            return ""
        return n.rsplit(".", 1)[-1].lstrip(".")

    def _validate(self, filename: str, content_type: str, data: bytes) -> None:
        if len(data) > self.max_upload_bytes:
            raise ValueError("too_large")
        ext = self._ext(filename)
        if self.allowed_ext and ext not in self.allowed_ext:
            raise ValueError("ext_not_allowed")
        ct = (content_type or "").lower()
        if self.allowed_mime and ct not in self.allowed_mime:
            raise ValueError("mime_not_allowed")

    def upload(
        self,
        *,
        owner_user_id: str,
        filename: str,
        content_type: str,
        content_bytes: bytes,
    ) -> DocumentOut:
        safe = self._sanitize_filename(filename)
        self._validate(safe, content_type, content_bytes)

        doc_id = uuid4().hex
        rel = f"documents/{doc_id}_{safe}"
        abs_path = self.storage_root / rel
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        abs_path.write_bytes(content_bytes)

        rec = DocumentRecord(
            id=doc_id,
            owner_user_id=str(owner_user_id),
            filename=safe,
            content_type=content_type or "application/octet-stream",
            size_bytes=len(content_bytes),
            storage_relpath=rel,
            created_at=self._now_iso_utc(),
            approval_status=DocumentApprovalStatus.QUARANTINED.value,
            scan_status=DocumentScanStatus.PENDING.value,
        )

        con = self._connect()
        try:
            con.execute(
                """
                INSERT INTO documents (
                  id, owner_user_id, filename, content_type, size_bytes,
                  storage_relpath, created_at, approval_status, scan_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    rec.id,
                    rec.owner_user_id,
                    rec.filename,
                    rec.content_type,
                    rec.size_bytes,
                    rec.storage_relpath,
                    rec.created_at,
                    rec.approval_status,
                    rec.scan_status,
                ),
            )
            con.commit()
        finally:
            con.close()

        return self._to_out(rec)

    def get(self, doc_id: str) -> DocumentRecord:
        con = self._connect()
        try:
            row = con.execute(
                """
                SELECT id, owner_user_id, filename, content_type, size_bytes,
                       storage_relpath, created_at, approval_status, scan_status
                FROM documents WHERE id = ?
                """,
                (doc_id,),
            ).fetchone()
        finally:
            con.close()

        if not row:
            raise KeyError("not_found")
        return DocumentRecord(*row)

    def list_quarantine(self) -> list[DocumentOut]:
        con = self._connect()
        try:
            rows = con.execute(
                """
                SELECT id, owner_user_id, filename, content_type, size_bytes,
                       storage_relpath, created_at, approval_status, scan_status
                FROM documents
                WHERE approval_status = ?
                ORDER BY created_at DESC
                """,
                (DocumentApprovalStatus.QUARANTINED.value,),
            ).fetchall()
        finally:
            con.close()

        return [self._to_out(DocumentRecord(*r)) for r in rows]

    def set_scan_status(self, doc_id: str, status: DocumentScanStatus) -> DocumentOut:
        rec = self.get(doc_id)
        approval = rec.approval_status
        if status == DocumentScanStatus.INFECTED:
            approval = DocumentApprovalStatus.REJECTED.value

        con = self._connect()
        try:
            con.execute(
                """
                UPDATE documents
                SET scan_status = ?, approval_status = ?
                WHERE id = ?
                """,
                (status.value, approval, doc_id),
            )
            con.commit()
        finally:
            con.close()

        return self._to_out(self.get(doc_id))

    def approve(self, doc_id: str) -> DocumentOut:
        rec = self.get(doc_id)
        if rec.scan_status != DocumentScanStatus.CLEAN.value:
            raise ValueError("not_scanned_clean")

        con = self._connect()
        try:
            con.execute(
                "UPDATE documents SET approval_status = ? WHERE id = ?",
                (DocumentApprovalStatus.APPROVED.value, doc_id),
            )
            con.commit()
        finally:
            con.close()

        return self._to_out(self.get(doc_id))

    def reject(self, doc_id: str) -> DocumentOut:
        self.get(doc_id)
        con = self._connect()
        try:
            con.execute(
                "UPDATE documents SET approval_status = ? WHERE id = ?",
                (DocumentApprovalStatus.REJECTED.value, doc_id),
            )
            con.commit()
        finally:
            con.close()

        return self._to_out(self.get(doc_id))

    def file_path(self, rec: DocumentRecord) -> Path:
        return self.storage_root / rec.storage_relpath

    @staticmethod
    def actor_role(actor) -> str:
        if actor is None:
            return ""
        if isinstance(actor, dict):
            return str(actor.get("role") or "")
        return str(getattr(actor, "role", "") or "")

    @staticmethod
    def actor_user_id(actor) -> Optional[str]:
        if actor is None:
            return None
        if isinstance(actor, dict):
            v = actor.get("user_id") or actor.get("id")
            return str(v) if v else None
        v = getattr(actor, "user_id", None) or getattr(actor, "id", None)
        return str(v) if v else None

    @staticmethod
    def is_admin(actor) -> bool:
        return DocumentsStore.actor_role(actor).lower() in ("admin", "superadmin")

    def can_read_meta(self, actor, rec: DocumentRecord) -> bool:
        if self.is_admin(actor):
            return True
        uid = self.actor_user_id(actor)
        if not uid:
            return False
        if rec.approval_status != DocumentApprovalStatus.APPROVED.value:
            return False
        return uid == rec.owner_user_id

    def can_download(self, actor, rec: DocumentRecord) -> bool:
        # admin darf immer (auch quarantined), user nur wenn approved+owner
        if self.is_admin(actor):
            return True
        return self.can_read_meta(actor, rec)

    @staticmethod
    def _to_out(rec: DocumentRecord) -> DocumentOut:
        return DocumentOut(
            id=rec.id,
            owner_user_id=rec.owner_user_id,
            filename=rec.filename,
            content_type=rec.content_type,
            size_bytes=rec.size_bytes,
            approval_status=DocumentApprovalStatus(rec.approval_status),
            scan_status=DocumentScanStatus(rec.scan_status),
            created_at=rec.created_at,
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
        allowed_ext={"pdf", "png", "jpg", "jpeg"},
        allowed_mime={"application/pdf", "image/png", "image/jpeg"},
        scan_mode="stub",
    )