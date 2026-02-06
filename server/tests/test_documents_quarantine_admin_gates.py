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