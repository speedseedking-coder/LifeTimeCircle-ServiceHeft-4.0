# server/tests/test_servicebook_inspection_flow.py
from __future__ import annotations

import datetime as dt
import uuid
from typing import Any, Dict, Optional

from fastapi.testclient import TestClient

from app.main import create_app
from app.routers.export_vehicle import get_actor  # type: ignore


def _get_id(d: Dict[str, Any]) -> Optional[str]:
    for k in ("id", "entry_id", "servicebook_entry_id"):
        if k in d and d[k] is not None:
            return str(d[k])
    return None


def _client_admin() -> TestClient:
    app = create_app()
    app.dependency_overrides[get_actor] = lambda: {"role": "admin", "user_id": "test-admin"}
    return TestClient(app)


def test_inspection_not_ok_creates_case() -> None:
    client = _client_admin()
    sbid = str(uuid.uuid4())

    payload = {
        "source": "GPS",
        "result_status": "NOT_OK",
        "title": "GPS Probefahrt",
        "summary": "Beweisspur erstellt",
        "details": "Abweichung erkannt",
        "occurred_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "km": 12345,
        "document_ids": [],
    }

    r = client.post(f"/servicebook/{sbid}/inspection-events", json=payload)
    assert r.status_code in (200, 201), r.text
    data = r.json()

    assert data.get("inspection_event") is not None
    assert data.get("case") is not None, "NOT_OK muss automatisch einen Case erzeugen"


def test_remediation_ok_marks_case_done() -> None:
    client = _client_admin()
    sbid = str(uuid.uuid4())

    r1 = client.post(
        f"/servicebook/{sbid}/inspection-events",
        json={"source": "READOUT", "result_status": "NOT_OK", "title": "OBD Auslesung"},
    )
    assert r1.status_code in (200, 201), r1.text
    case = r1.json().get("case")
    assert case is not None

    case_id = _get_id(case)
    assert case_id is not None, "Case hat keine ID (id/entry_id/...)"

    r2 = client.post(
        f"/servicebook/{sbid}/cases/{case_id}/remediation",
        json={
            "result_status": "OK",
            "title": "Behebung",
            "summary": "Fehler behoben",
            "details": "Maßnahme dokumentiert",
            "occurred_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        },
    )
    assert r2.status_code in (200, 201), r2.text
    data2 = r2.json()

    assert data2.get("case_status") == "DONE"
    assert data2.get("remediation") is not None

