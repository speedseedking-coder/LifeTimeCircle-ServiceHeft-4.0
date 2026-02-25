Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::UTF8

function Get-RepoRoot {
  $root = (git rev-parse --show-toplevel).Trim()
  if (-not $root) { throw "Repo-Root nicht gefunden (git rev-parse --show-toplevel leer)." }
  return $root
}

$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)

function Read-Utf8NoBom([string]$path) {
  if (-not (Test-Path -LiteralPath $path)) { throw "Missing: $path" }
  return [System.IO.File]::ReadAllText($path, $Utf8NoBom)
}

function Write-Utf8NoBom([string]$path, [string]$text) {
  $dir = Split-Path -Parent $path
  if ($dir -and -not (Test-Path -LiteralPath $dir)) { New-Item -ItemType Directory -Path $dir | Out-Null }
  [System.IO.File]::WriteAllText($path, $text, $Utf8NoBom)
}

function Ensure-Line([string]$text, [string]$needle, [string]$insertAfterPattern) {
  if ($text -match [regex]::Escape($needle)) { return $text }
  $m = [regex]::Match($text, $insertAfterPattern, [System.Text.RegularExpressions.RegexOptions]::Multiline)
  if (-not $m.Success) { return ($text.TrimEnd() + "`n" + $needle + "`n") }
  $idx = $m.Index + $m.Length
  return $text.Substring(0, $idx) + "`n" + $needle + $text.Substring($idx)
}

function Clean-ControlChars([string]$text) {
  # gezielt: VT(0x0B)->'v' und FF(0x0C)->'f' (weil bei dir genau diese Buchstaben “kaputt” waren)
  $text = $text -replace [char]0x0B, "v"
  $text = $text -replace [char]0x0C, "f"

  # restliche ASCII-Controls (außer \t \r \n) entfernen
  $text = [regex]::Replace($text, "[\x00-\x08\x0E-\x1F]", "")
  return $text
}

$root = Get-RepoRoot
Set-Location $root
[Environment]::CurrentDirectory = $root

# -------------------------
# 1) Router: export_servicebook.py (P0: redacted + grant + full encrypted)
# -------------------------
$exportServicebookPath = Join-Path $root "server\app\routers\export_servicebook.py"
$exportServicebook = @'
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import threading
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from cryptography.fernet import Fernet
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import Boolean, Column, DateTime, Integer, MetaData, String, Table, inspect, select, update
from sqlalchemy.orm import Session

from app.routers.export_vehicle import get_actor, get_db

router = APIRouter(prefix="/export/servicebook", tags=["export"])


def _role_of(actor: Any) -> str:
    if actor is None:
        return ""
    if hasattr(actor, "role"):
        return str(getattr(actor, "role") or "")
    if isinstance(actor, dict):
        return str(actor.get("role") or "")
    return ""


def _user_id_of(actor: Any) -> str:
    if actor is None:
        return ""
    for attr in ("user_id", "uid", "id", "sub"):
        if hasattr(actor, attr):
            v = getattr(actor, attr)
            if v:
                return str(v)
    if isinstance(actor, dict):
        for key in ("user_id", "uid", "id", "sub"):
            v = actor.get(key)
            if v:
                return str(v)
    return ""


def _require_superadmin(actor: Any) -> None:
    if _role_of(actor) != "superadmin":
        raise HTTPException(status_code=403, detail="forbidden")


def _deny_moderator(actor: Any) -> None:
    if _role_of(actor) == "moderator":
        raise HTTPException(status_code=403, detail="forbidden")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _utcnow_naive() -> datetime:
    return _utcnow().replace(tzinfo=None)


def _derive_fernet_key(secret: str) -> bytes:
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def _get_secret() -> str:
    secret = os.environ.get("LTC_SECRET_KEY", "")
    if len(secret) < 16:
        raise HTTPException(status_code=500, detail="server_misconfigured")
    return secret


def _hmac_value(value: str) -> str:
    return hmac.new(_get_secret().encode("utf-8"), value.encode("utf-8"), hashlib.sha256).hexdigest()


