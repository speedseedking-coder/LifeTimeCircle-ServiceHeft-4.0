
import os
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings
from app.db.base import Base


_ENGINE: Engine | None = None
_SessionLocal: sessionmaker | None = None


def get_engine() -> Engine:
    global _ENGINE, _SessionLocal

    if _ENGINE is not None:
        return _ENGINE

    settings = get_settings()
    url = settings.database_url

    connect_args = {}
    poolclass = None

    # SQLite in-memory: gleiche Connection halten (wichtig für Tests)
    if url.endswith(":memory:"):
        connect_args = {"check_same_thread": False}
        poolclass = StaticPool

    _ENGINE = create_engine(url, connect_args=connect_args, poolclass=poolclass, future=True)
    _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_ENGINE, future=True)

    return _ENGINE


def get_db():
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
    engine = get_engine()

    # sicherstellen, dass ./data existiert (nur wenn file-sqlite)
    settings = get_settings()
    if "sqlite" in settings.database_url and "///./" in settings.database_url:
        os.makedirs("./data", exist_ok=True)

    # Modelle importieren, damit Tabellen registriert sind
    from app.models import audit as _audit  # noqa: F401
    from app.models import masterclipboard as _mc  # noqa: F401

    Base.metadata.create_all(bind=engine)
