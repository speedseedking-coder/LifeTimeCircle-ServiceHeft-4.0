from __future__ import annotations

import hashlib
import os
import shutil
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


class DocumentStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


ALLOWED_MIME_DEFAULT = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/webp",
}

ALLOWED_EXT_DEFAULT = {
    "pdf",
    "jpg",
    "jpeg",
    "png",
    "webp",
}


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _server_root() -> Path:
    # .../server/app/services/documents_store.py -> parents[3] == server/
    return Path(__file__).resolve().parents[3]


def _normalize_allowlist_csv(value: str) -> set[str]:
    out: set[str] = set()
    for part in value.split(","):
        p = part.strip().lower()
        if p:
            out.add(p)
    return out


def sniff_mime_from_file(path: Path) -> Optional[str]:
    """
    Simple magic-number sniffing. Not a malware scanner.
    Deny-by-default: unknown -> None.
    """
    try:
        with path.open("rb") as f:
            head = f.read(32)
    except OSError:
        return None

    if head.startswith(b"%PDF-"):
        return "application/pdf"
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if len(head) >= 3 and head[0:3] == b"\xff\xd8\xff":
        return "image/jpeg"
    # WEBP: "RIFF" .... "WEBP"
    if len(head) >= 12 and head[0:4] == b"RIFF" and head[8:12] == b"WEBP":
        return "image/webp"

    return None


@dataclass(frozen=True)
class DocumentRow:
    id: str
    owner_id: str
    status: str
    original_filename: str
    content_type: str
    size_bytes: int
    sha256: str
    created_at: str
    reviewed_at: Optional[str]
    reviewed_by: Optional[str]
    rejected_reason: Optional[str]


