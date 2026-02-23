from __future__ import annotations

import secrets
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterator

from sqlalchemy import DateTime as SA_DateTime, MetaData, Table, insert, select, text, update
from sqlalchemy.orm import Session
from starlette.requests import Request

from app.routers import export_vehicle as ev


def _fake_request_for_app(app) -> Request:
    scope = {
        "type": "http",
        "asgi": {"spec_version": "2.3", "version": "3.0"},
        "method": "GET",
        "path": "/",
        "raw_path": b"/",
        "query_string": b"",
        "headers": [],
        "client": ("testclient", 0),
        "server": ("testserver", 80),
        "scheme": "http",
        "app": app,
    }
    return Request(scope)


@contextmanager
def _db_from_client(client) -> Iterator[Session]:
    req = _fake_request_for_app(client.app)
    gen = ev.get_db(req)
    db = next(gen)
    try:
        yield db
    finally:
        try:
            gen.close()
        except Exception:
            pass


def _ensure_servicebook_table(db: Session) -> Table:
    engine = db.get_bind()
    md = MetaData()
    for name in ("servicebook_entries", "servicebook_entry"):
        try:
            return Table(name, md, autoload_with=engine)
        except Exception:
            continue

    db.execute(
        text(
            """
            CREATE TABLE servicebook_entries (
                id TEXT PRIMARY KEY,
                servicebook_id TEXT NOT NULL,
                owner_id TEXT NULL,
                vin TEXT NULL,
                owner_email TEXT NULL,
                notes TEXT NULL,
                created_at TEXT NULL
            )
            """
        )
    )
    db.commit()
    return Table("servicebook_entries", MetaData(), autoload_with=engine)


def _insert_servicebook_for_owner(client, owner_uid: str) -> str:
    sbid = f"sb_{secrets.token_hex(6)}"
    with _db_from_client(client) as db:
        tbl = _ensure_servicebook_table(db)
        values: Dict[str, Any] = {
            "id": f"e_{secrets.token_hex(4)}",
            "servicebook_id": sbid,
            "owner_id": owner_uid,
            "vin": "WVWTESTVIN1234567",
            "owner_email": "owner@example.org",
            "notes": "top-secret",
        }
        if "created_at" in tbl.c:
            col = tbl.c.created_at
            now = datetime.now(timezone.utc)
            values["created_at"] = now if isinstance(getattr(col, "type", None), SA_DateTime) else now.isoformat()
        cols = {c.name for c in tbl.columns}
        values = {k: v for k, v in values.items() if k in cols}
        db.execute(insert(tbl).values(**values))
        db.commit()
    return sbid


def test_export_servicebook_p0_redacted_no_leaks_and_hmac(client, make_user_headers):
    owner_headers = make_user_headers(role="user")
    sbid = _insert_servicebook_for_owner(client, owner_headers["X-LTC-UID"])

    r = client.get(f"/export/servicebook/{sbid}", headers=owner_headers)
    assert r.status_code == 200, r.text
    body = r.json()

    assert "data" in body
    assert body["data"]["_redacted"] is True
    assert body["data"]["target"] == "servicebook"
    assert "servicebook_id_hmac" in body["data"]["servicebook"]

    body_text = r.text.lower()
    assert "wvwtestvin1234567" not in body_text
    assert "owner@example.org" not in body_text


def test_export_servicebook_p0_grant_persist_full_one_time_ttl_and_moderator_403(client, make_user_headers):
    owner_headers = make_user_headers(role="user")
    sa_headers = make_user_headers(role="superadmin")
    mod_headers = make_user_headers(role="moderator")
    sbid = _insert_servicebook_for_owner(client, owner_headers["X-LTC-UID"])

    r_mod_redacted = client.get(f"/export/servicebook/{sbid}", headers=mod_headers)
    assert r_mod_redacted.status_code == 403
    r_mod_grant = client.post(f"/export/servicebook/{sbid}/grant", headers=mod_headers)
    assert r_mod_grant.status_code == 403
    r_mod_full = client.get(f"/export/servicebook/{sbid}/full", headers=mod_headers)
    assert r_mod_full.status_code == 403

    r_no_token = client.get(f"/export/servicebook/{sbid}/full", headers=sa_headers)
    assert r_no_token.status_code == 400

    r_invalid = client.get(f"/export/servicebook/{sbid}/full", headers={**sa_headers, "X-Export-Token": "invalid"})
    assert r_invalid.status_code == 403

    r_grant = client.post(f"/export/servicebook/{sbid}/grant", headers=sa_headers)
    assert r_grant.status_code == 200, r_grant.text
    token = r_grant.json().get("token")
    assert isinstance(token, str) and len(token) > 10

    with _db_from_client(client) as db:
        grants = Table("export_grants_servicebook", MetaData(), autoload_with=db.get_bind())
        rows = db.execute(select(grants).where(grants.c.servicebook_id == sbid)).mappings().all()
        assert len(rows) == 1
        assert rows[0]["export_token"] == token

    r_full = client.get(f"/export/servicebook/{sbid}/full", headers={**sa_headers, "X-Export-Token": token})
    assert r_full.status_code == 200, r_full.text
    assert isinstance(r_full.json().get("ciphertext"), str) and len(r_full.json()["ciphertext"]) > 20

    r_full_again = client.get(f"/export/servicebook/{sbid}/full", headers={**sa_headers, "X-Export-Token": token})
    assert r_full_again.status_code == 403

    r_grant_exp = client.post(f"/export/servicebook/{sbid}/grant", headers=sa_headers)
    exp_token = r_grant_exp.json()["token"]

    with _db_from_client(client) as db:
        grants = Table("export_grants_servicebook", MetaData(), autoload_with=db.get_bind())
        row = db.execute(select(grants).where(grants.c.export_token == exp_token)).mappings().first()
        assert row is not None
        past = datetime.now(timezone.utc) - timedelta(seconds=5)
        db.execute(update(grants).where(grants.c.id == row["id"]).values(expires_at=past))
        db.commit()

    r_expired = client.get(f"/export/servicebook/{sbid}/full", headers={**sa_headers, "X-Export-Token": exp_token})
    assert r_expired.status_code == 403