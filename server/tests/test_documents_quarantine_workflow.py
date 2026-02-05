# FILE: server/tests/test_documents_quarantine_workflow.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.routers import documents as documents_router
from app.services.documents_store import DocumentsStore


@dataclass
class Actor:
    user_id: str
    role: str


@pytest.fixture()
def client(tmp_path: Path):
    store = DocumentsStore(
        storage_root=tmp_path / "storage",
        db_path=tmp_path / "data" / "documents.sqlite",
        max_upload_bytes=10 * 1024 * 1024,
        scan_mode="stub",
    )

    def override_store():
        return store

    # Header-basierter Actor für Tests (unabhängig vom echten Auth-Mechanismus)
    def override_actor(x_user_id: str = "u1", x_role: str = "user"):
        return Actor(user_id=x_user_id, role=x_role)

    # Für FastAPI: Header Injection via call signature (TestClient setzt headers)
    from fastapi import Header

    def override_actor_headers(
        x_user_id: str = Header("u1", alias="X-User-Id"),
        x_role: str = Header("user", alias="X-Role"),
    ):
        return Actor(user_id=x_user_id, role=x_role)

    app.dependency_overrides[documents_router.get_documents_store] = override_store
    app.dependency_overrides[documents_router.require_actor] = override_actor_headers

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


def test_quarantine_default_and_admin_workflow(client: TestClient):
    # user upload -> QUARANTINED + PENDING
    r = client.post(
        "/documents/upload",
        headers={"X-User-Id": "u1", "X-Role": "user"},
        files={"file": ("a.txt", b"hello", "text/plain")},
    )
    assert r.status_code == 200
    doc = r.json()
    assert doc["approval_status"] == "QUARANTINED"
    assert doc["scan_status"] == "PENDING"
    doc_id = doc["id"]

    # user cannot download while quarantined
    r = client.get(
        f"/documents/{doc_id}/download",
        headers={"X-User-Id": "u1", "X-Role": "user"},
    )
    assert r.status_code == 403

    # non-admin cannot see quarantine list
    r = client.get(
        "/documents/admin/quarantine",
        headers={"X-User-Id": "u1", "X-Role": "user"},
    )
    assert r.status_code == 403

    # admin cannot approve before CLEAN
    r = client.post(
        f"/documents/{doc_id}/approve",
        headers={"X-User-Id": "a1", "X-Role": "admin"},
    )
    assert r.status_code == 409
    assert r.json()["detail"] == "not_scanned_clean"

    # admin sets scan CLEAN
    r = client.post(
        f"/documents/{doc_id}/scan",
        headers={"X-User-Id": "a1", "X-Role": "admin"},
        json={"scan_status": "CLEAN"},
    )
    assert r.status_code == 200
    assert r.json()["scan_status"] == "CLEAN"
    assert r.json()["approval_status"] == "QUARANTINED"

    # admin approves
    r = client.post(
        f"/documents/{doc_id}/approve",
        headers={"X-User-Id": "a1", "X-Role": "admin"},
    )
    assert r.status_code == 200
    assert r.json()["approval_status"] == "APPROVED"

    # owner can download after approval
    r = client.get(
        f"/documents/{doc_id}/download",
        headers={"X-User-Id": "u1", "X-Role": "user"},
    )
    assert r.status_code == 200
    assert r.content == b"hello"

    # other user cannot download
    r = client.get(
        f"/documents/{doc_id}/download",
        headers={"X-User-Id": "u2", "X-Role": "user"},
    )
    assert r.status_code == 403


def test_infected_forces_reject_and_blocks_approve(client: TestClient):
    r = client.post(
        "/documents/upload",
        headers={"X-User-Id": "u1", "X-Role": "user"},
        files={"file": ("b.bin", b"x", "application/octet-stream")},
    )
    assert r.status_code == 200
    doc_id = r.json()["id"]

    # admin marks INFECTED => REJECTED
    r = client.post(
        f"/documents/{doc_id}/scan",
        headers={"X-User-Id": "a1", "X-Role": "admin"},
        json={"scan_status": "INFECTED"},
    )
    assert r.status_code == 200
    assert r.json()["scan_status"] == "INFECTED"
    assert r.json()["approval_status"] == "REJECTED"

    # approve still blocked
    r = client.post(
        f"/documents/{doc_id}/approve",
        headers={"X-User-Id": "a1", "X-Role": "admin"},
    )
    assert r.status_code == 409


def test_moderator_is_blocked_everywhere_on_documents(client: TestClient):
    r = client.post(
        "/documents/upload",
        headers={"X-User-Id": "m1", "X-Role": "moderator"},
        files={"file": ("x.txt", b"x", "text/plain")},
    )
    assert r.status_code == 403

    r = client.get(
        "/documents/admin/quarantine",
        headers={"X-User-Id": "m1", "X-Role": "moderator"},
    )
    assert r.status_code == 403