def _json_default(o: Any) -> Any:
    if isinstance(o, (datetime, date)):
        return o.isoformat()
    return str(o)


_grant_lock = threading.Lock()
_grant_cache: Dict[int, Table] = {}


def _grants_table(db: Session) -> Table:
    engine = db.get_bind()
    key = id(engine)

    with _grant_lock:
        cached = _grant_cache.get(key)
        if cached is not None:
            return cached

        md = MetaData()
        insp = inspect(engine)

        if insp.has_table("export_grants_servicebook"):
            tbl = Table("export_grants_servicebook", md, autoload_with=engine)
            _grant_cache[key] = tbl
            return tbl

        tbl = Table(
            "export_grants_servicebook",
            md,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("export_token", String(255), nullable=False, unique=True, index=True),
            Column("servicebook_id", String(255), nullable=False, index=True),
            Column("expires_at", DateTime(timezone=True), nullable=False, index=True),
            Column("used", Boolean, nullable=False, default=False),
            Column("created_at", DateTime(timezone=True), nullable=False),
        )
        md.create_all(engine, tables=[tbl])
        _grant_cache[key] = tbl
        return tbl


def _servicebook_table(db: Session) -> Table:
    engine = db.get_bind()
    md = MetaData()
    insp = inspect(engine)
    for name in ("servicebook_entries", "servicebook_entry", "servicebooks", "servicebook", "service_entries", "service_entry"):
        if insp.has_table(name):
            return Table(name, md, autoload_with=engine)
    raise HTTPException(status_code=404, detail="not_found")


def _fetch_servicebook_rows(db: Session, servicebook_id: str) -> Tuple[List[Dict[str, Any]], Table]:
    tbl = _servicebook_table(db)
    if "servicebook_id" in tbl.c:
        where_col = tbl.c.servicebook_id
    elif "vehicle_id" in tbl.c:
        where_col = tbl.c.vehicle_id
    elif "id" in tbl.c:
        where_col = tbl.c.id
    else:
        raise HTTPException(status_code=500, detail="server_misconfigured")

    rows = db.execute(select(tbl).where(where_col == servicebook_id)).mappings().all()
    if not rows:
        raise HTTPException(status_code=404, detail="not_found")
    return [dict(r) for r in rows], tbl


def _enforce_redacted_access(actor: Any, rows: List[Dict[str, Any]]) -> None:
    role = _role_of(actor)
    if role == "superadmin":
        return

    if role not in {"user", "vip", "dealer"}:
        raise HTTPException(status_code=403, detail="forbidden")

    uid = _user_id_of(actor)
    if not uid:
        raise HTTPException(status_code=403, detail="forbidden")

    owner_fields = ("owner_id", "owner_user_id", "user_id", "created_by_user_id", "created_by", "actor_user_id")
    for row in rows:
        for key in owner_fields:
            val = row.get(key)
            if val and str(val) == uid:
                return
    raise HTTPException(status_code=403, detail="forbidden")


def _read_expires_at(val: Any) -> Optional[datetime]:
    if val is None:
        return None
    if isinstance(val, datetime):
        return val.replace(tzinfo=None)
    if isinstance(val, str):
        try:
            return datetime.fromisoformat(val).replace(tzinfo=None)
        except Exception:
            return None
    return None


def _redact_row(row: Dict[str, Any]) -> Dict[str, Any]:
    blocked_contains = (
        "email",
        "phone",
        "tel",
        "name",
        "address",
        "street",
        "zip",
        "city",
        "vin",
        "token",
        "secret",
        "password",
        "note",
        "comment",
        "text",
        "details",
    )
    out: Dict[str, Any] = {}
    for key, value in row.items():
        k = key.lower()
        if any(x in k for x in blocked_contains):
            continue
        out[key] = value

    vin_val = row.get("vin")
    if vin_val:
        out["vin_hmac"] = _hmac_value(str(vin_val))

    owner_email = row.get("owner_email")
    if owner_email:
        out["owner_email_hmac"] = _hmac_value(str(owner_email))

    return out


