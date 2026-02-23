# server/tests/test_export_vehicle_p0.py
from __future__ import annotations

import os
import secrets
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, Iterator

import pytest
from sqlalchemy import MetaData, Table, insert, select
from sqlalchemy.orm import Session
from starlette.requests import Request

from app.routers import export_vehicle as ev

os.environ.setdefault("LTC_SECRET_KEY", "test_secret_key__0123456789abcdef")


def _reflect_vehicles_table(db: Session) -> Table:
    md = MetaData()
    for name in ("vehicles", "vehicle"):
        try:
            return Table(name, md, autoload_with=db.get_bind())
        except Exception:
            continue
    raise RuntimeError("vehicles table not found (vehicles|vehicle)")


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


def _insert_vehicle_for_owner(client, owner_uid: str) -> str:
    public_id = f"veh_{secrets.token_hex(6)}"

    with _db_from_client(client) as db:
        tbl = _reflect_vehicles_table(db)

        values: Dict[str, Any] = {}
        if "public_id" in tbl.c:
            values["public_id"] = public_id
        if "owner_user_id" in tbl.c:
            values["owner_user_id"] = owner_uid

        if "vin_prefix3" in tbl.c:
            values["vin_prefix3"] = "WVW"
        if "vin_last4" in tbl.c:
            values["vin_last4"] = "1234"

        # created_at/updated_at nur wenn zwingend (datetime-Objekte!)
        now = datetime.utcnow()
        if "created_at" in tbl.c:
            col = tbl.c.created_at
            if (not getattr(col, "nullable", True)) and col.default is None and col.server_default is None:
                values["created_at"] = now
        if "updated_at" in tbl.c:
            col = tbl.c.updated_at
            if (not getattr(col, "nullable", True)) and col.default is None and col.server_default is None:
                values["updated_at"] = now

        db.execute(insert(tbl).values(**values))
        db.commit()

        if "public_id" in tbl.c:
            row = db.execute(select(tbl.c.public_id).where(tbl.c.public_id == public_id)).first()
            assert row is not None

    return public_id


def test_export_vehicle_redacted_owner_ok_other_forbidden(client, make_user_headers):
    owner_headers = make_user_headers(role="user")
    other_headers = make_user_headers(role="user")

    vid = _insert_vehicle_for_owner(client, owner_uid=owner_headers["X-LTC-UID"])

    r_ok = client.get(f"/export/vehicle/{vid}", headers=owner_headers)
    assert r_ok.status_code == 200, r_ok.text

    r_forbid = client.get(f"/export/vehicle/{vid}", headers=other_headers)
    assert r_forbid.status_code == 403, r_forbid.text


def test_export_vehicle_redacted_moderator_forbidden(client, make_user_headers):
    owner_headers = make_user_headers(role="user")
    mod_headers = make_user_headers(role="moderator")

    vid = _insert_vehicle_for_owner(client, owner_uid=owner_headers["X-LTC-UID"])

    r_mod = client.get(f"/export/vehicle/{vid}", headers=mod_headers)
    assert r_mod.status_code == 403, r_mod.text


def test_export_vehicle_full_grant_and_full_encrypted_one_time(client, make_user_headers):
    owner_headers = make_user_headers(role="user")
    sa_headers = make_user_headers(role="superadmin")

    vid = _insert_vehicle_for_owner(client, owner_uid=owner_headers["X-LTC-UID"])

    r_user_grant = client.post(f"/export/vehicle/{vid}/grant", headers=owner_headers)
    assert r_user_grant.status_code == 403, r_user_grant.text

    r_grant = client.post(f"/export/vehicle/{vid}/grant", headers=sa_headers)
    assert r_grant.status_code == 200, r_grant.text
    token = r_grant.json().get("token")
    assert isinstance(token, str) and len(token) > 10

    r_full = client.get(f"/export/vehicle/{vid}/full", headers={**sa_headers, "X-Export-Token": token})
    assert r_full.status_code == 200, r_full.text
    assert isinstance(r_full.json().get("ciphertext"), str) and len(r_full.json()["ciphertext"]) > 20

    r_full_again = client.get(f"/export/vehicle/{vid}/full", headers={**sa_headers, "X-Export-Token": token})
    assert r_full_again.status_code == 403, r_full_again.text