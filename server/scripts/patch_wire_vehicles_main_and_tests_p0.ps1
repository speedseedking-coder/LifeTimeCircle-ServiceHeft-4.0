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

$vehPath  = Join-Path $root "server/app/routers/vehicles.py"
$mainPath = Join-Path $root "server/app/main.py"
$testPath = Join-Path $root "server/tests/test_vehicles_entries_api_p0.py"

foreach ($p in @($vehPath, $mainPath)) {
  if (!(Test-Path $p)) { throw "Nicht gefunden: $p" }
}

# --- vehicles.py: forbid_moderator Import auf existierenden Pfad fixen + newline ---
$veh = Get-Content -Raw -Encoding UTF8 $vehPath
if (($veh.Trim()).Length -lt 40) { throw "vehicles.py ist leer/zu kurz. Abbruch." }

# app.guards existiert sicher (siehe server/app/main.py)
$veh2 = $veh -replace 'from app\.auth\.guards import forbid_moderator', 'from app.guards import forbid_moderator'

# newline am Ende erzwingen
if (-not ($veh2.EndsWith("`n") -or $veh2.EndsWith("`r`n"))) { $veh2 += "`n" }
if ($veh2 -ne $veh) { Write-Utf8NoBom $vehPath $veh2 }

# --- main.py patch ---
$main = Get-Content -Raw -Encoding UTF8 $mainPath
$nl = "`n"; if ($main -match "`r`n") { $nl = "`r`n" }
$lines = $main -split "\r?\n"

$importLine = "from app.routers.vehicles import router as vehicles_router"
if ($main -notmatch [regex]::Escape($importLine)) {
  # bevorzugt nach public_site import einfügen
  $idx = -1
  for ($i=0; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -match '^from app\.routers\.public_site import router as public_site_router\s*$') { $idx = $i; break }
  }
  if ($idx -lt 0) {
    # fallback: nach letzter from app.routers... Zeile
    for ($i=0; $i -lt $lines.Count; $i++) {
      if ($lines[$i] -match '^from app\.routers(\.| )') { $idx = $i }
    }
  }
  if ($idx -lt 0) { throw "main.py: keine passende app.routers Importzeile gefunden." }

  $new = @()
  for ($i=0; $i -lt $lines.Count; $i++) {
    $new += $lines[$i]
    if ($i -eq $idx) { $new += $importLine }
  }
  $lines = $new
  $main = ($lines -join $nl)
}

$includeLine = "    app.include_router(vehicles_router)"
if ($main -notmatch 'include_router\(\s*vehicles_router\s*\)') {
  $lines = $main -split "\r?\n"
  $ins = -1

  for ($i=0; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -match '^\s*app\.include_router\(\s*sale_transfer_router\s*\)\s*$') { $ins = $i; break }
  }
  if ($ins -lt 0) {
    for ($i=0; $i -lt $lines.Count; $i++) {
      if ($lines[$i] -match '^\s*app\.include_router\(\s*consent_router\s*\)\s*$') { $ins = $i; break }
    }
  }
  if ($ins -lt 0) {
    for ($i=0; $i -lt $lines.Count; $i++) {
      if ($lines[$i] -match '^\s*app\.include_router\(') { $ins = $i }
    }
  }
  if ($ins -lt 0) { throw "main.py: keine app.include_router(...) Zeile gefunden." }

  $new = @()
  for ($i=0; $i -lt $lines.Count; $i++) {
    $new += $lines[$i]
    if ($i -eq $ins) { $new += $includeLine }
  }
  $main = ($new -join $nl)
}

Write-Utf8NoBom $mainPath ($main.TrimEnd() + $nl)

# --- Testfile anlegen (falls fehlt) ---
if (!(Test-Path $testPath)) {
  $test = @'
# server/tests/test_vehicles_entries_api_p0.py
import uuid

def _ensure_consent(client):
    # best-effort, ohne Knowledge über exaktes Schema
    st = client.get("/consent/status")
    if st.status_code == 200:
        j = st.json()
        if j.get("accepted") is True or j.get("is_accepted") is True:
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


def test_vehicle_paywall_user_max_1(client_user):
    _ensure_consent(client_user)

    r1 = client_user.post("/vehicles", json={
        "vin": "WVWZZZ1JZXW000001",
        "make": "VW",
        "model": "Golf",
        "year": 2020,
        "accident_status": "unknown",
    })
    assert r1.status_code == 200, r1.text
    vid = r1.json()["id"]

    r2 = client_user.post("/vehicles", json={
        "vin": "WVWZZZ1JZXW000002",
        "make": "VW",
        "model": "Golf",
        "year": 2021,
        "accident_status": "unknown",
    })
    assert r2.status_code == 402, r2.text

    r3 = client_user.get(f"/vehicles/{vid}")
    assert r3.status_code == 200, r3.text


def test_vehicle_object_level_forbidden(client_user, client_vip):
    _ensure_consent(client_vip)
    _ensure_consent(client_user)

    r = client_vip.post("/vehicles", json={
        "vin": "JH4KA9650MC000001",
        "make": "Acura",
        "model": "Legend",
        "year": 1991,
        "accident_status": "unknown",
    })
    assert r.status_code == 200, r.text
    vid = r.json()["id"]

    r2 = client_user.get(f"/vehicles/{vid}")
    assert r2.status_code == 403, r2.text


def test_entries_required_fields_422(client_vip):
    _ensure_consent(client_vip)

    r = client_vip.post("/vehicles", json={
        "vin": "WDB12345678900001",
        "make": "Mercedes",
        "model": "W123",
        "year": 1982,
        "accident_status": "unknown",
    })
    assert r.status_code == 200, r.text
    vid = r.json()["id"]

    bad = client_vip.post(f"/vehicles/{vid}/entries", json={
        "date": "2026-02-01",
        "entry_type": "service",
        "performed_by": "Fachwerkstatt"
    })
    assert bad.status_code == 422, bad.text
'@
  $dir = Split-Path -Parent $testPath
  if (!(Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
  Write-Utf8NoBom $testPath $test
}

Write-Host "OK: vehicles.py import+newline fixed, main.py wired, tests created."