@router.get("/{servicebook_id}")
def export_servicebook_redacted(servicebook_id: str, request: Request, actor: Any = Depends(get_actor)):
    _deny_moderator(actor)
    db: Session = next(get_db(request))
    try:
        rows, _tbl = _fetch_servicebook_rows(db, servicebook_id)
        _enforce_redacted_access(actor, rows)

        redacted_rows = [_redact_row(r) for r in rows]
        data = {
            "target": "servicebook",
            "id": servicebook_id,
            "_redacted": True,
            "servicebook": {"id": servicebook_id, "entries": redacted_rows, "servicebook_id_hmac": _hmac_value(servicebook_id)},
        }
        return {"data": data, "target": "servicebook", "id": servicebook_id, "entries": redacted_rows}
    finally:
        db.close()


@router.post("/{servicebook_id}/grant")
def export_servicebook_grant(servicebook_id: str, request: Request, ttl_seconds: int = 300, actor: Any = Depends(get_actor)):
    _deny_moderator(actor)
    _require_superadmin(actor)
    db: Session = next(get_db(request))
    try:
        _rows, _tbl = _fetch_servicebook_rows(db, servicebook_id)
        ttl = max(30, min(int(ttl_seconds), 3600))
        tok = secrets.token_urlsafe(32)
        now = _utcnow_naive()
        exp = now + timedelta(seconds=ttl)

        grants = _grants_table(db)
        db.execute(
            grants.insert().values(
                export_token=tok,
                servicebook_id=servicebook_id,
                expires_at=exp,
                used=0,
                created_at=now,
            )
        )
        db.commit()
        return {
            "servicebook_id": servicebook_id,
            "export_token": tok,
            "token": tok,
            "expires_at": exp.isoformat(),
            "ttl_seconds": ttl,
            "one_time": True,
            "header": "X-Export-Token",
        }
    finally:
        db.close()


@router.get("/{servicebook_id}/full")
def export_servicebook_full(
    servicebook_id: str,
    request: Request,
    x_export_token: Optional[str] = Header(default=None, convert_underscores=False, alias="X-Export-Token"),
    actor: Any = Depends(get_actor),
):
    _deny_moderator(actor)
    _require_superadmin(actor)

    if not x_export_token:
        raise HTTPException(status_code=400, detail="missing_export_token")

    db: Session = next(get_db(request))
    try:
        rows, _tbl = _fetch_servicebook_rows(db, servicebook_id)
        grants = _grants_table(db)
        g = db.execute(select(grants).where(grants.c.export_token == x_export_token)).mappings().first()
        if g is None:
            raise HTTPException(status_code=403, detail="forbidden")
        if str(g.get("servicebook_id") or "") != str(servicebook_id):
            raise HTTPException(status_code=403, detail="forbidden")

        exp = _read_expires_at(g.get("expires_at"))
        if exp is None or _utcnow_naive() > exp:
            raise HTTPException(status_code=403, detail="forbidden")

        if int(g.get("used") or 0) != 0:
            raise HTTPException(status_code=403, detail="forbidden")

        payload = {
            "target": "servicebook",
            "id": servicebook_id,
            "servicebook": {"id": servicebook_id, "entries": rows},
            "data": {"servicebook": {"id": servicebook_id, "entries": rows}},
            "exported_at": _utcnow().isoformat(),
        }
        f = Fernet(_derive_fernet_key(_get_secret()))
        ciphertext = f.encrypt(
            json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True, default=_json_default).encode("utf-8")
        ).decode("utf-8")

        db.execute(update(grants).where(grants.c.id == g["id"]).values(used=1))
        db.commit()

        return {"servicebook_id": servicebook_id, "ciphertext": ciphertext, "alg": "fernet", "one_time": True}
    finally:
        db.close()
'@
Write-Utf8NoBom $exportServicebookPath $exportServicebook

# -------------------------
# 2) Router: export_user.py (P0: redacted + grant + full encrypted)
# -------------------------
$exportUserPath = Join-Path $root "server\app\routers\export_user.py"
$exportUser = @'
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import threading
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple

