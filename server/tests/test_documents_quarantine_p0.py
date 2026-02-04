from __future__ import annotations

import io
import os
import tempfile
from typing import Any, Dict

from fastapi import Depends, FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.routers import documents as documents_router
from app.services.documents_store import DocumentsStore


def _make_actor(role: str, actor_id: str) -> Dict[str, Any]:
    return {"role": role, "id": actor_id}


def _forbid_moderator(actor: Any = Depends(documents_router.require_actor)) -> None:
    role = actor.get("role")
    if role == "moderator":
        raise HTTPException(status_code=403, detail="forbidden")


def _require_actor_factory(actor: Dict[str, Any]):
    def _dep():
        return actor
    return _dep


def _mk_app(store: DocumentsStore, actor: Dict[str, Any]) -> FastAPI:
    app = FastAPI()
    app.include_router(documents_router.router)

    # override store + auth deps
    app.dependency_overrides[documents_router.get_documents_store] = lambda: store
    app.dependency_overrides[documents_router.require_actor] = _require_actor_factory(actor)
    app.dependency_overrides[documents_router.forbid_moderator] = _forbid_moderator
    return app


def _pdf_bytes() -> bytes:
    # minimal header that passes %PDF- sniff
    return b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF\n"


def test_user_cannot_access_admin_quarantine_or_approve_reject():
    with tempfile.TemporaryDirectory() as td:
        store = DocumentsStore(
            storage_root=os.path.join(td, "storage") and __import__("pathlib").Path(td) / "storage",
            db_path=__import__("pathlib").Path(td) / "data" / "app.db",
            max_upload_bytes=1024 * 1024,
            allowed_ext={"pdf"},
            allowed_mime={"application/pdf"},
        )
        actor_user = _make_actor("user", "u1")
        app = _mk_app(store, actor_user)
        client = TestClient(app)

        # upload creates PENDING
        r = client.post(
            "/documents/upload",
            files={"file": ("x.pdf", _pdf_bytes(), "application/pdf")},
        )
        assert r.status_code == 200
        doc_id = r.json()["id"]

        # user forbidden on admin endpoints
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
        )
        actor_mod = _make_actor("moderator", "m1")
        app = _mk_app(store, actor_mod)
        client = TestClient(app)

        r = client.post(
            "/documents/upload",
            files={"file": ("x.pdf", _pdf_bytes(), "application/pdf")},
        )
        assert r.status_code == 403  # forbid_moderator kicks in


def test_pending_never_downloadable_for_user_but_downloadable_for_admin_and_then_user_after_approve():
    with tempfile.TemporaryDirectory() as td:
        store = DocumentsStore(
            storage_root=__import__("pathlib").Path(td) / "storage",
            db_path=__import__("pathlib").Path(td) / "data" / "app.db",
            max_upload_bytes=1024 * 1024,
            allowed_ext={"pdf"},
            allowed_mime={"application/pdf"},
        )

        # user uploads
        actor_user = _make_actor("user", "u1")
        app_user = _mk_app(store, actor_user)
        client_user = TestClient(app_user)

        r = client_user.post(
            "/documents/upload",
            files={"file": ("x.pdf", _pdf_bytes(), "application/pdf")},
        )
        assert r.status_code == 200
        doc_id = r.json()["id"]

        # user cannot download while PENDING
        r = client_user.get(f"/documents/{doc_id}/download")
        assert r.status_code == 403
        assert r.json()["detail"] == "not_approved"

        # admin can review-download while PENDING
        actor_admin = _make_actor("admin", "a1")
        app_admin = _mk_app(store, actor_admin)
        client_admin = TestClient(app_admin)

        r = client_admin.get(f"/documents/{doc_id}/download")
        assert r.status_code == 200
        assert r.headers.get("content-type", "").startswith("application/pdf")

        # approve
        r = client_admin.post(f"/documents/{doc_id}/approve")
        assert r.status_code == 200
        assert r.json()["status"] == "APPROVED"

        # now user can download
        r = client_user.get(f"/documents/{doc_id}/download")
        assert r.status_code == 200
        assert r.headers.get("content-type", "").startswith("application/pdf")