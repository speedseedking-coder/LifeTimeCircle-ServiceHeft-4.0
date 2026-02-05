# FILE: server/tests/test_documents_quarantine_workflow.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest
from fastapi import Header
from fastapi.testclient import TestClient

from app import deps as app_deps
from app.routers import documents as documents_router
from app.services.documents_store import DocumentsStore


@dataclass
class Actor:
    uid: str
    role: str


@pytest.fixture()
def client(tmp_path: Path):
    from app.main import create_app  # import lokal, damit conftest/create_app kompatibel bleibt

    app = create_app()

    store = DocumentsStore(
        storage_root=tmp_path / "storage",
        db_path=tmp_path / "data" / "app.db",
        max_upload_bytes=10 * 1024 * 1024,
        allowed_ext={"pdf"},
        allowed_mime={"application/pdf"},
        scan_mode="stub",
    )

    def override_store():
        return store

    def override_actor_headers(
        x_user_id: str = Header("u1", alias="X-User-Id"),
        x_role: str = Header("user", alias="X-Role"),
    ):
        return Actor(uid=x_user_id, role=x_role)

    app.dependency_overrides[documents_router.get_documents_store] = override_store
    app.dependency_overrides[app_deps.get_actor] = override_actor_headers

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


def test_quarantine_default_and_admin_workflow(client: TestClient):
    pdf_bytes = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\n%%EOF\n"

    r = client.post(
        "/documents/upload",
        headers={"X-User-Id": "u1", "X-Role": "user"},
        files={"file": ("a.pdf", pdf_bytes, "application/pdf")},
    )
    assert r.status_code == 200
    doc = r.json()
    assert doc["approval_status"] == "QUARANTINED"
    assert doc["scan_status"] == "PENDING"
    doc_id = doc["id"]

    r = client.get(
        f"/documents/{doc_id}/download",
        headers={"X-User-Id": "u1", "X-Role": "user"},
    )
    assert r.status_code == 403

    r = client.get(
        "/documents/admin/quarantine",
        headers={"X-User-Id": "u1", "X-Role": "user"},
    )
    assert r.status_code == 403

    r = client.post(
        f"/documents/{doc_id}/approve",
        headers={"X-User-Id": "a1", "X-Role": "admin"},
    )
    assert r.status_code == 409
    assert r.json()["detail"] == "not_scanned_clean"

    r = client.post(
        f"/documents/{doc_id}/scan",
        headers={"X-User-Id": "a1", "X-Role": "admin"},
        json={"scan_status": "CLEAN"},
    )
    assert r.status_code == 200
    assert r.json()["scan_status"] == "CLEAN"
    assert r.json()["approval_status"] == "QUARANTINED"

    r = client.post(
        f"/documents/{doc_id}/approve",
        headers={"X-User-Id": "a1", "X-Role": "admin"},
    )
    assert r.status_code == 200
    assert r.json()["approval_status"] == "APPROVED"

    r = client.get(
        f"/documents/{doc_id}/download",
        headers={"X-User-Id": "u1", "X-Role": "user"},
    )
    assert r.status_code == 200
    assert r.content == pdf_bytes

    r = client.get(
        f"/documents/{doc_id}/download",
        headers={"X-User-Id": "u2", "X-Role": "user"},
    )
    assert r.status_code == 403


def test_infected_forces_reject_and_blocks_approve(client: TestClient):
    r = client.post(
        "/documents/upload",
        headers={"X-User-Id": "u1", "X-Role": "user"},
        files={"file": ("b.pdf", b"%PDF-1.4\n%%EOF\n", "application/pdf")},
    )
    assert r.status_code == 200
    doc_id = r.json()["id"]

    r = client.post(
        f"/documents/{doc_id}/scan",
        headers={"X-User-Id": "a1", "X-Role": "admin"},
        json={"scan_status": "INFECTED"},
    )
    assert r.status_code == 200
    assert r.json()["scan_status"] == "INFECTED"
    assert r.json()["approval_status"] == "REJECTED"

    r = client.post(
        f"/documents/{doc_id}/approve",
        headers={"X-User-Id": "a1", "X-Role": "admin"},
    )
    assert r.status_code == 409


def test_moderator_is_blocked_everywhere_on_documents(client: TestClient):
    r = client.post(
        "/documents/upload",
        headers={"X-User-Id": "m1", "X-Role": "moderator"},
        files={"file": ("x.pdf", b"%PDF-1.4\n%%EOF\n", "application/pdf")},
    )
    assert r.status_code == 403

    r = client.get(
        "/documents/admin/quarantine",
        headers={"X-User-Id": "m1", "X-Role": "moderator"},
    )
    assert r.status_code == 403