from cryptography.fernet import Fernet
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import Boolean, Column, DateTime, Integer, MetaData, String, Table, inspect, select, update
from sqlalchemy.orm import Session

from app.routers.export_vehicle import get_actor, get_db

router = APIRouter(prefix="/export/user", tags=["export"])


def _role_of(actor: Any) -> str:
    if actor is None:
        return ""
    if hasattr(actor, "role"):
        return str(getattr(actor, "role") or "")
    if isinstance(actor, dict):
        return str(actor.get("role") or "")
    return ""


def _user_id_of(actor: Any) -> str:
    if actor is None:
        return ""
    for attr in ("user_id", "uid", "id", "sub"):
        if hasattr(actor, attr):
            v = getattr(actor, attr)
            if v:
                return str(v)
    if isinstance(actor, dict):
        for key in ("user_id", "uid", "id", "sub"):
            v = actor.get(key)
            if v:
                return str(v)
    return ""


def _require_superadmin(actor: Any) -> None:
    if _role_of(actor) != "superadmin":
        raise HTTPException(status_code=403, detail="forbidden")


def _deny_moderator(actor: Any) -> None:
    if _role_of(actor) == "moderator":
        raise HTTPException(status_code=403, detail="forbidden")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _utcnow_naive() -> datetime:
    return _utcnow().replace(tzinfo=None)


def _derive_fernet_key(secret: str) -> bytes:
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def _get_secret() -> str:
    secret = os.environ.get("LTC_SECRET_KEY", "")
    if len(secret) < 16:
        raise HTTPException(status_code=500, detail="server_misconfigured")
    return secret


def _hmac_value(value: str) -> str:
    return hmac.new(_get_secret().encode("utf-8"), value.encode("utf-8"), hashlib.sha256).hexdigest()


def _json_default(o: Any) -> Any:
    if isinstance(o, (datetime, date)):
        return o.isoformat()
    return str(o)


_grant_lock = threading.Lock()
_grant_cache: Dict[int, Table] = {}


def _grants_table(db: Session) -> Table:
    engine = db.get_bind()
    key = id(engine)

    with _grant_lock:
        cached = _grant_cache.get(key)
        if cached is not None:
            return cached

        md = MetaData()
        insp = inspect(engine)
        if insp.has_table("export_grants_user"):
            tbl = Table("export_grants_user", md, autoload_with=engine)
            _grant_cache[key] = tbl
            return tbl

        tbl = Table(
            "export_grants_user",
            md,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("export_token", String(255), nullable=False, unique=True, index=True),
            Column("user_id", String(255), nullable=False, index=True),
            Column("expires_at", DateTime(timezone=True), nullable=False, index=True),
            Column("used", Boolean, nullable=False, default=False),
            Column("created_at", DateTime(timezone=True), nullable=False),
        )
        md.create_all(engine, tables=[tbl])
        _grant_cache[key] = tbl
        return tbl


def _users_table(db: Session) -> Table:
    engine = db.get_bind()
    md = MetaData()
    insp = inspect(engine)
    for name in ("auth_users", "users", "user"):
        if insp.has_table(name):
            return Table(name, md, autoload_with=engine)
    raise HTTPException(status_code=404, detail="not_found")


def _fetch_user_row(db: Session, user_id: str) -> Tuple[Dict[str, Any], Table]:
    tbl = _users_table(db)
    candidate_cols = [c for c in ("user_id", "id", "public_id", "uid", "sub") if c in tbl.c]
    for col in candidate_cols:
        row = db.execute(select(tbl).where(tbl.c[col] == user_id)).mappings().first()
        if row is not None:
            return dict(row), tbl
    raise HTTPException(status_code=404, detail="not_found")


def _enforce_redacted_access(actor: Any, target_user_id: str) -> None:
    role = _role_of(actor)
    if role == "superadmin":
        return
    if role not in {"user", "vip", "dealer"}:
        raise HTTPException(status_code=403, detail="forbidden")
    if _user_id_of(actor) != str(target_user_id):
        raise HTTPException(status_code=403, detail="forbidden")


