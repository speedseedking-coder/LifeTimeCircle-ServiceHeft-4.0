# server/scripts/patch_tests_vehicles_entries_api_p0.ps1
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-RepoRoot {
  $dir = Get-Location
  for ($i = 0; $i -lt 12; $i++) {
    if (Test-Path (Join-Path $dir ".git")) { return (Resolve-Path $dir).Path }
    $parent = Split-Path -Parent $dir
    if ($parent -eq $dir) { break }
    $dir = $parent
  }
  throw "Repo-Root nicht gefunden (.git). Bitte im Repo-Root ausführen."
}

function Write-Utf8NoBom([string]$path, [string]$content) {
  $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($path, $content, $utf8NoBom)
}

$root = Resolve-RepoRoot
$testPath = Join-Path $root "server/tests/test_vehicles_entries_api_p0.py"

$dir = Split-Path -Parent $testPath
if (!(Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }

$test = @'
# server/tests/test_vehicles_entries_api_p0.py
from __future__ import annotations

import uuid
from contextlib import contextmanager
from typing import Any, Dict

# WICHTIG: exakt der Dependency-Callable, den vehicles.py via Depends(get_actor) nutzt
from app.routers.export_vehicle import get_actor  # type: ignore


def _mk_actor(role: str) -> Dict[str, Any]:
    uid = f"t_{role}_{uuid.uuid4().hex[:12]}"
    actor: Dict[str, Any] = {
        "role": role,
        "user_id": uid,
        "id": uid,
        "email": f"{role}-{uid}@example.com",
    }
    if role == "dealer":
        actor["business_id"] = f"biz_{uid}"
    return actor


@contextmanager
def _as_actor(client, actor: Dict[str, Any]):
    overrides = client.app.dependency_overrides
    prev = overrides.get(get_actor)
    overrides[get_actor] = lambda: actor
    try:
        yield
    finally:
        if prev is None:
            overrides.pop(get_actor, None)
        else:
            overrides[get_actor] = prev


def _ensure_consent(client) -> None:
    # best-effort: akzeptieren, ohne exakte API-Details zu kennen
    st = client.get("/consent/status")
    if st.status_code == 200:
        j = st.json()
        if isinstance(j, dict) and (j.get("accepted") is True or j.get("is_accepted") is True):
            return

    version = None
    cur = client.get("/consent/current")
    if cur.status_code == 200:
        j = cur.json()
        if isinstance(j, dict):
            for k in ("version", "current_version", "consent_version"):
                if k in j:
                    version = j.get(k)
                    break
            if version is None and isinstance(j.get("current"), dict):
                version = j["current"].get("version") or j["current"].get("current_version")

    payloads = []
    if version:
        payloads.append({"version": version})
    payloads.append({})

    for p in payloads:
        r = client.post("/consent/accept", json=p, headers={"Idempotency-Key": str(uuid.uuid4())})
        if r.status_code in (200, 204, 409):
            return
        if r.status_code == 422:
            continue

    r2 = client.post("/consent/accept", headers={"Idempotency-Key": str(uuid.uuid4())})
    if r2.status_code in (200, 204, 409):
        return
    raise AssertionError(f"consent accept failed: {r2.status_code} {r2.text}")


def test_vehicle_paywall_user_max_1(client):
    actor = _mk_actor("user")
    with _as_actor(client, actor):
        _ensure_consent(client)

        r1 = client.post("/vehicles", json={
            "vin": "WVWZZZ1JZXW000001",
            "make": "VW",
            "model": "Golf",
            "year": 2020,
            "accident_status": "unknown",
        })
        assert r1.status_code == 200, r1.text
        vid = r1.json()["id"]

        r2 = client.post("/vehicles", json={
            "vin": "WVWZZZ1JZXW000002",
            "make": "VW",
            "model": "Golf",
            "year": 2021,
            "accident_status": "unknown",
        })
        assert r2.status_code == 402, r2.text

        r3 = client.get(f"/vehicles/{vid}")
        assert r3.status_code == 200, r3.text


def test_vehicle_object_level_forbidden(client):
    vip = _mk_actor("vip")
    user = _mk_actor("user")

    with _as_actor(client, vip):
        _ensure_consent(client)
        r = client.post("/vehicles", json={
            "vin": "JH4KA9650MC000001",
            "make": "Acura",
            "model": "Legend",
            "year": 1991,
            "accident_status": "unknown",
        })
        assert r.status_code == 200, r.text
        vid = r.json()["id"]

    with _as_actor(client, user):
        _ensure_consent(client)
        r2 = client.get(f"/vehicles/{vid}")
        assert r2.status_code == 403, r2.text


def test_entries_required_fields_422(client):
    vip = _mk_actor("vip")
    with _as_actor(client, vip):
        _ensure_consent(client)

        r = client.post("/vehicles", json={
            "vin": "WDB12345678900001",
            "make": "Mercedes",
            "model": "W123",
            "year": 1982,
            "accident_status": "unknown",
        })
        assert r.status_code == 200, r.text
        vid = r.json()["id"]

        bad = client.post(f"/vehicles/{vid}/entries", json={
            "date": "2026-02-01",
            "entry_type": "service",
            "performed_by": "Fachwerkstatt"
        })
        assert bad.status_code == 422, bad.text
'@

Write-Utf8NoBom $testPath $test
Write-Host "OK: test_vehicles_entries_api_p0.py rewritten to use only fixture 'client' + actor override."