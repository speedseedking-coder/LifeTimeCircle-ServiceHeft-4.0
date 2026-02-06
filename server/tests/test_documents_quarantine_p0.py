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