def _read_expires_at(val: Any) -> Optional[datetime]:
    if val is None:
        return None
    if isinstance(val, datetime):
        return val.replace(tzinfo=None)
    if isinstance(val, str):
        try:
            return datetime.fromisoformat(val).replace(tzinfo=None)
        except Exception:
            return None
    return None


def _redacted_user(row: Dict[str, Any], target_user_id: str) -> Dict[str, Any]:
    blocked_contains = (
        "email",
        "phone",
        "tel",
        "name",
        "address",
        "street",
        "zip",
        "city",
        "secret",
        "password",
        "token",
    )
    out: Dict[str, Any] = {"user_id": target_user_id, "_redacted": True}

    for key, value in row.items():
        k = key.lower()
        if any(x in k for x in blocked_contains):
            continue
        if k in {"created_at", "role", "status", "id", "user_id"}:
            out[key] = value

    email_hmac = row.get("email_hmac")
    if email_hmac:
        out["email_hmac"] = str(email_hmac)
    elif row.get("email"):
        out["email_hmac"] = _hmac_value(str(row.get("email")))

    out["user_id_hmac"] = _hmac_value(target_user_id)
    return out


@router.get("/{user_id}")
def export_user_redacted(user_id: str, request: Request, actor: Any = Depends(get_actor)):
    _deny_moderator(actor)
    db: Session = next(get_db(request))
    try:
        row, _tbl = _fetch_user_row(db, user_id)
        resolved_user_id = str(row.get("user_id") or row.get("id") or user_id)
        _enforce_redacted_access(actor, resolved_user_id)
        data = {
            "target": "user",
            "id": resolved_user_id,
            "_redacted": True,
            "user": _redacted_user(row, resolved_user_id),
        }
        return {"data": data}
    finally:
        db.close()


@router.post("/{user_id}/grant")
def export_user_grant(user_id: str, request: Request, ttl_seconds: int = 300, actor: Any = Depends(get_actor)):
    _deny_moderator(actor)
    _require_superadmin(actor)
    db: Session = next(get_db(request))
    try:
        row, _tbl = _fetch_user_row(db, user_id)
        resolved_user_id = str(row.get("user_id") or row.get("id") or user_id)

        ttl = max(30, min(int(ttl_seconds), 3600))
        tok = secrets.token_urlsafe(32)
        now = _utcnow_naive()
        exp = now + timedelta(seconds=ttl)

        grants = _grants_table(db)
        db.execute(
            grants.insert().values(
                export_token=tok,
                user_id=resolved_user_id,
                expires_at=exp,
                used=0,
                created_at=now,
            )
        )
        db.commit()
        return {
            "user_id": resolved_user_id,
            "export_token": tok,
            "token": tok,
            "expires_at": exp.isoformat(),
            "ttl_seconds": ttl,
            "one_time": True,
            "header": "X-Export-Token",
        }
    finally:
        db.close()


@router.get("/{user_id}/full")
def export_user_full(
    user_id: str,
    request: Request,
    x_export_token: Optional[str] = Header(default=None, convert_underscores=False, alias="X-Export-Token"),
    actor: Any = Depends(get_actor),
):
    _deny_moderator(actor)
    _require_superadmin(actor)

    if not x_export_token:
        raise HTTPException(status_code=400, detail="missing_export_token")

    db: Session = next(get_db(request))
    try:
        row, _tbl = _fetch_user_row(db, user_id)
        resolved_user_id = str(row.get("user_id") or row.get("id") or user_id)

        grants = _grants_table(db)
        g = db.execute(select(grants).where(grants.c.export_token == x_export_token)).mappings().first()
        if g is None:
            raise HTTPException(status_code=403, detail="forbidden")
        if str(g.get("user_id") or "") != resolved_user_id:
            raise HTTPException(status_code=403, detail="forbidden")

        exp = _read_expires_at(g.get("expires_at"))
        if exp is None or _utcnow_naive() > exp:
            raise HTTPException(status_code=403, detail="forbidden")

        if int(g.get("used") or 0) != 0:
            raise HTTPException(status_code=403, detail="forbidden")

        payload = {
            "target": "user",
            "id": resolved_user_id,
            "user": row,
            "data": {"user": row},
            "exported_at": _utcnow().isoformat(),
        }
        f = Fernet(_derive_fernet_key(_get_secret()))
        ciphertext = f.encrypt(
            json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True, default=_json_default).encode("utf-8")
        ).decode("utf-8")

        db.execute(update(grants).where(grants.c.id == g["id"]).values(used=1))
        db.commit()

        return {"user_id": resolved_user_id, "ciphertext": ciphertext, "alg": "fernet", "one_time": True}
    finally:
        db.close()
