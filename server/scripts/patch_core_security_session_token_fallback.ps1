Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Read-Utf8([string]$Path) {
  Get-Content -Path $Path -Raw -Encoding UTF8
}

function Write-Utf8NoBom([string]$Path, [string]$Content) {
  $enc = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($Path, $Content, $enc)
}

$serverRoot = Split-Path -Parent $PSScriptRoot
$target = Join-Path $serverRoot "app/core/security.py"

if (-not (Test-Path $target)) {
  throw "Nicht gefunden: $target"
}

$text = Read-Utf8 $target

if ($text -match "SESSION_TOKEN_FALLBACK_LTC") {
  Write-Host "SKIP: Patch bereits vorhanden in $target"
  exit 0
}

# 1) Helper vor get_current_actor einfügen
$needle = "def get_current_actor"
$idx = $text.IndexOf($needle)
if ($idx -lt 0) {
  throw "Konnte 'def get_current_actor' nicht finden in $target"
}

$helper = @"
# --- SESSION_TOKEN_FALLBACK_LTC ---
# Akzeptiert neben JWT (core.security) auch Auth-Session-Tokens (/auth/verify).
# Keine Tokens/PII loggen. org_id Fallback: user_id (single-tenant / own-scope).
def decode_session_token(token: str):
    try:
        from app.auth.settings import load_settings as _load_auth_settings
        from app.auth.service import resolve_me as _resolve_me
    except Exception:
        _deny(401, "unauthorized")

    try:
        auth_settings = _load_auth_settings()
        me = _resolve_me(auth_settings, token)
        if me is None:
            _deny(401, "unauthorized")

        # me kann tuple/list, dict oder Objekt sein – robust extrahieren
        user_id = None
        role = None

        if isinstance(me, (tuple, list)) and len(me) >= 2:
            user_id = me[0]
            role = me[1]
        elif isinstance(me, dict):
            user_id = me.get("user_id") or me.get("id") or me.get("uid")
            role = me.get("role")
        else:
            user_id = getattr(me, "user_id", None) or getattr(me, "id", None) or getattr(me, "uid", None)
            role = getattr(me, "role", None)

        if not user_id or not role:
            _deny(401, "unauthorized")

        # org_id: MVP fallback = user_id (Scope-Isolation pro Account)
        return Actor(subject_id=str(user_id), role=str(role), org_id=str(user_id))
    except HTTPException:
        raise
    except Exception:
        _deny(401, "unauthorized")

"@

$text2 = $text.Substring(0, $idx) + $helper + $text.Substring($idx)

# 2) get_current_actor: return decode_token(...) -> try/except + fallback
$pattern = [regex]::Escape("return decode_token(creds.credentials)")
if ($text2 -notmatch $pattern) {
  throw "Konnte die Zeile 'return decode_token(creds.credentials)' nicht finden (Patchpunkt fehlt/anders) in $target"
}

$replacement = @"
try:
        return decode_token(creds.credentials)
    except HTTPException as e:
        # SESSION_TOKEN_FALLBACK_LTC
        if getattr(e, "status_code", None) != 401:
            raise
        return decode_session_token(creds.credentials)
"@

# Achtung: Indentation – wir ersetzen die einzelne return-Zeile inkl. Einrückung
$text3 = $text2 -replace "(?m)^\s*return decode_token\(creds\.credentials\)\s*$", ("    " + ($replacement -replace "`r?`n", "`n    ").TrimEnd())

Write-Utf8NoBom -Path $target -Content $text3

Write-Host "OK: Session-Token-Fallback gepatcht: $target"
Write-Host "HINWEIS: Uvicorn neu starten, damit der Patch aktiv wird."
