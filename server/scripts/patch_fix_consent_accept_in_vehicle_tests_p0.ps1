# server/scripts/patch_fix_consent_accept_in_vehicle_tests_p0.ps1
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

import datetime as dt
import uuid
from contextlib import contextmanager
from typing import Any, Dict, Optional, Tuple

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


def _deep_find_version(obj: Any) -> Optional[str]:
    if isinstance(obj, dict):
        for k in ("version", "current_version", "consent_version"):
            if k in obj and obj[k] is not None:
                return str(obj[k])
        for k, v in obj.items():
            if isinstance(k, str) and "version" in k.lower() and v is not None:
                return str(v)
        for v in obj.values():
            r = _deep_find_version(v)
            if r:
                return r
    if isinstance(obj, list):
        for it in obj:
            r = _deep_find_version(it)
            if r:
                return r
    return None


def _deep_find_key(obj: Any, needle: str) -> Optional[Any]:
    n = needle.lower()
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(k, str) and n == k.lower():
                return v
        for k, v in obj.items():
            if isinstance(k, str) and n in k.lower():
                if v is not None:
                    return v
        for v in obj.values():
            r = _deep_find_key(v, needle)
            if r is not None:
                return r
    if isinstance(obj, list):
        for it in obj:
            r = _deep_find_key(it, needle)
            if r is not None:
                return r
    return None


def _openapi(client) -> Dict[str, Any]:
    # /openapi.json kann je nach env deaktiviert sein; app.openapi() ist in tests immer da.
    try:
        return client.app.openapi()
    except Exception:
        return {}


def _resolve_ref(openapi: Dict[str, Any], ref: str) -> Dict[str, Any]:
    if not ref.startswith("#/"):
        return {}
    parts = ref.lstrip("#/").split("/")
    cur: Any = openapi
    for p in parts:
        if isinstance(cur, dict) and p in cur:
            cur = cur[p]
        else:
            return {}
    return cur if isinstance(cur, dict) else {}


