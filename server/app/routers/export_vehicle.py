from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import threading
from contextlib import contextmanager
from datetime import date, datetime, timedelta, timezone
from typing import Any, Callable, Dict, Iterator, Optional, Tuple

from cryptography.fernet import Fernet
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    MetaData,
    String,
    Table,
    inspect,
    select,
    update,
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.auth.actor import dev_headers_enabled, require_actor as core_require_actor

# ============================================================
# Actor / RBAC (LAZY, keine Varargs => keine 422 Query-Fallen)
# ============================================================

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
            if v is not None and str(v) != "":
                return str(v)

    if isinstance(actor, dict):
        for key in ("user_id", "uid", "id", "sub"):
            v = actor.get(key)
            if v is not None and str(v) != "":
                return str(v)

    return ""


def _call_best_effort(fn: Callable[..., Any], request: Request) -> Any:
    try:
        return fn()
    except TypeError:
        pass
    try:
        return fn(request)
    except TypeError:
        pass
    try:
        return fn(request=request)
    except TypeError:
        pass
    try:
        return fn(request.app)
    except TypeError:
        pass
    try:
        return fn(app=request.app)
    except TypeError:
        pass
    return fn()


def get_actor(request: Request) -> Any:
    ov = getattr(request.app, "dependency_overrides", None)
    if isinstance(ov, dict) and ov:
        for fn in list(ov.values()) + list(ov.keys()):
            if not callable(fn):
                continue
            try:
                res = _call_best_effort(fn, request)
            except Exception:
                continue

            actor = None
            if hasattr(res, "__iter__") and hasattr(res, "__next__"):
                gen = res
                try:
                    actor = next(gen)
                except Exception:
                    actor = None
                finally:
                    try:
                        if hasattr(gen, "close"):
                            gen.close()
                    except Exception:
                        pass
            else:
                actor = res

            if _role_of(actor):
                return actor

    try:
        import app.rbac as _rbac  # type: ignore

        for name in ("require_actor", "get_actor"):
            fn = getattr(_rbac, name, None)
            if not callable(fn):
                continue
            try:
                res = _call_best_effort(fn, request)
            except Exception:
                continue

            actor = None
            if hasattr(res, "__iter__") and hasattr(res, "__next__"):
                gen = res
                try:
                    actor = next(gen)
                except Exception:
                    actor = None
                finally:
                    try:
                        if hasattr(gen, "close"):
                            gen.close()
                    except Exception:
                        pass
            else:
                actor = res

            if _role_of(actor):
                return actor
    except Exception:
        pass

    try:
        return core_require_actor(request)
    except HTTPException as exc:
        if exc.status_code != 401:
            raise

    # Legacy test/dev compatibility: only honor X-LTC-* headers when the
    # explicit dev-header gate is enabled. Production must never trust these.
    if dev_headers_enabled():
        role = request.headers.get("X-LTC-ROLE") or request.headers.get("x-ltc-role")
        uid = request.headers.get("X-LTC-UID") or request.headers.get("x-ltc-uid")
        if role:
            return {"role": role, "user_id": uid or "", "uid": uid or "", "roles": [role]}

    raise HTTPException(status_code=401, detail="unauthorized")


def forbid_moderator(actor: Any = Depends(get_actor)) -> None:
    if _role_of(actor) == "moderator":
        raise HTTPException(status_code=403, detail="forbidden")


# ============================================================
# DB dependency (LAZY: overrides/state/module scan)
# ============================================================

@contextmanager
def _session_from_result(res: Any) -> Iterator[Session]:
    if hasattr(res, "__iter__") and hasattr(res, "__next__"):
        gen = res
        db = next(gen)
        if not isinstance(db, Session):
            try:
                if hasattr(gen, "close"):
                    gen.close()
            except Exception:
                pass
            raise HTTPException(status_code=500, detail="server_misconfigured")
        try:
            yield db
        finally:
            try:
                if hasattr(gen, "close"):
                    gen.close()
            except Exception:
                pass
        return

    if isinstance(res, Session):
        try:
            yield res
        finally:
            try:
                res.close()
            except Exception:
                pass
        return

    raise HTTPException(status_code=500, detail="server_misconfigured")


def _probe_db_from_overrides(request: Request) -> Optional[Session]:
    ov = getattr(request.app, "dependency_overrides", None)
    if not isinstance(ov, dict) or not ov:
        return None

    for fn in list(ov.values()) + list(ov.keys()):
        if not callable(fn):
            continue
        try:
            res = _call_best_effort(fn, request)
        except Exception:
            continue
        try:
            with _session_from_result(res) as db:
                return db
        except Exception:
            continue

    return None


