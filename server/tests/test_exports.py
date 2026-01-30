import os
from typing import Optional, Any

import pytest
from fastapi.testclient import TestClient

# ------------------------------------------------------------
# TEST ENV: deterministisch vor allen App-Imports setzen
# ------------------------------------------------------------
os.environ["LTC_SECRET_KEY"] = "test-secret-key-32chars-minimum-aaaaaaaa"
os.environ["LTC_ENV"] = "dev"

from app.core.config import get_settings  # noqa: E402
from app.main import create_app  # noqa: E402


def _cache_clear(obj: Any) -> None:
    """
    get_settings() ist i.d.R. @lru_cache. In Tests wollen wir deterministisch sein.
    """
    try:
        obj.cache_clear()  # type: ignore[attr-defined]
    except Exception:
        pass


def _make_access_token(role: str, sub: str = "test-user", org_id: Optional[str] = "test-org") -> str:
    """
    Token exakt kompatibel zu app.core.security erzeugen.
    Wichtig:
    - org_id gesetzt (falls Guard darauf besteht)
    - jwt.encode kann bytes liefern -> immer zu str normalisieren
    """
    settings = get_settings()

    # Import hier drin, damit wir keine Lib-Mismatch-Effekte bekommen
    import jwt  # type: ignore

    tok = jwt.encode(
        {"sub": sub, "role": role, "org_id": org_id},
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )

    if isinstance(tok, bytes):
        tok = tok.decode("utf-8")
    return str(tok)


@pytest.fixture()
def api_client() -> TestClient:
    # Settings-Cache leeren, damit Secret/Algo konsistent sind
    _cache_clear(get_settings)
    app = create_app()
    return TestClient(app)


def test_export_redacted_rbac(api_client: TestClient):
    # no auth -> 401/403 (je nach Guard)
    r0 = api_client.get("/export/masterclipboard/does-not-exist")
    assert r0.status_code in (401, 403)

    # moderator -> 403 (RBAC deny)
    mod_token = _make_access_token("moderator")
    r1 = api_client.get(
        "/export/masterclipboard/does-not-exist",
        headers={"Authorization": f"Bearer {mod_token}"},
    )
    assert r1.status_code == 403

    # dealer -> darf nicht 401/403 sein (404 ok)
    dealer_token = _make_access_token("dealer")
    r2 = api_client.get(
        "/export/masterclipboard/does-not-exist",
        headers={"Authorization": f"Bearer {dealer_token}"},
    )
    assert r2.status_code not in (401, 403)


def test_full_export_requires_token_and_consumes_once(api_client: TestClient):
    super_token = _make_access_token("superadmin")

    # ohne X-Export-Token -> 400 (Auth muss vorher ok sein)
    r0 = api_client.get(
        "/export/masterclipboard/does-not-exist/full",
        headers={"Authorization": f"Bearer {super_token}"},
    )
    assert r0.status_code == 400

    # Grant erzeugen
    g = api_client.post(
        "/export/masterclipboard/does-not-exist/grant",
        headers={"Authorization": f"Bearer {super_token}"},
        params={"ttl_seconds": 300},
    )
    assert g.status_code == 200
    export_token = g.json().get("export_token")
    assert export_token

    # 1st call: darf nicht 401/403/400 sein (404 oder 501 oder 200 sind ok)
    r1 = api_client.get(
        "/export/masterclipboard/does-not-exist/full",
        headers={
            "Authorization": f"Bearer {super_token}",
            "X-Export-Token": export_token,
        },
    )
    assert r1.status_code not in (401, 403, 400, 422)

    # 2nd call: Token ist one-time -> 409
    r2 = api_client.get(
        "/export/masterclipboard/does-not-exist/full",
        headers={
            "Authorization": f"Bearer {super_token}",
            "X-Export-Token": export_token,
        },
    )
    assert r2.status_code == 409


def test_grant_is_superadmin_only(api_client: TestClient):
    admin_token = _make_access_token("admin")
    r = api_client.post(
        "/export/masterclipboard/does-not-exist/grant",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    # require_roles("superadmin") -> 403
    assert r.status_code == 403
