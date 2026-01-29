import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Stelle sicher, dass "server/" im sys.path ist (damit "import app" immer funktioniert)
SERVER_ROOT = Path(__file__).resolve().parents[1]
if str(SERVER_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVER_ROOT))

# Env vor App-Import setzen (Settings laden SECRET_KEY Pflicht)
os.environ.setdefault("LTC_SECRET_KEY", "test-secret")
os.environ.setdefault("LTC_ENV", "test")
os.environ.setdefault("LTC_DATABASE_URL", "sqlite+pysqlite:///:memory:")

from app.main import create_app  # noqa: E402


@pytest.fixture()
def client():
    app = create_app()
    with TestClient(app) as c:
        yield c