def _probe_db_from_state(request: Request) -> Optional[Session]:
    st = getattr(request.app, "state", None)
    if st is None:
        return None

    for name in (
        "_SessionLocal",
        "SessionLocal",
        "session_local",
        "sessionmaker",
        "SessionMaker",
        "db_sessionmaker",
        "db_session_factory",
        "db_factory",
    ):
        factory = getattr(st, name, None)
        if callable(factory):
            try:
                db = factory()
                if isinstance(db, Session):
                    return db
            except Exception:
                continue

    engine = getattr(st, "engine", None) or getattr(st, "db_engine", None) or getattr(st, "_engine", None)
    if engine is not None:
        try:
            from sqlalchemy.orm import sessionmaker

            SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
            db = SessionLocal()
            if isinstance(db, Session):
                return db
        except Exception:
            return None

    return None


def _probe_db_from_modules(request: Request) -> Optional[Session]:
    for modname in (
        "app.db",
        "app.database",
        "app.core.db",
        "app.core.database",
        "app.deps",
        "app.dependencies",
    ):
        try:
            mod = __import__(modname, fromlist=["*"])
        except Exception:
            continue

        for fname in ("get_db_prod", "get_db", "get_session", "db_session"):
            fn = getattr(mod, fname, None)
            if callable(fn):
                try:
                    res = _call_best_effort(fn, request)
                except Exception:
                    continue
                try:
                    with _session_from_result(res) as db:
                        return db
                except Exception:
                    continue

        for sname in ("SessionLocal", "session_local", "SessionMaker", "sessionmaker"):
            fac = getattr(mod, sname, None)
            if callable(fac):
                try:
                    db = fac()
                    if isinstance(db, Session):
                        return db
                except Exception:
                    continue

        engine = getattr(mod, "engine", None)
        if engine is not None:
            try:
                from sqlalchemy.orm import sessionmaker

                SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
                db = SessionLocal()
                if isinstance(db, Session):
                    return db
            except Exception:
                continue

    return None


def get_db(request: Request) -> Iterator[Session]:
    db = _probe_db_from_overrides(request)
    if db is None:
        db = _probe_db_from_state(request)
    if db is None:
        db = _probe_db_from_modules(request)

    if db is None:
        raise HTTPException(status_code=500, detail="server_misconfigured")

    try:
        yield db
    finally:
        try:
            db.close()
        except Exception:
            pass


get_db_prod = get_db


@contextmanager
def _db_from_request(request: Request) -> Iterator[Session]:
    gen = get_db(request)
    db = next(gen)
    try:
        yield db
    finally:
        try:
            gen.close()
        except Exception:
            pass


# ============================================================
# Router logic: public_id lookup + owner scope
# ============================================================

router = APIRouter(
    prefix="/export/vehicle",
    tags=["export"],
    dependencies=[Depends(forbid_moderator)],
)

_ADMIN_ROLES = {"admin", "superadmin"}

_meta_lock = threading.Lock()
_meta_cache: Dict[int, Tuple[MetaData, Table]] = {}

_grant_lock = threading.Lock()
_grant_cache: Dict[int, Table] = {}


def _is_admin_like(actor: Any) -> bool:
    return _role_of(actor) in _ADMIN_ROLES


def _require_superadmin(actor: Any) -> None:
    if _role_of(actor) != "superadmin":
        raise HTTPException(status_code=403, detail="forbidden")


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _utcnow_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _get_engine(db: Session) -> Engine:
    bind = db.get_bind()
    if bind is None:
        raise HTTPException(status_code=500, detail="server_misconfigured")
    return bind  # type: ignore[return-value]


def _vehicles_table(db: Session) -> Table:
    engine = _get_engine(db)
    key = id(engine)

    with _meta_lock:
        cached = _meta_cache.get(key)
        if cached is not None:
            return cached[1]

        md = MetaData()
        for name in ("vehicles", "vehicle"):
            try:
                tbl = Table(name, md, autoload_with=engine)
                _meta_cache[key] = (md, tbl)
                return tbl
            except Exception:
                continue

    raise HTTPException(status_code=500, detail="server_misconfigured")


def _lookup_vehicle(db: Session, vehicle_id: str) -> Tuple[Dict[str, Any], Table]:
    tbl = _vehicles_table(db)

    cand_names: list[str] = []
    for cname in tbl.c.keys():
        l = cname.lower()
        if l in ("public_id", "publicid", "vehicle_public_id", "vehiclepublicid"):
            cand_names.append(cname)
        elif ("public" in l and "id" in l) or l in ("vehicle_id", "vehicleid"):
            cand_names.append(cname)

    seen = set()
    candidates: list[str] = []
    for n in cand_names:
        if n not in seen:
            seen.add(n)
            candidates.append(n)

    for cname in candidates:
        col = tbl.c.get(cname)
        if col is None:
            continue
        row = db.execute(select(tbl).where(col == vehicle_id)).mappings().first()
        if row is not None:
            return dict(row), tbl

    if "id" in tbl.c:
        row = db.execute(select(tbl).where(tbl.c.id == vehicle_id)).mappings().first()
        if row is not None:
            return dict(row), tbl

        try:
            vid_int = int(vehicle_id)
        except Exception:
            vid_int = None
        if vid_int is not None:
            row2 = db.execute(select(tbl).where(tbl.c.id == vid_int)).mappings().first()
            if row2 is not None:
                return dict(row2), tbl

    raise HTTPException(status_code=404, detail="not_found")


