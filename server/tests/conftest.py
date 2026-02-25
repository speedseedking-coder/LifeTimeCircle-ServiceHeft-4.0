import os

# LTC_TEST_SECRET_KEY_IMPORTTIME

# Minimal deterministic test secret (>=16 chars) – test-only
os.environ["LTC_SECRET_KEY"] = os.environ.get("LTC_SECRET_KEY") or "test-secret-key-1234567890"

# Ensure settings read the env (cache clear if present)
try:
    from app.settings import get_settings  # type: ignore
    if hasattr(get_settings, "cache_clear"):
        get_settings.cache_clear()
except Exception:
    try:
        from app.core.settings import get_settings  # type: ignore
        if hasattr(get_settings, "cache_clear"):
            get_settings.cache_clear()
    except Exception:
        pass
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Stelle sicher, dass "server/" im sys.path ist (damit "import app" immer funktioniert)
SERVER_ROOT = Path(__file__).resolve().parents[1]
if str(SERVER_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVER_ROOT))



from app.main import create_app  # noqa: E402


@pytest.fixture()
def client():
    app = create_app()
    with TestClient(app) as c:
        yield c

# --- LTC: make_vehicle_for_owner (servicebook_entries using TEST DB via dependency override) ---
import pytest
# --- LTC: make_vehicle_for_owner (API based, no ORM import) ---
import pytest
# --- LTC: make_vehicle_for_owner (servicebook_entries using TEST DB via dependency override) ---
import pytest
# --- LTC: make_vehicle_for_owner (servicebook_entries via DB reflection) ---
import pytest
# --- LTC: make_vehicle_for_owner (servicebook_entries using TEST DB via dependency override) ---
import pytest
# --- LTC: make_vehicle_for_owner (servicebook_entries using TEST DB via dependency override) ---
import pytest
# --- LTC: make_vehicle_for_owner (servicebook_entries using TEST DB via dependency override) ---
import pytest
@pytest.fixture()
def make_vehicle_for_owner(client):
    import uuid
    from datetime import datetime, timezone
    from sqlalchemy import MetaData, Table, insert, inspect, text
    from app.db.session import get_db as get_db_prod

    def _mk(owner_headers: dict):
        oh = {str(k).lower(): v for k, v in dict(owner_headers).items()}
        uid = oh.get("x-ltc-uid")
        if not uid: raise RuntimeError("test headers missing X-LTC-UID")
        get_db = client.app.dependency_overrides.get(get_db_prod, get_db_prod)
        db_gen = get_db()
        db = next(db_gen)

        try:
            bind = db.get_bind()
            insp = inspect(bind)

            if "servicebook_entries" not in insp.get_table_names():
                if bind.dialect.name != "sqlite":
                    raise RuntimeError("servicebook_entries missing in test DB; run migrations/create_all for tests.")

                db.execute(text("""
                    CREATE TABLE servicebook_entries (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        servicebook_id TEXT NOT NULL,
                        owner_id TEXT NULL,
                        actor_role TEXT NULL,
                        entry_type TEXT NULL,
                        source TEXT NULL,
                        result_status TEXT NULL,
                        title TEXT NULL,
                        summary TEXT NULL,
                        details TEXT NULL,
                        occurred_at TEXT NULL,
                        km INTEGER NULL,
                        document_ids TEXT NULL,
                        created_at TEXT NULL,
                        updated_at TEXT NULL
                    )
                """))
                db.commit()

            md = MetaData()
            t = Table("servicebook_entries", md, autoload_with=bind)
            cols = {c.name for c in t.columns}

            now = datetime.now(timezone.utc).isoformat()
            servicebook_id = str(uuid.uuid4())
            vehicle_id = servicebook_id

            data = {"servicebook_id": servicebook_id}

            if "owner_id" in cols:
                data["owner_id"] = uid
            if "actor_role" in cols:
                data["actor_role"] = oh.get("x-ltc-role") or "user"

            for k, v in (
                ("entry_type", "test"),
                ("source", "test"),
                ("result_status", "ok"),
                ("title", "Test Entry"),
                ("summary", "Test"),
                ("details", "Test"),
            ):
                if k in cols:
                    data[k] = v

            if "occurred_at" in cols:
                data["occurred_at"] = now
            if "km" in cols:
                data["km"] = 0
            if "document_ids" in cols:
                data["document_ids"] = "[]"
            if "created_at" in cols:
                data["created_at"] = now
            if "updated_at" in cols:
                data["updated_at"] = now

            db.execute(insert(t).values(**data))
            db.commit()
            return vehicle_id

        finally:
            try:
                next(db_gen)
            except StopIteration:
                pass

    return _mk
# --- /LTC make_vehicle_for_owner ---

# --- LTC: make_user_headers (simple user header factory) ---
@pytest.fixture()
def make_user_headers():
    def _mk(uid: str | None = None, role: str = "user", **_kw):
        import uuid
        if uid is None:
            uid = str(uuid.uuid4())
        h = {"X-LTC-UID": uid}
        if role is not None:
            h["X-LTC-ROLE"] = role
        return h
    return _mk
# --- /LTC make_user_headers ---







import pytest

# LTC_TEST_SECRET_KEY_AUTOUSE
# Tests erwarten einen gültigen Secret-Key (>= 16 chars) für One-Time-Token Exporte.
# In Prod MUSS das aus Env/Secrets kommen – hier nur für Tests.
@pytest.fixture(autouse=True, scope="session")
def _ltc_test_secret_key() -> None:
    key = "test_secret_key__0123456789abcdef"
    os.environ.setdefault("LTC_SECRET_KEY", key)
    # optional Fallbacks, falls Settings andere Env-Namen akzeptieren:
    os.environ.setdefault("SECRET_KEY", key)
    os.environ.setdefault("APP_SECRET_KEY", key)
