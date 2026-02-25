from __future__ import annotations

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
    if "sqlite" not in database_url:
        return
    if ":memory:" in database_url:
        return

    marker = ":///./"
    if marker not in database_url:
        return

    rel = database_url.split(marker, 1)[1]
    db_file = Path(".") / rel
    db_dir = db_file.parent
    if str(db_dir) and str(db_dir) != ".":
        os.makedirs(db_dir, exist_ok=True)


def get_engine() -> Engine:
    global _ENGINE, _SessionLocal

    if _ENGINE is not None:
        return _ENGINE

    settings = get_settings()
    url = settings.database_url

    connect_args: dict = {}
    engine_kwargs: dict = {"future": True}

    # SQLite in-memory: gleiche Connection halten (wichtig für Tests)
    if url.endswith(":memory:") or url in ("sqlite:///:memory:", "sqlite+pysqlite:///:memory:"):
        connect_args = {"check_same_thread": False}
        engine_kwargs["poolclass"] = StaticPool

    if connect_args:
        engine_kwargs["connect_args"] = connect_args

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
    settings = get_settings()
    _ensure_sqlite_dir(settings.database_url)

    engine = get_engine()

    # Modelle importieren, damit Tabellen registriert sind
    from app.models import audit as _audit  # noqa: F401
    from app.models import masterclipboard as _mc  # noqa: F401

    try:
        from app.models import entitlements as _entitlements  # noqa: F401
    except Exception:
        pass

    try:
        from app.models import addons as _addons  # noqa: F401
    except Exception:
        pass

    try:
        from app.models import consent as _consent  # noqa: F401
    except Exception:
        pass

    from app.models import vehicle as _vehicle  # noqa: F401

    Base.metadata.create_all(bind=engine)