class DocumentsStore:
    def __init__(
        self,
        *,
        storage_root: Path,
        db_path: Path,
        max_upload_bytes: int,
        allowed_ext: set[str],
        allowed_mime: set[str],
    ) -> None:
        self.storage_root = storage_root
        self.db_path = db_path
        self.max_upload_bytes = max_upload_bytes
        self.allowed_ext = allowed_ext
        self.allowed_mime = allowed_mime

        self.quarantine_dir = self.storage_root / "quarantine"
        self.approved_dir = self.storage_root / "approved"

        self.storage_root.mkdir(parents=True, exist_ok=True)
        self.quarantine_dir.mkdir(parents=True, exist_ok=True)
        self.approved_dir.mkdir(parents=True, exist_ok=True)

        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    @classmethod
    def from_env(cls) -> "DocumentsStore":
        sr = _server_root()

        storage_env = os.getenv("LTC_STORAGE_DIR", "storage").strip()
        storage_root = Path(storage_env)
        if not storage_root.is_absolute():
            storage_root = (sr / storage_root).resolve()

        db_env = os.getenv("LTC_DB_PATH", "data/app.db").strip()
        db_path = Path(db_env)
        if not db_path.is_absolute():
            db_path = (sr / db_path).resolve()

        max_bytes = int(os.getenv("LTC_MAX_UPLOAD_BYTES", str(10 * 1024 * 1024)))

        ext_csv = os.getenv("LTC_UPLOAD_EXT_ALLOWLIST", "")
        mime_csv = os.getenv("LTC_UPLOAD_MIME_ALLOWLIST", "")

        allowed_ext = _normalize_allowlist_csv(ext_csv) if ext_csv.strip() else set(ALLOWED_EXT_DEFAULT)
        allowed_mime = _normalize_allowlist_csv(mime_csv) if mime_csv.strip() else set(ALLOWED_MIME_DEFAULT)

        return cls(
            storage_root=storage_root,
            db_path=db_path,
            max_upload_bytes=max_bytes,
            allowed_ext=allowed_ext,
            allowed_mime=allowed_mime,
        )

    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(str(self.db_path))
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys = ON;")
        return con

    def _ensure_schema(self) -> None:
        con = self._connect()
        try:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    owner_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    original_filename TEXT NOT NULL,
                    content_type TEXT NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    sha256 TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    reviewed_at TEXT,
                    reviewed_by TEXT,
                    rejected_reason TEXT
                );
                """
            )
            con.execute("CREATE INDEX IF NOT EXISTS idx_documents_owner ON documents(owner_id);")
            con.execute("CREATE INDEX IF NOT EXISTS idx_documents_status_created ON documents(status, created_at);")
            con.commit()
        finally:
            con.close()

    def _ext_of(self, filename: str) -> str:
        name = (filename or "").strip()
        if "." not in name:
            return ""
        return name.rsplit(".", 1)[-1].lower().strip()

    def _paths_for(self, doc_id: str) -> Tuple[Path, Path]:
        return (self.quarantine_dir / doc_id, self.approved_dir / doc_id)

    def ingest_upload(
        self,
        *,
        owner_id: str,
        original_filename: str,
        fileobj,
    ) -> DocumentRow:
        """
        Ingests an upload into quarantine:
        - Enforces extension allowlist + size limit
        - Writes to temp file, calculates sha256
        - Sniffs mime from magic bytes (deny unknown)
        - Stores metadata in SQLite with status=PENDING
        """
        ext = self._ext_of(original_filename)
        if ext not in self.allowed_ext:
            raise ValueError("file_extension_not_allowed")

        doc_id = str(uuid.uuid4())
        quarantine_path, _approved_path = self._paths_for(doc_id)
        tmp_path = quarantine_path.with_suffix(".uploading")

        hasher = hashlib.sha256()
        size = 0

        try:
            with tmp_path.open("wb") as out:
                while True:
                    chunk = fileobj.read(64 * 1024)
                    if not chunk:
                        break
                    size += len(chunk)
                    if size > self.max_upload_bytes:
                        raise ValueError("file_too_large")
                    hasher.update(chunk)
                    out.write(chunk)

            sniffed = sniff_mime_from_file(tmp_path)
            if sniffed is None or sniffed not in self.allowed_mime:
                raise ValueError("file_mime_not_allowed")

            os.replace(str(tmp_path), str(quarantine_path))

            row = DocumentRow(
                id=doc_id,
                owner_id=owner_id,
                status=DocumentStatus.PENDING.value,
                original_filename=original_filename,
                content_type=sniffed,
                size_bytes=size,
                sha256=hasher.hexdigest(),
                created_at=_utc_now_iso(),
                reviewed_at=None,
                reviewed_by=None,
                rejected_reason=None,
            )
            self._insert_row(row)
            return row
        except Exception:
            # cleanup best-effort
            try:
                if tmp_path.exists():
                    tmp_path.unlink()
            except OSError:
                pass
            try:
                if quarantine_path.exists():
                    quarantine_path.unlink()
            except OSError:
                pass
            raise

    def _insert_row(self, row: DocumentRow) -> None:
        con = self._connect()
        try:
            con.execute(
                """
                INSERT INTO documents
                (id, owner_id, status, original_filename, content_type, size_bytes, sha256, created_at, reviewed_at, reviewed_by, rejected_reason)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row.id,
                    row.owner_id,
                    row.status,
                    row.original_filename,
                    row.content_type,
                    row.size_bytes,
                    row.sha256,
                    row.created_at,
                    row.reviewed_at,
                    row.reviewed_by,
                    row.rejected_reason,
                ),
            )
            con.commit()
        finally:
            con.close()

    def get(self, doc_id: str) -> Optional[DocumentRow]:
        con = self._connect()
        try:
            cur = con.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
            r = cur.fetchone()
            if not r:
                return None
            return DocumentRow(
                id=r["id"],
                owner_id=r["owner_id"],
                status=r["status"],
                original_filename=r["original_filename"],
                content_type=r["content_type"],
                size_bytes=int(r["size_bytes"]),
                sha256=r["sha256"],
                created_at=r["created_at"],
                reviewed_at=r["reviewed_at"],
                reviewed_by=r["reviewed_by"],
                rejected_reason=r["rejected_reason"],
            )
        finally:
            con.close()

    def list_quarantine(self, limit: int = 200) -> List[DocumentRow]:
        con = self._connect()
        try:
            cur = con.execute(
                """
                SELECT * FROM documents
                WHERE status = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (DocumentStatus.PENDING.value, int(limit)),
            )
            rows = []
            for r in cur.fetchall():
                rows.append(
                    DocumentRow(
                        id=r["id"],
                        owner_id=r["owner_id"],
                        status=r["status"],
                        original_filename=r["original_filename"],
                        content_type=r["content_type"],
                        size_bytes=int(r["size_bytes"]),
                        sha256=r["sha256"],
                        created_at=r["created_at"],
                        reviewed_at=r["reviewed_at"],
                        reviewed_by=r["reviewed_by"],
                        rejected_reason=r["rejected_reason"],
                    )
                )
            return rows
        finally:
            con.close()

    def approve(self, *, doc_id: str, reviewed_by: str) -> DocumentRow:
        row = self.get(doc_id)
        if row is None:
            raise KeyError("not_found")
        if row.status != DocumentStatus.PENDING.value:
            return row  # idempotent-ish

        quarantine_path, approved_path = self._paths_for(doc_id)
        if not quarantine_path.exists():
            raise FileNotFoundError("quarantine_file_missing")

        approved_tmp = approved_path.with_suffix(".approving")
        shutil.copyfile(str(quarantine_path), str(approved_tmp))
        os.replace(str(approved_tmp), str(approved_path))
        try:
            quarantine_path.unlink()
        except OSError:
            pass

        reviewed_at = _utc_now_iso()

        con = self._connect()
        try:
            con.execute(
                """
                UPDATE documents
                SET status = ?, reviewed_at = ?, reviewed_by = ?, rejected_reason = NULL
                WHERE id = ?
                """,
                (DocumentStatus.APPROVED.value, reviewed_at, reviewed_by, doc_id),
            )
            con.commit()
        finally:
            con.close()

        updated = self.get(doc_id)
        if updated is None:
            raise KeyError("not_found_after_update")
        return updated

    def reject(self, *, doc_id: str, reviewed_by: str, reason: str) -> DocumentRow:
        row = self.get(doc_id)
        if row is None:
            raise KeyError("not_found")
        if row.status != DocumentStatus.PENDING.value:
            return row  # idempotent-ish

        # sanitize reason (no PII enforcement here; keep it short)
        reason_clean = (reason or "").strip()
        if len(reason_clean) > 200:
            reason_clean = reason_clean[:200]

        quarantine_path, _approved_path = self._paths_for(doc_id)
        try:
            if quarantine_path.exists():
                quarantine_path.unlink()
        except OSError:
            pass

        reviewed_at = _utc_now_iso()

        con = self._connect()
        try:
            con.execute(
                """
                UPDATE documents
                SET status = ?, reviewed_at = ?, reviewed_by = ?, rejected_reason = ?
                WHERE id = ?
                """,
                (DocumentStatus.REJECTED.value, reviewed_at, reviewed_by, reason_clean, doc_id),
            )
            con.commit()
        finally:
            con.close()

        updated = self.get(doc_id)
        if updated is None:
            raise KeyError("not_found_after_update")
        return updated

    def resolve_download_path(self, doc_id: str, status: str) -> Path:
        quarantine_path, approved_path = self._paths_for(doc_id)
        if status == DocumentStatus.APPROVED.value:
            return approved_path
        return quarantine_path