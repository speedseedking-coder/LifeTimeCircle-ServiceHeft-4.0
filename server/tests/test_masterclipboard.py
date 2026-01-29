from app.core.security import create_token


def _auth_headers(role="dealer", org_id="org1", sub="u1"):
    t = create_token(sub=sub, role=role, org_id=org_id)
    return {"Authorization": f"Bearer {t}"}


def test_masterclipboard_happy_path(client):
    # create session
    h = _auth_headers()
    r = client.post(
        "/api/masterclipboard/sessions",
        json={"vehicle_public_id": "veh_public_1"},
        headers={**h, "Idempotency-Key": "k1"},
    )
    assert r.status_code == 201
    session_id = r.json()["session_id"]

    # add speech
    r = client.post(
        f"/api/masterclipboard/sessions/{session_id}/speech",
        json={"source": "text", "content_redacted": "defekt vorne links"},
        headers={**h, "Idempotency-Key": "k2"},
    )
    assert r.status_code == 201

    # create triage items
    r = client.post(
        f"/api/masterclipboard/sessions/{session_id}/triage/items",
        json={
            "items": [
                {
                    "kind": "defect",
                    "title": "Bremse quietscht",
                    "details_redacted": "bei leichtem Bremsen",
                    "severity": "high",
                    "status": "open",
                    "evidence_refs": ["doc:123"],
                }
            ]
        },
        headers={**h, "Idempotency-Key": "k3"},
    )
    assert r.status_code == 201
    item_id = r.json()["created_ids"][0]

    # patch triage item
    r = client.patch(
        f"/api/masterclipboard/sessions/{session_id}/triage/items/{item_id}",
        json={"status": "in_progress"},
        headers={**h, "Idempotency-Key": "k4"},
    )
    assert r.status_code == 200
    assert r.json()["ok"] is True

    # board snapshot
    r = client.post(
        f"/api/masterclipboard/sessions/{session_id}/board/snapshot",
        json={"ordered_item_ids": [item_id], "notes_redacted": "prio 1"},
        headers={**h, "Idempotency-Key": "k5"},
    )
    assert r.status_code == 201
    assert "snapshot_id" in r.json()

    # close
    r = client.post(
        f"/api/masterclipboard/sessions/{session_id}/close",
        headers={**h, "Idempotency-Key": "k6"},
    )
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_rbac_blocks_public_and_moderator(client):
    # public role -> 403
    h_pub = _auth_headers(role="public")
    r = client.post(
        "/api/masterclipboard/sessions",
        json={"vehicle_public_id": "veh_public_1"},
        headers={**h_pub, "Idempotency-Key": "p1"},
    )
    assert r.status_code == 403

    # moderator role -> 403
    h_mod = _auth_headers(role="moderator")
    r = client.post(
        "/api/masterclipboard/sessions",
        json={"vehicle_public_id": "veh_public_1"},
        headers={**h_mod, "Idempotency-Key": "m1"},
    )
    assert r.status_code == 403


def test_missing_idempotency_key_is_400(client):
    h = _auth_headers()
    r = client.post("/api/masterclipboard/sessions", json={"vehicle_public_id": "veh_public_1"}, headers=h)
    assert r.status_code == 400