def _schema_merge(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(a)
    # required
    ra = out.get("required", [])
    rb = b.get("required", [])
    req = []
    for x in (ra if isinstance(ra, list) else []):
        if x not in req:
            req.append(x)
    for x in (rb if isinstance(rb, list) else []):
        if x not in req:
            req.append(x)
    if req:
        out["required"] = req
    # properties
    pa = out.get("properties", {}) if isinstance(out.get("properties", {}), dict) else {}
    pb = b.get("properties", {}) if isinstance(b.get("properties", {}), dict) else {}
    if pa or pb:
        out["properties"] = {**pa, **pb}
    return out


def _normalize_schema(openapi: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
    # ref
    if "$ref" in schema:
        return _normalize_schema(openapi, _resolve_ref(openapi, schema["$ref"]))
    # allOf
    if "allOf" in schema and isinstance(schema["allOf"], list):
        merged: Dict[str, Any] = {}
        for s in schema["allOf"]:
            if isinstance(s, dict):
                merged = _schema_merge(merged, _normalize_schema(openapi, s))
        # local overlay
        local = dict(schema)
        local.pop("allOf", None)
        local = _normalize_schema(openapi, local) if local else {}
        merged = _schema_merge(merged, local)
        return merged
    # oneOf/anyOf -> nimm erstes als MVP (wir retryen unten, falls 422)
    for k in ("oneOf", "anyOf"):
        if k in schema and isinstance(schema[k], list) and schema[k]:
            first = schema[k][0]
            if isinstance(first, dict):
                return _normalize_schema(openapi, first)
    return schema


def _get_accept_schema(openapi: Dict[str, Any]) -> Dict[str, Any]:
    paths = openapi.get("paths", {}) if isinstance(openapi.get("paths", {}), dict) else {}
    p = paths.get("/consent/accept", {}) if isinstance(paths.get("/consent/accept", {}), dict) else {}
    post = p.get("post", {}) if isinstance(p.get("post", {}), dict) else {}
    rb = post.get("requestBody", {}) if isinstance(post.get("requestBody", {}), dict) else {}
    content = rb.get("content", {}) if isinstance(rb.get("content", {}), dict) else {}
    appjson = content.get("application/json", {}) if isinstance(content.get("application/json", {}), dict) else {}
    schema = appjson.get("schema", {}) if isinstance(appjson.get("schema", {}), dict) else {}
    return _normalize_schema(openapi, schema)


def _guess_value(field: str, prop: Dict[str, Any], cur_obj: Any, version: Optional[str]) -> Any:
    fl = field.lower()

    # default / enum
    if "default" in prop:
        return prop["default"]
    if "enum" in prop and isinstance(prop["enum"], list) and prop["enum"]:
        return prop["enum"][0]

    if "version" in fl:
        return version or "v1"

    # häufige Zustimmung
    if "accept" in fl or "agree" in fl or fl in ("accepted", "is_accepted", "consent"):
        t = prop.get("type")
        if t == "string":
            return "true"
        return True

    # id aus /consent/current ziehen, wenn Feld nach id aussieht
    if fl.endswith("_id") or fl == "id":
        v = _deep_find_key(cur_obj, field)
        if v is None:
            v = _deep_find_key(cur_obj, "id")
        if v is not None:
            return v
        return str(uuid.uuid4())

    if "timestamp" in fl or fl.endswith("_at"):
        return dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

    # type-basiert
    t = prop.get("type")
    if t == "boolean":
        return True
    if t in ("integer", "number"):
        return 1
    if t == "array":
        return []
    if t == "object":
        return {}
    return "test"


def _build_payload(schema: Dict[str, Any], cur_obj: Any, version: Optional[str]) -> Dict[str, Any]:
    required = schema.get("required", [])
    props = schema.get("properties", {}) if isinstance(schema.get("properties", {}), dict) else {}
    payload: Dict[str, Any] = {}

    if isinstance(required, list) and required:
        for f in required:
            if not isinstance(f, str):
                continue
            prop = props.get(f, {})
            if not isinstance(prop, dict):
                prop = {}
            payload[f] = _guess_value(f, prop, cur_obj, version)
        return payload

    # fallback minimal
    if version:
        return {"version": version, "accepted": True}
    return {"accepted": True}


def _ensure_consent(client) -> None:
    st = client.get("/consent/status")
    if st.status_code == 200:
        j = st.json()
        if isinstance(j, dict) and (j.get("accepted") is True or j.get("is_accepted") is True):
            return

    cur_obj: Any = {}
    cur = client.get("/consent/current")
    if cur.status_code == 200:
        try:
            cur_obj = cur.json()
        except Exception:
            cur_obj = {}

    version = _deep_find_version(cur_obj)

    openapi = _openapi(client)
    schema = _get_accept_schema(openapi)
    payload = _build_payload(schema, cur_obj, version)

    r = client.post("/consent/accept", json=payload, headers={"Idempotency-Key": str(uuid.uuid4())})
    if r.status_code in (200, 204, 409):
        return

    # Retry-Strategie: manchmal heißt das Feld anders -> versuche mit verbreiteten Alternativen
    fallbacks = []
    if version:
        fallbacks.append({"version": version, "accepted": True})
        fallbacks.append({"version": version, "is_accepted": True})
        fallbacks.append({"version": version, "agree": True})
    fallbacks.append({"accepted": True})
    fallbacks.append({"is_accepted": True})
    fallbacks.append({"agree": True})

    for fb in fallbacks:
        r2 = client.post("/consent/accept", json=fb, headers={"Idempotency-Key": str(uuid.uuid4())})
        if r2.status_code in (200, 204, 409):
            return

    raise AssertionError(f"consent accept failed: {r.status_code} {r.text} | payload={payload}")


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
Write-Host "OK: vehicles tests updated (consent accept payload via OpenAPI; never posts without body)."