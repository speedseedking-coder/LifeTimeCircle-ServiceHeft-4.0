from __future__ import annotations

import tempfile
from typing import Any, Dict

from fastapi import Depends, FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.routers import documents as documents_router
from app.services.documents_store import DocumentsStore


def _make_actor(role: str, actor_id: str) -> Dict[str, Any]:
    return {"role": role, "id": actor_id}


def _require_user_factory(actor: Dict[str, Any]):
    def _dep():
        return actor

    return _dep


def _pdf_bytes() -> bytes:
    return b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF\n"


def _mk_app(store: DocumentsStore, actor: Dict[str, Any]) -> FastAPI:
    app = FastAPI()
    app.include_router(documents_router.router)

    # override store + auth deps
    app.dependency_overrides[documents_router.get_documents_store] = lambda: store
    app.dependency_overrides[documents_router.get_current_user] = _require_user_factory(actor)
    return app


def test_user_cannot_access_admin_quarantine_or_approve_reject():
    with tempfile.TemporaryDirectory() as td:
        store = DocumentsStore(
            storage_root=__import__("pathlib").Path(td) / "storage",
            db_path=__import__("pathlib").Path(td) / "data" / "app.db",
            max_upload_bytes=1024 * 1024,
            allowed_ext={"pdf"},
            allowed_mime={"application/pdf"},
            scan_mode="stub",
        )
        client = TestClient(_mk_app(store, _make_actor("user", "u1")))

        r = client.post("/documents/upload", files={"file": ("x.pdf", _pdf_bytes(), "application/pdf")})
        assert r.status_code == 200
        doc_id = r.json()["id"]

        r = client.get("/documents/admin/quarantine")
        assert r.status_code == 403

        r = client.post(f"/documents/{doc_id}/approve")
        assert r.status_code == 403

        r = client.post(f"/documents/{doc_id}/reject", params={"reason": "nope"})
        assert r.status_code == 403


def test_moderator_is_forbidden_everywhere_on_documents():
    with tempfile.TemporaryDirectory() as td:
        store = DocumentsStore(
            storage_root=__import__("pathlib").Path(td) / "storage",
            db_path=__import__("pathlib").Path(td) / "data" / "app.db",
            max_upload_bytes=1024 * 1024,
            allowed_ext={"pdf"},
            allowed_mime={"application/pdf"},
            scan_mode="stub",
        )
        client = TestClient(_mk_app(store, _make_actor("moderator", "m1")))

        r = client.post("/documents/upload", files={"file": ("x.pdf", _pdf_bytes(), "application/pdf")})
        assert r.status_code == 403


def test_pending_never_downloadable_for_user_but_downloadable_for_admin_and_then_user_after_approve():
    with tempfile.TemporaryDirectory() as td:
        store = DocumentsStore(
            storage_root=__import__("pathlib").Path(td) / "storage",
            db_path=__import__("pathlib").Path(td) / "data" / "app.db",
            max_upload_bytes=1024 * 1024,
            allowed_ext={"pdf"},
            allowed_mime={"application/pdf"},
            scan_mode="stub",
        )

        user_client = TestClient(_mk_app(store, _make_actor("user", "u1")))
        r = user_client.post("/documents/upload", files={"file": ("x.pdf", _pdf_bytes(), "application/pdf")})
        assert r.status_code == 200
        doc_id = r.json()["id"]

        r = user_client.get(f"/documents/{doc_id}/download")
        assert r.status_code == 403
        assert r.json()["detail"] == "not_approved"

        admin_client = TestClient(_mk_app(store, _make_actor("admin", "a1")))

        # admin can review-download while pending
        r = admin_client.get(f"/documents/{doc_id}/download")
        assert r.status_code == 200
        assert r.headers.get("content-type", "").startswith("application/pdf")

        # approve allowed because scan_mode=stub => CLEAN
        r = admin_client.post(f"/documents/{doc_id}/approve")
        assert r.status_code == 200
        assert r.json()["status"] == "APPROVED"

        r = user_client.get(f"/documents/{doc_id}/download")
        assert r.status_code == 200
        assert r.headers.get("content-type", "").startswith("application/pdf")


def test_admin_cannot_approve_if_scan_not_clean():
    with tempfile.TemporaryDirectory() as td:
        store = DocumentsStore(
            storage_root=__import__("pathlib").Path(td) / "storage",
            db_path=__import__("pathlib").Path(td) / "data" / "app.db",
            max_upload_bytes=1024 * 1024,
            allowed_ext={"pdf"},
            allowed_mime={"application/pdf"},
            scan_mode="disabled",  # => scan_status stays PENDING
        )

        user_client = TestClient(_mk_app(store, _make_actor("user", "u1")))
        r = user_client.post("/documents/upload", files={"file": ("x.pdf", _pdf_bytes(), "application/pdf")})
        assert r.status_code == 200
        doc_id = r.json()["id"]

        admin_client = TestClient(_mk_app(store, _make_actor("admin", "a1")))
        r = admin_client.post(f"/documents/{doc_id}/approve")
        assert r.status_code == 409
        assert r.json()["detail"] == "not_scanned_clean"