'@
Write-Utf8NoBom $exportUserPath $exportUser

# -------------------------
# 3) main.py: Router include ergänzen (import + include_router)
# -------------------------
$mainPath = Join-Path $root "server\app\main.py"
$main = Read-Utf8NoBom $mainPath

if ($main -notmatch [regex]::Escape("from app.routers.export_user import router as export_user_router")) {
  $main = $main -replace "(?m)^from app\.routers\.export_servicebook import router as export_servicebook_router\s*$", "from app.routers.export_servicebook import router as export_servicebook_router`nfrom app.routers.export_user import router as export_user_router"
}

if ($main -notmatch [regex]::Escape("app.include_router(export_user_router)")) {
  $main = $main -replace "(?m)^\s*app\.include_router\(export_servicebook_router\)\s*$", "    app.include_router(export_servicebook_router)`n    app.include_router(export_user_router)"
}

Write-Utf8NoBom $mainPath $main

# -------------------------
# 4) Tests: P0 für servicebook + user
# -------------------------
$testSbPath = Join-Path $root "server\tests\test_export_servicebook_p0.py"
$testSb = @'
from __future__ import annotations

import secrets
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterator

from sqlalchemy import MetaData, Table, insert, select, text, update
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
            values["created_at"] = datetime.now(timezone.utc).isoformat()

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
'@
Write-Utf8NoBom $testSbPath $testSb

$testUserPath = Join-Path $root "server\tests\test_export_user_p0.py"
$testUser = @'
from __future__ import annotations

import secrets
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from typing import Iterator

from sqlalchemy import MetaData, Table, insert, select, text, update
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


def _ensure_users_table(db: Session) -> Table:
    engine = db.get_bind()
    md = MetaData()
    for name in ("auth_users", "users", "user"):
        try:
            return Table(name, md, autoload_with=engine)
        except Exception:
            continue

    db.execute(
        text(
            """
            CREATE TABLE auth_users (
                user_id TEXT PRIMARY KEY,
                email_hmac TEXT NOT NULL,
                role TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL,
                email TEXT NULL,
                phone TEXT NULL,
                address TEXT NULL,
                full_name TEXT NULL
            )
            """
        )
    )
    db.commit()
    return Table("auth_users", MetaData(), autoload_with=engine)


def _insert_user(client, role: str = "user") -> str:
    uid = f"usr_{secrets.token_hex(6)}"
    with _db_from_client(client) as db:
        tbl = _ensure_users_table(db)
        values = {
            "user_id": uid,
            "email_hmac": f"hmac_{secrets.token_hex(8)}",
            "role": role,
            "status": "active",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "email": "private@example.org",
            "phone": "+49170123456",
            "address": "Main Street 1",
            "full_name": "Max Mustermann",
        }
        cols = {c.name for c in tbl.columns}
        db.execute(insert(tbl).values(**{k: v for k, v in values.items() if k in cols}))
        db.commit()
    return uid


def test_export_user_p0_redacted_no_leaks_and_hmac(client, make_user_headers):
    uid = _insert_user(client)
    owner_headers = make_user_headers(uid=uid, role="user")

    r = client.get(f"/export/user/{uid}", headers=owner_headers)
    assert r.status_code == 200, r.text
    body = r.json()

    assert body["data"]["_redacted"] is True
    assert body["data"]["target"] == "user"
    assert "email_hmac" in body["data"]["user"]

    text_body = r.text.lower()
    assert "private@example.org" not in text_body
    assert "max mustermann" not in text_body
    assert "+49170123456" not in text_body


