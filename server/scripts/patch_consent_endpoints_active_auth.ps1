# server/scripts/patch_consent_endpoints_active_auth.ps1
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Read-Utf8([string]$Path) { Get-Content -Path $Path -Raw -Encoding UTF8 }

function Write-Utf8NoBom([string]$Path, [string]$Content) {
  $enc = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($Path, $Content, $enc)
}

$serverRoot = Split-Path -Parent $PSScriptRoot
$appDir = Join-Path $serverRoot "app"

# 1) aktive Auth-Datei finden: da wo verify route definiert ist
$pyFiles = Get-ChildItem -Path $appDir -Recurse -Filter "*.py" | Select-Object -ExpandProperty FullName

$pattern = 'post\(\s*["'']\/(auth\/)?verify["'']'
$hit = Select-String -Path $pyFiles -Pattern $pattern -List | Select-Object -First 1

if (-not $hit) {
  throw "Konnte keine Datei mit verify-Route finden (Pattern: $pattern)."
}

$authPath = $hit.Path
$text = Read-Utf8 $authPath

if ($text -match "Consent endpoints: AGB \+ Datenschutz Pflicht") {
  Write-Host "SKIP: Consent-Endpunkte bereits vorhanden in: $authPath"
  exit 0
}

# 2) Router-Variable ermitteln (erstes '<name> = APIRouter')
$m = [regex]::Match($text, '^[ \t]*(?<name>[A-Za-z_][A-Za-z0-9_]*)[ \t]*=[ \t]*APIRouter\b', [System.Text.RegularExpressions.RegexOptions]::Multiline)
if (-not $m.Success) {
  throw "Konnte keine Router-Variable (= APIRouter) in $authPath finden."
}
$routerName = $m.Groups["name"].Value

# 3) Consent-Pfad bestimmen:
# - Wenn Datei Routen wie "/auth/request" oder "/auth/verify" enthält -> Router hat wahrscheinlich KEIN prefix und Routen sind vollqualifiziert
# - Sonst -> Router hat vermutlich prefix="/auth" und Routen sind "/request" "/verify"
$consentPath = "/consent"
if ($text -match '["'']\/auth\/(request|verify|me)["'']') {
  $consentPath = "/auth/consent"
}

$append = @"
# --- Consent endpoints: AGB + Datenschutz Pflicht (Version + Timestamp) ---
# Speichert Version + Timestamp auditierbar. Keine PII / Tokens im Klartext loggen.
from fastapi import Body, Depends, HTTPException
from app.consent_store import record_consent, get_consent_status, env_consent_version, env_db_path
from app.rbac import get_current_user

def _ltc_uid(u):
    if u is None:
        return None
    if isinstance(u, dict):
        return u.get("user_id") or u.get("id") or u.get("uid")
    return getattr(u, "user_id", None) or getattr(u, "id", None) or getattr(u, "uid", None)

@$routerName.get("$consentPath")
def consent_status(user = Depends(get_current_user)):
    uid = _ltc_uid(user)
    if uid is None:
        raise HTTPException(status_code=401, detail={"code": "unauthenticated"})
    required_version = env_consent_version()
    st = get_consent_status(env_db_path(), str(uid), required_version)
    return {
        "required_version": st.required_version,
        "has_required": st.has_required,
        "latest_version": st.latest_version,
        "latest_accepted_at": st.latest_accepted_at,
        "latest_source": st.latest_source,
    }

@$routerName.post("$consentPath")
def accept_consent(payload: dict = Body(...), user = Depends(get_current_user)):
    uid = _ltc_uid(user)
    if uid is None:
        raise HTTPException(status_code=401, detail={"code": "unauthenticated"})

    agb = bool(payload.get("agb"))
    ds = bool(payload.get("datenschutz"))
    if not (agb and ds):
        raise HTTPException(status_code=400, detail={"code": "consent_required", "consent_version": env_consent_version()})

    source = payload.get("source", "web")
    version = env_consent_version()
    accepted_at = record_consent(env_db_path(), str(uid), version, str(source))
    return {"ok": True, "consent_version": version, "accepted_at": accepted_at}
"@

Write-Utf8NoBom -Path $authPath -Content ($text + "`n`n" + $append)
Write-Host "OK: Consent-Endpunkte angehängt an: $authPath"
Write-Host "HINWEIS: Uvicorn neu starten (Ctrl+C, dann erneut starten), damit OpenAPI aktualisiert."
