# server/tests/test_public_qr_disclaimer.py

from __future__ import annotations

from fastapi.testclient import TestClient

EXACT_DISCLAIMER = (
    "Die Trust-Ampel bewertet ausschließlich die Dokumentations- und Nachweisqualität. "
    "Sie ist keine Aussage über den technischen Zustand des Fahrzeugs."
)


def test_public_qr_returns_exact_disclaimer() -> None:
    from app.main import app  # lazy import

    client = TestClient(app)
    r = client.get("/public/qr/test-vehicle-id")
    assert r.status_code == 200, r.text

    data = r.json()
    assert "disclaimer" in data
    assert data["disclaimer"] == EXACT_DISCLAIMER

    # Sicherheitsnetz: Public-QR darf keine Metrics/Counts/Percentages/Zeiträume liefern
    bad_keys = {"count", "percent", "percentage", "anzahl", "tage", "wochen", "monate", "jahre", "jahr"}
    assert not (set(map(str.lower, data.keys())) & bad_keys)
