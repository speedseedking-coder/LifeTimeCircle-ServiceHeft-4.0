# FILE: server/scripts/patch_documents_quarantine_p0_v2.ps1
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function RepoRoot {
  (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
}

function Write-Utf8NoBom([string]$Path, [string]$Content) {
  $dir = Split-Path -Parent $Path
  if ($dir -and !(Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
  $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($Path, $Content, $utf8NoBom)
}

function Write-Rel([string]$Rel, [string]$Content) {
  $full = Join-Path (RepoRoot) $Rel
  Write-Utf8NoBom -Path $full -Content $Content
}

function Patch-ServerGitignore {
  $repo = RepoRoot
  $p = Join-Path $repo "server\.gitignore"
  if (!(Test-Path -LiteralPath $p)) { return }

  $txt = Get-Content -LiteralPath $p -Raw
  $need = @(
    "# documents quarantine p0",
    "data/documents.sqlite",
    "storage/documents/",
    "storage/documents/**"
  )

  foreach ($line in $need) {
    if ($txt -notmatch [regex]::Escape($line)) {
      $txt = $txt.TrimEnd() + "`n" + $line + "`n"
    }
  }

  Write-Utf8NoBom -Path $p -Content $txt
}

function Patch-MainPy {
  $repo = RepoRoot
  $main = Join-Path $repo "server\app\main.py"
  if (!(Test-Path -LiteralPath $main)) { throw "NOT FOUND: $main" }

  $raw = Get-Content -LiteralPath $main -Raw
  $lines = $raw -split "`r?`n"

  # ---- ensure: from app.routers import documents (as separate line)
  $hasDocsImport = $false
  foreach ($ln in $lines) {
    if ($ln -match '^\s*from\s+app\.routers\s+import\s+documents\s*$') { $hasDocsImport = $true; break }
  }

  if (-not $hasDocsImport) {
    # insert after first "from app.routers import ..." block or near top
    $insertAt = -1
    for ($i=0; $i -lt $lines.Length; $i++) {
      if ($lines[$i] -match '^\s*from\s+app\.routers\s+import\s+') {
        # if multiline import with ( ... ), insert after closing ')'
        if ($lines[$i] -match '\(') {
          for ($j=$i+1; $j -lt $lines.Length; $j++) {
            if ($lines[$j] -match '^\s*\)\s*$') { $insertAt = $j + 1; break }
          }
          if ($insertAt -lt 0) { $insertAt = $i + 1 }
        } else {
          $insertAt = $i + 1
        }
        break
      }
    }
    if ($insertAt -lt 0) { $insertAt = 0 }

    $before = @()
    if ($insertAt -gt 0) { $before = $lines[0..($insertAt-1)] }
    $after = @()
    if ($insertAt -le $lines.Length - 1) { $after = $lines[$insertAt..($lines.Length-1)] }
    $lines = $before + "from app.routers import documents" + $after
  }

  # ---- ensure: app.include_router(documents.router) inside create_app
  $hasInclude = $false
  foreach ($ln in $lines) {
    if ($ln -match '^\s*app\.include_router\(\s*documents\.router\s*\)\s*$') { $hasInclude = $true; break }
  }

  if (-not $hasInclude) {
    $createIdx = -1
    for ($i=0; $i -lt $lines.Length; $i++) {
      if ($lines[$i] -match '^\s*def\s+create_app\s*\(') { $createIdx = $i; break }
    }
    if ($createIdx -lt 0) { throw "create_app() not found in server/app/main.py" }

    $returnIdx = -1
    $indent = "    "
    for ($i=$createIdx+1; $i -lt $lines.Length; $i++) {
      if ($lines[$i] -match '^(?<ws>\s+)return\s+app\s*$') {
        $returnIdx = $i
        $indent = $Matches["ws"]
        break
      }
    }
    if ($returnIdx -lt 0) { throw "'return app' not found inside create_app()" }

    # insert before return app (safe, preserves indentation)
    $before = $lines[0..($returnIdx-1)]
    $after  = $lines[$returnIdx..($lines.Length-1)]
    $lines  = $before + ("{0}app.include_router(documents.router)" -f $indent) + $after
  }

  $out = ($lines -join "`n").TrimEnd() + "`n"
  Write-Utf8NoBom -Path $main -Content $out
}

# ----------------- write new module files -----------------

Write-Rel "server/app/models/documents.py" @'
from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field


class DocumentApprovalStatus(str, Enum):
    QUARANTINED = "QUARANTINED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class DocumentScanStatus(str, Enum):
    PENDING = "PENDING"
    CLEAN = "CLEAN"
    INFECTED = "INFECTED"


class DocumentOut(BaseModel):
    id: str = Field(..., min_length=6)
    owner_user_id: str
    filename: str
    content_type: str
    size_bytes: int = Field(..., ge=0)
    approval_status: DocumentApprovalStatus
    scan_status: DocumentScanStatus
    created_at: str  # ISO-8601 (UTC)
'@

Write-Rel "server/app/services/documents_store.py" @'
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

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as con:
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

        with sqlite3.connect(self.db_path) as con:
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

        return self._to_out(rec)

    def get(self, doc_id: str) -> DocumentRecord:
        with sqlite3.connect(self.db_path) as con:
            row = con.execute(
                """
                SELECT id, owner_user_id, filename, content_type, size_bytes,
                       storage_relpath, created_at, approval_status, scan_status
                FROM documents WHERE id = ?
                """,
                (doc_id,),
            ).fetchone()
        if not row:
            raise KeyError("not_found")
        return DocumentRecord(*row)

    def list_quarantine(self) -> list[DocumentOut]:
        with sqlite3.connect(self.db_path) as con:
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
        return [self._to_out(DocumentRecord(*r)) for r in rows]

    def set_scan_status(self, doc_id: str, status: DocumentScanStatus) -> DocumentOut:
        rec = self.get(doc_id)
        approval = rec.approval_status
        if status == DocumentScanStatus.INFECTED:
            approval = DocumentApprovalStatus.REJECTED.value

        with sqlite3.connect(self.db_path) as con:
            con.execute(
                """
                UPDATE documents
                SET scan_status = ?, approval_status = ?
                WHERE id = ?
                """,
                (status.value, approval, doc_id),
            )
            con.commit()

        return self._to_out(self.get(doc_id))

    def approve(self, doc_id: str) -> DocumentOut:
        rec = self.get(doc_id)
        if rec.scan_status != DocumentScanStatus.CLEAN.value:
            raise ValueError("not_scanned_clean")

        with sqlite3.connect(self.db_path) as con:
            con.execute(
                "UPDATE documents SET approval_status = ? WHERE id = ?",
                (DocumentApprovalStatus.APPROVED.value, doc_id),
            )
            con.commit()
        return self._to_out(self.get(doc_id))

    def reject(self, doc_id: str) -> DocumentOut:
        self.get(doc_id)
        with sqlite3.connect(self.db_path) as con:
            con.execute(
                "UPDATE documents SET approval_status = ? WHERE id = ?",
                (DocumentApprovalStatus.REJECTED.value, doc_id),
            )
            con.commit()
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
'@

Write-Rel "server/app/routers/documents.py" @'
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
'@

Write-Rel "server/tests/test_documents_quarantine_p0.py" @'
from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routers import documents as documents_router
from app.services.documents_store import DocumentsStore


def _make_actor(role: str, user_id: str) -> Dict[str, Any]:
    return {"role": role, "user_id": user_id}


def _mk_app(store: DocumentsStore, actor: Dict[str, Any]) -> FastAPI:
    app = FastAPI()
    app.include_router(documents_router.router)
    app.dependency_overrides[documents_router.get_documents_store] = lambda: store
    app.dependency_overrides[documents_router.require_actor] = lambda: actor
    return app


def test_user_cannot_access_admin_quarantine_or_approve_reject():
    with tempfile.TemporaryDirectory() as td:
        store = DocumentsStore(
            storage_root=Path(td) / "storage",
            db_path=Path(td) / "data" / "app.db",
            max_upload_bytes=1024 * 1024,
            allowed_ext={"pdf"},
            allowed_mime={"application/pdf"},
            scan_mode="stub",
        )
        client = TestClient(_mk_app(store, _make_actor("user", "u1")))

        r = client.get("/documents/admin/quarantine")
        assert r.status_code == 403

        # upload ok
        pdf_bytes = b"%PDF-1.4\n% test\n%%EOF\n"
        r = client.post("/documents/upload", files={"file": ("t.pdf", pdf_bytes, "application/pdf")})
        assert r.status_code in (200, 201), r.text
        doc_id = r.json()["id"]

        r = client.post(f"/documents/{doc_id}/approve")
        assert r.status_code == 403

        r = client.post(f"/documents/{doc_id}/reject")
        assert r.status_code == 403


def test_moderator_is_forbidden_everywhere_on_documents():
    with tempfile.TemporaryDirectory() as td:
        store = DocumentsStore(
            storage_root=Path(td) / "storage",
            db_path=Path(td) / "data" / "app.db",
            max_upload_bytes=1024 * 1024,
            allowed_ext={"pdf"},
            allowed_mime={"application/pdf"},
            scan_mode="stub",
        )
        client = TestClient(_mk_app(store, _make_actor("moderator", "m1")))

        r = client.get("/documents/admin/quarantine")
        assert r.status_code == 403, r.text

        r = client.post("/documents/upload", files={"file": ("t.pdf", b"%PDF-1.4\n%%EOF\n", "application/pdf")})
        assert r.status_code == 403, r.text


def test_pending_never_downloadable_for_user_but_downloadable_for_admin_and_then_user_after_approve():
    with tempfile.TemporaryDirectory() as td:
        store = DocumentsStore(
            storage_root=Path(td) / "storage",
            db_path=Path(td) / "data" / "app.db",
            max_upload_bytes=1024 * 1024,
            allowed_ext={"pdf"},
            allowed_mime={"application/pdf"},
            scan_mode="stub",
        )

        user_client = TestClient(_mk_app(store, _make_actor("user", "u1")))
        pdf_bytes = b"%PDF-1.4\n% test\n%%EOF\n"
        r = user_client.post("/documents/upload", files={"file": ("t.pdf", pdf_bytes, "application/pdf")})
        assert r.status_code in (200, 201), r.text
        doc_id = r.json()["id"]
        assert r.json()["approval_status"] == "QUARANTINED"
        assert r.json()["scan_status"] == "PENDING"

        # user cannot download pending
        r = user_client.get(f"/documents/{doc_id}/download")
        assert r.status_code == 403, r.text

        # admin CAN download pending
        admin_client = TestClient(_mk_app(store, _make_actor("admin", "a1")))
        r = admin_client.get(f"/documents/{doc_id}/download")
        assert r.status_code == 200, r.text

        # approve without CLEAN -> 409
        r = admin_client.post(f"/documents/{doc_id}/approve")
        assert r.status_code == 409, r.text

        # scan CLEAN + approve
        r = admin_client.post(f"/documents/{doc_id}/scan", json={"scan_status": "CLEAN"})
        assert r.status_code == 200, r.text

        r = admin_client.post(f"/documents/{doc_id}/approve")
        assert r.status_code == 200, r.text
        assert r.json()["approval_status"] == "APPROVED"

        # user can download now
        r = user_client.get(f"/documents/{doc_id}/download")
        assert r.status_code == 200, r.text
        assert r.content == pdf_bytes


def test_admin_cannot_approve_if_scan_not_clean():
    with tempfile.TemporaryDirectory() as td:
        store = DocumentsStore(
            storage_root=Path(td) / "storage",
            db_path=Path(td) / "data" / "app.db",
            max_upload_bytes=1024 * 1024,
            allowed_ext={"pdf"},
            allowed_mime={"application/pdf"},
            scan_mode="disabled",
        )

        user_client = TestClient(_mk_app(store, _make_actor("user", "u1")))
        admin_client = TestClient(_mk_app(store, _make_actor("admin", "a1")))

        r = user_client.post("/documents/upload", files={"file": ("t.pdf", b"%PDF-1.4\n%%EOF\n", "application/pdf")})
        assert r.status_code in (200, 201), r.text
        doc_id = r.json()["id"]

        r = admin_client.post(f"/documents/{doc_id}/approve")
        assert r.status_code == 409, r.text
        assert r.json()["detail"] == "not_scanned_clean"
'@

Write-Rel "server/tests/test_documents_quarantine_admin_gates.py" @'
from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any, Dict

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.routers import documents as documents_router
from app.services.documents_store import DocumentsStore


def _mk_actor(role: str, user_id: str) -> Dict[str, Any]:
    return {"role": role, "user_id": user_id}


def _make_client(tmp_dir: str, actor: Dict[str, Any]) -> TestClient:
    store = DocumentsStore(
        storage_root=Path(tmp_dir) / "storage",
        db_path=Path(tmp_dir) / "data" / "app.db",
        max_upload_bytes=1024 * 1024,
        allowed_ext={"pdf"},
        allowed_mime={"application/pdf"},
        scan_mode="stub",
    )
    app = FastAPI()
    app.include_router(documents_router.router)
    app.dependency_overrides[documents_router.get_documents_store] = lambda: store
    app.dependency_overrides[documents_router.require_actor] = lambda: actor
    return TestClient(app)


def _upload_quarantine_doc(client: TestClient) -> str:
    pdf_bytes = b"%PDF-1.4\n% test\n%%EOF\n"
    r = client.post("/documents/upload", files={"file": ("test.pdf", pdf_bytes, "application/pdf")})
    assert r.status_code in (200, 201), r.text
    return r.json()["id"]


@pytest.mark.parametrize("role", ["user", "vip", "dealer"])
def test_admin_endpoints_forbidden_for_non_admin_roles(tmp_path, role: str) -> None:
    user_client = _make_client(str(tmp_path), _mk_actor("user", "u_user"))
    doc_id = _upload_quarantine_doc(user_client)

    c = _make_client(str(tmp_path), _mk_actor(role, f"u_{role}"))
    r = c.get("/documents/admin/quarantine")
    assert r.status_code == 403, r.text

    r = c.post(f"/documents/{doc_id}/scan", json={"scan_status": "CLEAN"})
    assert r.status_code == 403, r.text

    r = c.post(f"/documents/{doc_id}/approve")
    assert r.status_code == 403, r.text

    r = c.post(f"/documents/{doc_id}/reject")
    assert r.status_code == 403, r.text


def test_documents_quarantine_moderator_forbidden_everywhere(tmp_path) -> None:
    mod_client = _make_client(str(tmp_path), _mk_actor("moderator", "u_mod"))
    r = mod_client.get("/documents/admin/quarantine")
    assert r.status_code == 403, r.text
    r = mod_client.post("/documents/upload", files={"file": ("x.pdf", b"%PDF-1.4\n%%EOF\n", "application/pdf")})
    assert r.status_code == 403, r.text


def test_admin_can_approve_and_user_can_download_only_after_approved(tmp_path) -> None:
    user_client = _make_client(str(tmp_path), _mk_actor("user", "u_user"))
    doc_id = _upload_quarantine_doc(user_client)

    # user cannot download while quarantined
    r = user_client.get(f"/documents/{doc_id}/download")
    assert r.status_code == 403, r.text

    admin_client = _make_client(str(tmp_path), _mk_actor("admin", "u_admin"))

    # scan CLEAN + approve
    r = admin_client.post(f"/documents/{doc_id}/scan", json={"scan_status": "CLEAN"})
    assert r.status_code == 200, r.text
    r = admin_client.post(f"/documents/{doc_id}/approve")
    assert r.status_code == 200, r.text

    # user can download now
    r = user_client.get(f"/documents/{doc_id}/download")
    assert r.status_code == 200, r.text
'@

Patch-ServerGitignore
Patch-MainPy

Write-Host "OK: documents quarantine P0 v2 applied."