def test_export_user_p0_grant_persist_full_one_time_ttl_and_moderator_403(client, make_user_headers):
    uid = _insert_user(client)
    owner_headers = make_user_headers(uid=uid, role="user")
    sa_headers = make_user_headers(role="superadmin")
    mod_headers = make_user_headers(role="moderator")

    r_ok = client.get(f"/export/user/{uid}", headers=owner_headers)
    assert r_ok.status_code == 200

    r_mod_redacted = client.get(f"/export/user/{uid}", headers=mod_headers)
    assert r_mod_redacted.status_code == 403
    r_mod_grant = client.post(f"/export/user/{uid}/grant", headers=mod_headers)
    assert r_mod_grant.status_code == 403
    r_mod_full = client.get(f"/export/user/{uid}/full", headers=mod_headers)
    assert r_mod_full.status_code == 403

    r_other = client.get(f"/export/user/{uid}", headers=make_user_headers(role="user"))
    assert r_other.status_code == 403

    r_no_token = client.get(f"/export/user/{uid}/full", headers=sa_headers)
    assert r_no_token.status_code == 400

    r_invalid = client.get(f"/export/user/{uid}/full", headers={**sa_headers, "X-Export-Token": "invalid"})
    assert r_invalid.status_code == 403

    r_grant = client.post(f"/export/user/{uid}/grant", headers=sa_headers)
    assert r_grant.status_code == 200
    token = r_grant.json()["token"]

    with _db_from_client(client) as db:
        grants = Table("export_grants_user", MetaData(), autoload_with=db.get_bind())
        rows = db.execute(select(grants).where(grants.c.user_id == uid)).mappings().all()
        assert len(rows) == 1
        assert rows[0]["export_token"] == token

    r_full = client.get(f"/export/user/{uid}/full", headers={**sa_headers, "X-Export-Token": token})
    assert r_full.status_code == 200
    assert isinstance(r_full.json().get("ciphertext"), str) and len(r_full.json()["ciphertext"]) > 20

    r_full_again = client.get(f"/export/user/{uid}/full", headers={**sa_headers, "X-Export-Token": token})
    assert r_full_again.status_code == 403

    r_grant_exp = client.post(f"/export/user/{uid}/grant", headers=sa_headers)
    exp_token = r_grant_exp.json()["token"]
    with _db_from_client(client) as db:
        grants = Table("export_grants_user", MetaData(), autoload_with=db.get_bind())
        row = db.execute(select(grants).where(grants.c.export_token == exp_token)).mappings().first()
        assert row is not None
        past = datetime.now(timezone.utc) - timedelta(seconds=5)
        db.execute(update(grants).where(grants.c.id == row["id"]).values(expires_at=past))
        db.commit()

    r_expired = client.get(f"/export/user/{uid}/full", headers={**sa_headers, "X-Export-Token": exp_token})
    assert r_expired.status_code == 403
'@
Write-Utf8NoBom $testUserPath $testUser

# -------------------------
# 5) Docs: nur Clean-Control-Chars (du hast PR #190 bereits merged; hier kein aggressives Rewriting)
# -------------------------
$docPaths = @(
  (Join-Path $root "docs\99_MASTER_CHECKPOINT.md"),
  (Join-Path $root "docs\02_PRODUCT_SPEC_UNIFIED.md"),
  (Join-Path $root "docs\03_RIGHTS_MATRIX.md"),
  (Join-Path $root "docs\01_DECISIONS.md")
)

foreach ($p in $docPaths) {
  if (-not (Test-Path -LiteralPath $p)) { continue }
  $t = Read-Utf8NoBom $p
  $c = Clean-ControlChars $t
  if ($c -ne $t) {
    Write-Utf8NoBom $p $c
  }
}

Write-Host "OK: Export P0 Servicebook+User (Router+Tests) geschrieben, main.py ergänzt, Docs-Control-Chars bereinigt."
Write-Host "NEXT: git status; dann pwsh tools/test_all.ps1; dann commit + PR."