# server/tests/test_documents_quarantine_admin_gates.py
from __future__ import annotations

import os
from importlib import import_module
from typing import Any, Callable, Dict, Optional

import pytest
from fastapi.testclient import TestClient


def _import_attr(candidates: list[str]) -> Any:
    """
    candidates: ["module.sub:attr", ...]
    """
    last_err: Optional[Exception] = None
    for cand in candidates:
        mod_name, attr = cand.split(":", 1)
        try:
            mod = import_module(mod_name)
            return getattr(mod, attr)
        except Exception as e:  # pragma: no cover
            last_err = e
            continue
    raise ImportError(f"Could not import any of: {candidates}") from last_err


# App factory (robust gegen minimale Strukturänderungen)
_create_app = _import_attr(
    [
        "app.main:create_app",
        "server.app.main:create_app",
    ]
)

# Actor dependency (wird in Routern verwendet; Tests überschreiben diese)
_get_actor = _import_attr(
    [
        "app.deps:get_actor",
        "app.auth.deps:get_actor",
        "server.app.deps:get_actor",
        "server.app.auth.deps:get_actor",
    ]
)


def _mk_actor(role: str, user_id: str) -> Dict[str, Any]:
    # Minimales Schema, das in documents.py bereits genutzt wird (admin["user_id"])
    return {"role": role, "user_id": user_id, "email": f"{user_id}@example.com"}


def _make_client(tmp_storage_dir: str, actor: Dict[str, Any]) -> TestClient:
    # Storage isolieren (wenn Settings diese Env Vars nutzen, super; wenn nicht, harmless)
    os.environ.setdefault("LTC_STORAGE_PATH", tmp_storage_dir)
    os.environ.setdefault("LTC_STORAGE_DIR", tmp_storage_dir)

    app = _create_app()
    app.dependency_overrides[_get_actor] = lambda: actor
    return TestClient(app)


def _upload_quarantine_doc(client: TestClient) -> str:
    # Extra Form-Felder sind unschädlich (FastAPI ignoriert unbekannte Keys)
    data = {
        "title": "Test Doc",
        "type": "misc",
        "doc_type": "misc",
        "kind": "misc",
        "servicebook_id": "sb_test",
        "vehicle_id": "veh_test",
        "entry_id": "entry_test",
    }
    pdf_bytes = b"%PDF-1.4\n% test\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF\n"
    files = {"file": ("test.pdf", pdf_bytes, "application/pdf")}

    r = client.post("/documents/upload", data=data, files=files)
    assert r.status_code in (200, 201), r.text
    payload = r.json()

    doc_id = (
        payload.get("doc_id")
        or payload.get("id")
        or payload.get("document_id")
        or payload.get("uuid")
        or payload.get("doc", {}).get("id")
    )
    assert doc_id, f"Upload response missing doc id. payload={payload}"
    return str(doc_id)


@pytest.mark.parametrize("role", ["user", "vip", "dealer"])
def test_documents_quarantine_admin_endpoints_forbidden_for_non_admin_roles(tmp_path, role: str) -> None:
    # Arrange: Dokument erzeugen (Quarantine-by-default)
    user_client = _make_client(str(tmp_path), _mk_actor("user", "u_user"))
    doc_id = _upload_quarantine_doc(user_client)

    # Client mit verbotener Rolle
    forbidden_client = _make_client(str(tmp_path), _mk_actor(role, f"u_{role}"))

    # Act + Assert: Admin-Endpoints müssen 403 liefern
    r1 = forbidden_client.get("/documents/admin/quarantine")
    assert r1.status_code == 403, r1.text

    r2 = forbidden_client.post(f"/documents/{doc_id}/approve")
    assert r2.status_code == 403, r2.text

    r3 = forbidden_client.post(f"/documents/{doc_id}/reject")
    assert r3.status_code == 403, r3.text


def test_documents_quarantine_moderator_forbidden_everywhere(tmp_path) -> None:
    # Moderator ist strikt nur Blog/News → documents muss 403 liefern
    mod_client = _make_client(str(tmp_path), _mk_actor("moderator", "u_mod"))

    r = mod_client.get("/documents/admin/quarantine")
    assert r.status_code == 403, r.text

    # Upload muss ebenfalls verboten sein (router-level forbid_moderator)
    pdf_bytes = b"%PDF-1.4\n% test\n%%EOF\n"
    files = {"file": ("test.pdf", pdf_bytes, "application/pdf")}
    r2 = mod_client.post("/documents/upload", data={"title": "x"}, files=files)
    assert r2.status_code == 403, r2.text


def test_admin_can_approve_and_user_can_download_only_after_approved(tmp_path) -> None:
    # Arrange: user lädt hoch -> quarantined
    user_client = _make_client(str(tmp_path), _mk_actor("user", "u_user"))
    doc_id = _upload_quarantine_doc(user_client)

    # Vor Freigabe: Download muss scheitern (403 oder 404 je nach Implementierung)
    pre = user_client.get(f"/documents/{doc_id}/download")
    assert pre.status_code in (403, 404), pre.text

    # Admin genehmigt
    admin_client = _make_client(str(tmp_path), _mk_actor("admin", "u_admin"))
    ok = admin_client.post(f"/documents/{doc_id}/approve")
    assert ok.status_code in (200, 201), ok.text

    # Nach Freigabe: Download muss 200 sein
    post = user_client.get(f"/documents/{doc_id}/download")
    assert post.status_code == 200, post.text