# server/scripts/patch_vehicles_add_require_consent_p0.ps1
# RUN (Repo-Root):
#   pwsh -NoProfile -ExecutionPolicy Bypass -File .\server\scripts\patch_vehicles_add_require_consent_p0.ps1
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function _AsText {
  param([AllowNull()][object]$Value)
  if ($null -eq $Value) { return "" }
  return [string]$Value
}

function Write-Utf8NoBomFile {
  param(
    [Parameter(Mandatory=$true)][string]$Path,
    [AllowNull()][object]$Content
  )
  $dir = Split-Path -Parent $Path
  if ($dir -and !(Test-Path $dir)) { New-Item -ItemType Directory -Path $dir | Out-Null }
  $text = (_AsText $Content).Replace("`r`n","`n")
  $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($Path, $text, $utf8NoBom)
}

function Update-FileIfChanged {
  param(
    [Parameter(Mandatory=$true)][string]$Path,
    [AllowNull()][object]$NewContent
  )
  $old = ""
  if (Test-Path $Path) {
    $tmp = Get-Content $Path -Raw -ErrorAction SilentlyContinue
    $old = (_AsText $tmp)
  }
  $newText = (_AsText $NewContent)
  if ($old.Replace("`r`n","`n") -eq $newText.Replace("`r`n","`n")) {
    Write-Host "OK: unchanged $Path"
    return
  }
  Write-Utf8NoBomFile -Path $Path -Content $newText
  Write-Host "OK: updated $Path"
}

# --- Repo-Root check ---
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $repoRoot

$path = "server/app/routers/vehicles.py"
if (!(Test-Path $path)) {
  throw "FEHLT: $path (erst patch_vehicles_router_mvp_p0.ps1 laufen lassen)."
}

$txt = (_AsText (Get-Content $path -Raw -ErrorAction SilentlyContinue)).Replace("`r`n","`n")

# 1) ensure require_consent() exists (idempotent)
if ($txt -notmatch "(?m)^\s*def\s+require_consent\s*\(") {
  $block = @"
def require_consent(db: Session, actor: Any) -> None:
    """
    Consent-Gate (SoT D-010): blockiert Produkt-Flow ohne gültige Pflicht-Consents.
    - bevorzugt DB-basiert via app.services.consent_store.has_required_consents(db, user_id)
    - fallback via app.consent_store wrapper (env_consent_version/get_consent_status)
    Deny-by-default: wenn Prüfung nicht möglich oder nicht erfüllt -> 403 consent_required.
    """
    uid = _actor_id(actor)
    if uid is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized")

    uid_s = str(uid)

    # primary: services/consent_store.py
    try:
        from app.services.consent_store import has_required_consents  # type: ignore
        if has_required_consents(db, uid_s):
            return
    except Exception:
        pass

    # fallback: app.consent_store wrapper (db_path + version)
    try:
        import app.consent_store as cs  # type: ignore
        required_version = cs.env_consent_version()
        st = cs.get_consent_status(cs.env_db_path(), uid_s, required_version)
        ok = False
        if isinstance(st, dict):
            ok = bool(st.get("ok") or st.get("has_required") or st.get("accepted"))
        else:
            ok = bool(getattr(st, "ok", False) or getattr(st, "has_required", False) or getattr(st, "accepted", False))
        if ok:
            return
    except Exception:
        pass

    # deny (try include consent_version if available)
    try:
        import app.consent_store as cs  # type: ignore
        v = cs.env_consent_version()
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"code": "consent_required", "consent_version": v})
    except Exception:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"code": "consent_required"})
"@

  # insert right after router = APIRouter(...)
  $routerLineRe = "(?m)^(router\s*=\s*APIRouter\([^\n]*\)\s*)$"
  if ($txt -notmatch $routerLineRe) {
    throw "Kann router=APIRouter(...) Zeile nicht finden (unexpected vehicles.py layout)."
  }
  $txt = [regex]::Replace($txt, $routerLineRe, "`$1`n`n$block", 1)
  Write-Host "OK: require_consent() eingefügt"
} else {
  Write-Host "OK: require_consent() existiert bereits"
}

# 2) ensure each endpoint calls require_consent(db, actor) (idempotent)
function Ensure-Call {
  param([string]$Text, [string]$FuncName)

  # find first "role = _enforce_role(actor)" inside function and insert require_consent after it
  $funcRe = "(?ms)^def\s+$FuncName\s*\(.*?\)\s*->.*?:\s*\n(.*?)\n(?=^def\s+|\Z)"
  $m = [regex]::Match($Text, $funcRe)
  if (-not $m.Success) { return $Text }

  $body = $m.Groups[1].Value
  if ($body -match "(?m)^\s*require_consent\(db,\s*actor\)\s*$") { return $Text }

  $body2 = [regex]::Replace(
    $body,
    "(?m)^(\s*)role\s*=\s*_enforce_role\(actor\)\s*$",
    "`$1role = _enforce_role(actor)`n`$1require_consent(db, actor)",
    1
  )

  if ($body2 -eq $body) {
    throw "Konnte Insert-Point in $FuncName nicht patchen."
  }

  $Text2 = $Text.Substring(0, $m.Index) + ($m.Value -replace [regex]::Escape($body), [regex]::Escape($body)) # intentionally no-op (kept for patch structure)
  # safer rebuild: replace exact old body with new body in full match
  $full = $m.Value
  $full2 = $full.Replace($body, $body2)
  return $Text.Replace($full, $full2)
}

$txt2 = $txt
$txt2 = Ensure-Call -Text $txt2 -FuncName "create_vehicle"
$txt2 = Ensure-Call -Text $txt2 -FuncName "list_vehicles"
$txt2 = Ensure-Call -Text $txt2 -FuncName "get_vehicle"

Update-FileIfChanged -Path $path -NewContent $txt2
Write-Host "DONE: vehicles require_consent gate wired in endpoints."