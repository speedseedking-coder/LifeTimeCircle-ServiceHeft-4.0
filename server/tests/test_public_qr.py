# C:\Users\stefa\Projekte\LifeTimeCircle-ServiceHeft-4.0\server\tests\test_public_qr.py

import re
from starlette.testclient import TestClient


def test_public_qr_has_disclaimer_and_no_numbers(client: TestClient):
    r = client.get("/public/qr/demo-vehicle")
    assert r.status_code == 200, r.text

    data = r.json()
    assert set(data.keys()) == {
        "trust_light",
        "hint",
        "history_status",
        "evidence_status",
        "verification_level",
        "accident_status",
        "accident_status_label",
        "disclaimer",
    }

    assert data["trust_light"] in {"rot", "orange", "gelb", "gruen"}
    assert data["history_status"] in {"vorhanden", "nicht_vorhanden"}
    assert data["evidence_status"] in {"vorhanden", "nicht_vorhanden"}
    assert data["verification_level"] in {"niedrig", "mittel", "hoch"}
    assert data["accident_status"] in {"unfallfrei", "nicht_unfallfrei", "unbekannt"}
    assert data["accident_status_label"] in {"Unfallfrei", "Nicht unfallfrei", "Unbekannt"}

    # Pflicht-Disclaimer (exakt)
    assert data["disclaimer"] == (
        "Die Trust-Ampel bewertet ausschließlich die Dokumentations- und Nachweisqualität. "
        "Sie ist keine Aussage über den technischen Zustand des Fahrzeugs."
    )

    # Keine Zahlen in Public-Texten (keine Counts/Zeiträume/Metriken)
    assert not re.search(r"\d", data["hint"] + data["disclaimer"])
