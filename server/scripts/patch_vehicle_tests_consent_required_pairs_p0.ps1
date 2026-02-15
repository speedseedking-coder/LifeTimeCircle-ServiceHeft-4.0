# server/scripts/patch_vehicle_tests_consent_required_pairs_p0.ps1
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-RepoRoot {
  $dir = Get-Location
  for ($i = 0; $i -lt 15; $i++) {
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
if (!(Test-Path $testPath)) { throw "Fehlt: $testPath" }

# Read (raw)
$txt = Get-Content -Raw -Encoding UTF8 $testPath

# Normalize newlines for editing
$txt = $txt -replace "`r`n", "`n"

# Ensure import re exists
if ($txt -notmatch "(?m)^\s*import\s+re\s*$") {
  if ($txt -match "(?m)^\s*import\s+uuid\s*$") {
    $txt = [regex]::Replace($txt, "(?m)^\s*import\s+uuid\s*$", "import uuid`nimport re", 1)
  } elseif ($txt -match "(?m)^\s*import\s+datetime\s+as\s+dt\s*$") {
    $txt = [regex]::Replace($txt, "(?m)^\s*import\s+datetime\s+as\s+dt\s*$", "import datetime as dt`nimport re", 1)
  } else {
    # fallback: add at top after future import
    $txt = [regex]::Replace($txt, "(?m)^from __future__ import annotations\s*$", "from __future__ import annotations`n`nimport re", 1)
  }
}

# Ensure helper _extract_required_pairs exists (insert right before _ensure_consent)
if ($txt -notmatch "(?s)\ndef\s+_extract_required_pairs\(") {
  $helper = @'
def _extract_required_pairs(detail_text: str) -> Dict[str, str]:
    # erwartet u.a.: "Pflicht-Consents fehlen oder Version falsch: terms:v1, privacy:v1"
    pairs = re.findall(r"([a-zA-Z0-9_\-]+)\s*:\s*([a-zA-Z0-9_\-\.]+)", detail_text or "")
    out: Dict[str, str] = {}
    for k, v in pairs:
        out[str(k)] = str(v)
    return out

'@
  if ($txt -match "(?m)^def\s+_ensure_consent\(client\)\s*->\s*None\s*:") {
    $txt = [regex]::Replace(
      $txt,
      "(?m)^def\s+_ensure_consent\(client\)\s*->\s*None\s*:",
      $helper + "def _ensure_consent(client) -> None:",
      1
    )
  } else {
    throw "Konnte def _ensure_consent(client) -> None: nicht finden."
  }
}

# Replace _ensure_consent implementation (only the function body)
if ($txt -notmatch "(?s)def\s+_ensure_consent\(client\)\s*->\s*None\s*:") {
  throw "def _ensure_consent(...) nicht gefunden."
}
if ($txt -notmatch "(?s)\n\ndef\s+test_") {
  throw "Konnte Block-Ende nicht finden (erwarte danach 'def test_...')."
}

$newEnsure = @'
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

    # existing helper in file expects (schema, cur_obj, version)
    payload = _build_payload(schema, cur_obj, version)

    def _post(p: Dict[str, Any]) -> Any:
        return client.post("/consent/accept", json=p, headers={"Idempotency-Key": str(uuid.uuid4())})

    r = _post(payload)
    if r.status_code in (200, 204, 409):
        return

    # Parse required pairs from 400 detail
    detail_text = ""
    try:
        jj = r.json()
        d = jj.get("detail") if isinstance(jj, dict) else None
        detail_text = d if isinstance(d, str) else str(d)
    except Exception:
        detail_text = r.text

    required = _extract_required_pairs(detail_text)
    if required:
        mapping = dict(required)
        items = list(mapping.items())
        as_strings = [f"{k}:{v}" for k, v in items]

        # list-of-objects variants
        obj_key = [{"key": k, "version": v, "accepted": True} for k, v in items]
        obj_slug = [{"slug": k, "version": v, "accepted": True} for k, v in items]
        obj_kind = [{"kind": k, "version": v, "accepted": True} for k, v in items]
        obj_name = [{"name": k, "version": v, "accepted": True} for k, v in items]
        obj_id = [{"id": k, "version": v, "accepted": True} for k, v in items]
        obj_type = [{"type": k, "version": v, "accepted": True} for k, v in items]

        bases: list[Dict[str, Any]] = []
        b1 = dict(payload)
        if version and "version" not in b1:
            b1["version"] = version
        bases.append(b1)

        b2 = dict(b1)
        b2.pop("accepted", None)
        b2.pop("is_accepted", None)
        b2.pop("agree", None)
        bases.append(b2)

        candidates: list[Dict[str, Any]] = []

        # 1) try schema-driven property fill (best chance)
        props = schema.get("properties", {}) if isinstance(schema.get("properties", {}), dict) else {}
        for bk in bases:
            for pname, ps in props.items():
                if not isinstance(ps, dict):
                    continue
                t = ps.get("type")
                if t == "object":
                    candidates.append({**bk, pname: mapping})
                elif t == "array":
                    candidates.append({**bk, pname: as_strings})
                    candidates.append({**bk, pname: obj_key})
                    candidates.append({**bk, pname: obj_slug})
                    candidates.append({**bk, pname: obj_kind})
                    candidates.append({**bk, pname: obj_name})
                    candidates.append({**bk, pname: obj_id})
                    candidates.append({**bk, pname: obj_type})

        # 2) common fieldnames (fallback)
        keys = ["consents", "required_consents", "accepted_consents", "consent_versions", "consent", "items", "agreements"]
        for bk in bases:
            for kname in keys:
                candidates.append({**bk, kname: mapping})
                candidates.append({**bk, kname: as_strings})
                candidates.append({**bk, kname: obj_key})
                candidates.append({**bk, kname: obj_slug})
                candidates.append({**bk, kname: obj_kind})
                candidates.append({**bk, kname: obj_name})
                candidates.append({**bk, kname: obj_id})
                candidates.append({**bk, kname: obj_type})

            # 3) top-level mapping variants
            candidates.append({**bk, **mapping})
            flat_v = dict(bk)
            for ck, cv in items:
                flat_v[f"{ck}_version"] = cv
            candidates.append(flat_v)

            flat_accept = dict(bk)
            for ck, _cv in items:
                flat_accept[f"accept_{ck}"] = True
            candidates.append(flat_accept)

        for cand in candidates:
            rr = _post(cand)
            if rr.status_code in (200, 204, 409):
                return

    raise AssertionError(f"consent accept failed: {r.status_code} {r.text} | payload={payload}")
'@

# Replace from def _ensure_consent ... up to before first "\n\ndef test_"
$pattern = [regex]::new("(?s)def\s+_ensure_consent\(client\)\s*->\s*None\s*:\n.*?(?=\n\ndef\s+test_)", [System.Text.RegularExpressions.RegexOptions]::None)
if (!$pattern.IsMatch($txt)) {
  throw "Replace-Pattern für _ensure_consent nicht gefunden. Datei-Struktur unerwartet."
}
$txt2 = $pattern.Replace($txt, $newEnsure, 1)

# Restore Windows newlines to be polite on Windows working copy
$txt2 = $txt2 -replace "`n", "`r`n"

Write-Utf8NoBom $testPath $txt2
Write-Host "OK: test_vehicles_entries_api_p0.py patched (consent accept satisfies required terms/privacy versions)."