def _owner_value_from_row(tbl: Table, row: Dict[str, Any]) -> Optional[str]:
    for cname in ("owner_user_id", "owner_uid", "owner_id", "user_id", "uid"):
        if cname in tbl.c:
            v = row.get(cname)
            return "" if v is None else str(v)
    return None


def _enforce_scope(actor: Any, row: Dict[str, Any], tbl: Table) -> None:
    if _is_admin_like(actor):
        return

    owner_val = _owner_value_from_row(tbl, row)
    if owner_val is None:
        raise HTTPException(status_code=403, detail="forbidden")

    actor_uid = _user_id_of(actor)
    if owner_val != actor_uid:
        raise HTTPException(status_code=403, detail="forbidden")


# ============================================================
# Grant persistence: export_grants_vehicle (für TTL Test)
#   -> braucht id PK (test nutzt grants.c.id / row["id"])
#   -> migriert test-sicher: wenn Tabelle existiert aber ohne id -> drop & recreate
# ============================================================

def _grants_table(db: Session) -> Table:
    engine = _get_engine(db)
    key = id(engine)

    with _grant_lock:
        cached = _grant_cache.get(key)
        if cached is not None:
            return cached

        insp = inspect(engine)
        if insp.has_table("export_grants_vehicle"):
            cols = [c.get("name") for c in insp.get_columns("export_grants_vehicle")]
            if "id" not in cols:
                old_md = MetaData()
                old = Table("export_grants_vehicle", old_md, autoload_with=engine)
                old.drop(engine, checkfirst=True)

        md = MetaData()
        grants = Table(
            "export_grants_vehicle",
            md,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("export_token", String, nullable=False, unique=True),
            Column("vehicle_id", String, nullable=False),
            Column("expires_at", DateTime, nullable=False),
            Column("used", Integer, nullable=False, default=0, server_default="0"),
            Column("created_at", DateTime, nullable=False),
        )
        md.create_all(engine, tables=[grants])
        _grant_cache[key] = grants
        return grants


def _read_expires_at(val: Any) -> Optional[datetime]:
    if val is None:
        return None
    if isinstance(val, datetime):
        return val.replace(tzinfo=None)
    if isinstance(val, str):
        try:
            dt = datetime.fromisoformat(val)
            return dt.replace(tzinfo=None)
        except Exception:
            return None
    return None


# ============================================================
# Crypto / helpers
# ============================================================

def _derive_fernet_key(secret: str) -> bytes:
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def _get_secret() -> str:
    secret = os.environ.get("LTC_SECRET_KEY", "")
    if len(secret) < 16:
        raise HTTPException(status_code=500, detail="server_misconfigured")
    return secret


def _get_fernet() -> Fernet:
    secret = _get_secret()
    return Fernet(_derive_fernet_key(secret))


def _ttl_seconds(ttl_seconds_param: int) -> int:
    env = os.environ.get("LTC_EXPORT_TTL_SECONDS", "").strip()
    if env:
        try:
            ttl_seconds_param = int(env)
        except Exception:
            pass

    if ttl_seconds_param < 30:
        ttl_seconds_param = 30
    if ttl_seconds_param > 3600:
        ttl_seconds_param = 3600
    return ttl_seconds_param


def _json_default(o: Any) -> Any:
    if isinstance(o, (datetime, date)):
        return o.isoformat()
    if isinstance(o, (bytes, bytearray)):
        return base64.urlsafe_b64encode(bytes(o)).decode("ascii")
    if isinstance(o, (set, tuple)):
        return list(o)
    return str(o)


def _vin_hmac(row: Dict[str, Any]) -> Optional[str]:
    # Tests erwarten vin_hmac im redacted payload, aber vin darf nicht raus.
    vin = row.get("vin")
    if vin is None or str(vin) == "":
        return None
    secret = _get_secret()
    return hmac.new(secret.encode("utf-8"), str(vin).encode("utf-8"), hashlib.sha256).hexdigest()


# ============================================================
# Routes (genaues Test-Shape)
# ============================================================

