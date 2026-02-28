from __future__ import annotations

import importlib
import os
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.db.base import Base

_ENGINE: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def _ensure_sqlite_dir(database_url: str) -> None:
    url = (database_url or "").strip()
    if "sqlite" not in url:
        return
    if ":memory:" in url:
        return

    # erwartet URLs wie: sqlite:///./data/app.db
    marker = ":///./"
    if marker not in url:
        return

    rel = url.split(marker, 1)[1]
    db_file = Path(".") / rel
    db_dir = db_file.parent
    if str(db_dir) and str(db_dir) != ".":
        os.makedirs(db_dir, exist_ok=True)


def _try_import(module: str) -> None:
    """
    Import module if it exists.
    - If the module itself is missing -> ignore.
    - If the module exists but its import fails due to other errors -> raise (so we don't hide real bugs).
    """
    try:
        importlib.import_module(module)
    except ModuleNotFoundError as e:
        if e.name == module:
            return
        raise


def get_engine() -> Engine:
    global _ENGINE, _SessionLocal

    if _ENGINE is not None:
        return _ENGINE

    settings = get_settings()
    url = settings.database_url

    engine_kwargs: dict = {"future": True}

    # SQLite in-memory: keep same connection across sessions/tests
    if url.endswith(":memory:") or url in ("sqlite:///:memory:", "sqlite+pysqlite:///:memory:"):
        engine_kwargs["connect_args"] = {"check_same_thread": False}
        engine_kwargs["poolclass"] = StaticPool

    _ENGINE = create_engine(url, **engine_kwargs)
    _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_ENGINE, future=True)
    return _ENGINE


def get_db() -> Generator[Session, None, None]:
    global _SessionLocal

    if _SessionLocal is None:
        get_engine()
    assert _SessionLocal is not None

    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Import models so SQLAlchemy registers tables, then create_all().

    IMPORTANT:
    Some modules may be optional depending on repo state.
    Missing optional modules must NOT crash app startup / tests.
    """
    settings = get_settings()
    _ensure_sqlite_dir(settings.database_url)

    engine = get_engine()

    # Required model modules (should exist; if they don't, that's a real error)
    _try_import("app.models.audit")
    _try_import("app.models.masterclipboard")
    _try_import("app.models.vehicle")
    _try_import("app.models.vehicle_entry")

    # Optional model modules (may or may not exist in a given repo state)
    _try_import("app.models.entitlements")
    _try_import("app.models.addons")
    _try_import("app.models.consent")

    Base.metadata.create_all(bind=engine)