@router.get("/{vehicle_id}")
def export_vehicle_redacted(vehicle_id: str, request: Request, actor: Any = Depends(get_actor)):
    if _role_of(actor) == "moderator":
        raise HTTPException(status_code=403, detail="forbidden")

    with _db_from_request(request) as db:
        row, tbl = _lookup_vehicle(db, vehicle_id)
        _enforce_scope(actor, row, tbl)

        pid = str(row.get("public_id") or row.get("id") or vehicle_id)

        data: Dict[str, Any] = {
            "target": "vehicle",
            "id": pid,
            "vehicle_id": pid,
            "public_id": pid,
            "_redacted": True,
            "exported_at": _utcnow().isoformat(),
            # p0-kompat: nested vehicle mit safe-only Teilen
            "vehicle": {"public_id": pid},
        }

        # optional mask-helpers (falls vorhanden)
        if "vin_prefix3" in tbl.c:
            data["vehicle"]["vin_prefix3"] = row.get("vin_prefix3")
        if "vin_last4" in tbl.c:
            data["vehicle"]["vin_last4"] = row.get("vin_last4")

        # REQUIRED by tests/test_export_vehicle.py
        vh = _vin_hmac(row)
        if vh is not None:
            data["vin_hmac"] = vh

        # Hard guarantee: no raw vin / owner_email leaks
        data.pop("vin", None)
        data.pop("owner_email", None)
        if isinstance(data.get("vehicle"), dict):
            data["vehicle"].pop("vin", None)
            data["vehicle"].pop("owner_email", None)

        return {"data": data}


@router.post("/{vehicle_id}/grant")
def export_vehicle_grant(vehicle_id: str, request: Request, ttl_seconds: int = 300, actor: Any = Depends(get_actor)):
    if _role_of(actor) == "moderator":
        raise HTTPException(status_code=403, detail="forbidden")

    _require_superadmin(actor)

    with _db_from_request(request) as db:
        row, _tbl = _lookup_vehicle(db, vehicle_id)
        pid = str(row.get("public_id") or row.get("id") or vehicle_id)

        ttl = _ttl_seconds(ttl_seconds)
        tok = secrets.token_urlsafe(32)
        now = _utcnow_naive()
        exp = now + timedelta(seconds=ttl)

        grants = _grants_table(db)
        db.execute(
            grants.insert().values(
                export_token=tok,
                vehicle_id=pid,
                expires_at=exp,
                used=0,
                created_at=now,
            )
        )
        db.commit()

        return {
            "vehicle_id": pid,
            "export_token": tok,
            "token": tok,
            "expires_at": exp.isoformat(),
            "ttl_seconds": ttl,
            "one_time": True,
            "header": "X-Export-Token",
        }


@router.get("/{vehicle_id}/full")
def export_vehicle_full(
    vehicle_id: str,
    request: Request,
    x_export_token: Optional[str] = Header(default=None, convert_underscores=False, alias="X-Export-Token"),
    actor: Any = Depends(get_actor),
):
    if _role_of(actor) == "moderator":
        raise HTTPException(status_code=403, detail="forbidden")

    _require_superadmin(actor)

    if not x_export_token:
        raise HTTPException(status_code=400, detail="missing_export_token")

    with _db_from_request(request) as db:
        row, _tbl = _lookup_vehicle(db, vehicle_id)
        pid = str(row.get("public_id") or row.get("id") or vehicle_id)

        grants = _grants_table(db)
        g = db.execute(select(grants).where(grants.c.export_token == x_export_token)).mappings().first()
        if g is None:
            raise HTTPException(status_code=403, detail="forbidden")

        if str(g.get("vehicle_id") or "") != pid:
            raise HTTPException(status_code=403, detail="forbidden")

        exp = _read_expires_at(g.get("expires_at"))
        if exp is None or _utcnow_naive() > exp:
            raise HTTPException(status_code=403, detail="forbidden")

        try:
            used_int = int(g.get("used") or 0)
        except Exception:
            used_int = 0
        if used_int != 0:
            raise HTTPException(status_code=403, detail="forbidden")

        # Full payload MUST satisfy tests/test_export_vehicle.py:
        # payload["target"], payload["id"], payload["vehicle"]["vin"]
        full_payload: Dict[str, Any] = {
            "target": "vehicle",
            "id": pid,
            "exported_at": _utcnow().isoformat(),
            # REQUIRED: top-level vehicle
            "vehicle": row,
            # p0-kompat: zusätzlich data.vehicle
            "data": {"vehicle": row},
        }

        f = _get_fernet()
        plaintext = json.dumps(
            full_payload,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
            default=_json_default,
        ).encode("utf-8")
        ciphertext = f.encrypt(plaintext).decode("utf-8")

        # one-time: mark used by id (tests reflect grants.c.id)
        db.execute(update(grants).where(grants.c.id == g["id"]).values(used=1))
        db.commit()

        return {"vehicle_id": pid, "ciphertext": ciphertext, "alg": "fernet", "one_time": True}
