# server/scripts/patch_consent_gate.ps1
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Utf8NoBom {
  param([Parameter(Mandatory=$true)][string]$Path,
        [Parameter(Mandatory=$true)][string]$Content)

  $dir = Split-Path -Parent $Path
  if ($dir -and !(Test-Path $dir)) { New-Item -ItemType Directory -Path $dir | Out-Null }

  $enc = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($Path, $Content, $enc)
}

function Read-Utf8 {
  param([Parameter(Mandatory=$true)][string]$Path)
  return Get-Content -Path $Path -Raw -Encoding UTF8
}

function Write-LinesUtf8NoBom {
  param([Parameter(Mandatory=$true)][string]$Path,
        [Parameter(Mandatory=$true)][string[]]$Lines)
  $enc = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllLines($Path, $Lines, $enc)
}

function Find-FirstExisting {
  param([Parameter(Mandatory=$true)][string[]]$Candidates)
  foreach ($c in $Candidates) {
    if (Test-Path $c) { return $c }
  }
  return $null
}

function Skip-Docstring-Header {
  param([string[]]$Lines)

  $i = 0
  while ($i -lt $Lines.Count -and ($Lines[$i].Trim() -eq "" -or $Lines[$i].Trim().StartsWith("#"))) { $i++ }
  if ($i -ge $Lines.Count) { return 0 }

  $t = $Lines[$i].Trim()
  $quote = $null
  if ($t.StartsWith('"""')) { $quote = '"""' }
  elseif ($t.StartsWith("'''")) { $quote = "'''" }

  if ($quote -eq $null) { return 0 }

  # single-line docstring
  if ($t.Length -ge 6 -and $t.EndsWith($quote) -and $t -ne $quote) {
    return ($i + 1)
  }

  $i++
  while ($i -lt $Lines.Count) {
    if ($Lines[$i].Contains($quote)) { return ($i + 1) }
    $i++
  }
  return 0
}

function Insert-Import-IfMissing {
  param([string[]]$Lines,
        [string]$ImportLine)

  if ($Lines -contains $ImportLine) { return ,$Lines }

  $start = Skip-Docstring-Header -Lines $Lines
  $i = $start

  while ($i -lt $Lines.Count) {
    $trim = $Lines[$i].Trim()
    if ($trim -eq "" -or $trim.StartsWith("#") -or $trim.StartsWith("import ") -or $trim.StartsWith("from ")) {
      $i++
      continue
    }
    break
  }

  $new = @()
  if ($i -gt 0) { $new += $Lines[0..($i-1)] }
  $new += $ImportLine
  $new += $Lines[$i..($Lines.Count-1)]
  return ,$new
}

function Patch-GetCurrentUser {
  param([Parameter(Mandatory=$true)][string]$RbacPath)

  $lines = Get-Content -Path $RbacPath -Encoding UTF8

  if ($lines -match "consent_required") {
    Write-Host "SKIP: rbac.py scheint bereits Consent-Gate zu enthalten."
    return
  }

  # Imports sicherstellen
  $lines = Insert-Import-IfMissing -Lines $lines -ImportLine "import os"
  $lines = Insert-Import-IfMissing -Lines $lines -ImportLine "from typing import Optional"
  $lines = Insert-Import-IfMissing -Lines $lines -ImportLine "from starlette.requests import Request"
  $lines = Insert-Import-IfMissing -Lines $lines -ImportLine "from app.consent_store import has_consent, env_consent_version, env_db_path"

  # def get_current_user(...) finden
  $defIdx = -1
  for ($i=0; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -match "^\s*def\s+get_current_user\s*\(") { $defIdx = $i; break }
  }
  if ($defIdx -lt 0) { throw "Konnte def get_current_user(...) in $RbacPath nicht finden." }

  # Signatur-Ende finden (Zeile mit ') ... :')
  $sigEnd = -1
  for ($j=$defIdx; $j -lt $lines.Count; $j++) {
    if ($lines[$j] -match "\)\s*(->\s*.*)?\s*:\s*$") { $sigEnd = $j; break }
  }
  if ($sigEnd -lt 0) { throw "Konnte Ende der get_current_user-Signatur in $RbacPath nicht finden." }

  # request-Param hinzufügen (wenn noch nicht vorhanden)
  $sigBlock = ($lines[$defIdx..$sigEnd] -join "`n")
  if ($sigBlock -notmatch "\brequest\b") {
    if ($sigEnd -eq $defIdx) {
      # one-line def
      $lines[$defIdx] = $lines[$defIdx] -replace '\)\s*(->\s*.*)?\s*:\s*$', ', request: Optional[Request] = None)$1:'
    } else {
      # multi-line def: param vor schließender Klammer einfügen
      $indent = ($lines[$defIdx] -replace "^(\s*).*$", '$1') + "    "
      $paramLine = "${indent}request: Optional[Request] = None,"
      $before = @()
      if ($sigEnd -gt 0) { $before = $lines[0..($sigEnd-1)] }
      $after = $lines[$sigEnd..($lines.Count-1)]
      $lines = $before + @($paramLine) + $after
      $sigEnd += 1
    }
  }

  # Funktionskörper finden und erstes `return <var>` innerhalb von get_current_user finden
  $baseIndent = ($lines[$defIdx] -replace "^(\s*).*$", '$1')
  $bodyIndentLen = ($baseIndent.Length + 4)

  $returnIdx = -1
  $returnVar = $null

  for ($k=($sigEnd+1); $k -lt $lines.Count; $k++) {
    $line = $lines[$k]
    $trim = $line.Trim()

    # Ende der Funktion: weniger indent und nicht leer/comment
    $indentLen = ($line -replace "^(\s*).*$", '$1').Length
    if ($trim -ne "" -and -not $trim.StartsWith("#") -and $indentLen -le $baseIndent.Length) { break }

    if ($line -match "^\s*return\s+([A-Za-z_][A-Za-z0-9_]*)\s*$") {
      $returnIdx = $k
      $returnVar = $Matches[1]
      break
    }
  }

  if ($returnIdx -lt 0 -or -not $returnVar) {
    throw "Konnte kein einfaches 'return <var>' in get_current_user in $RbacPath finden (Patch-Anchor fehlt)."
  }

  # Consent-Gate Block einfügen (direkt vor return)
  $indent = ($lines[$returnIdx] -replace "^(\s*).*$", '$1')
  $gate = @(
    "${indent}# Consent-Gate: AGB + Datenschutz Pflicht (Version + Timestamp) — serverseitig enforced",
    "${indent}# Ohne gültige Zustimmung: kein produktiver Zugriff (alles außer /auth/*).",
    "${indent}if request is not None and not str(request.url.path).startswith(""/auth""):",
    "${indent}    required_version = env_consent_version()",
    "${indent}    db_path = env_db_path()",
    "${indent}    _uid = getattr($returnVar, ""user_id"", None) or getattr($returnVar, ""id"", None) or getattr($returnVar, ""uid"", None)",
    "${indent}    if _uid is not None and not has_consent(db_path, str(_uid), required_version):",
    "${indent}        raise HTTPException(status_code=403, detail={""code"": ""consent_required"", ""consent_version"": required_version})"
  )

  $lines = $lines[0..($returnIdx-1)] + $gate + $lines[$returnIdx..($lines.Count-1)]

  Write-LinesUtf8NoBom -Path $RbacPath -Lines $lines
  Write-Host "OK: rbac.py gepatcht: Consent-Gate in get_current_user()."
}

function Patch-Auth-AddConsentEndpoints {
  param([Parameter(Mandatory=$true)][string]$AuthPath)

  $text = Read-Utf8 -Path $AuthPath
  if ($text -match "Consent endpoints: AGB \+ Datenschutz Pflicht") {
    Write-Host "SKIP: Auth-Datei scheint bereits Consent-Endpunkte zu enthalten."
    return
  }

  # Router-Variable ermitteln (erstes "<name> = APIRouter")
  $m = [regex]::Match($text, '^[ \t]*(?<name>[A-Za-z_][A-Za-z0-9_]*)[ \t]*=[ \t]*APIRouter\b', [System.Text.RegularExpressions.RegexOptions]::Multiline)
  if (-not $m.Success) {
    throw "Konnte keine Router-Variable (= APIRouter) in $AuthPath finden."
  }
  $routerName = $m.Groups["name"].Value

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

try:
    _auth_prefix = getattr($routerName, "prefix", "") or ""
except Exception:
    _auth_prefix = ""

# Wenn der Router bereits prefix="/auth" trägt, reicht "/consent"; sonst "/auth/consent"
_CONSENT_PATH = "/consent" if str(_auth_prefix).startswith("/auth") else "/auth/consent"

@$routerName.get(_CONSENT_PATH)
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

@$routerName.post(_CONSENT_PATH)
def accept_consent(payload: dict = Body(...), user = Depends(get_current_user)):
    uid = _ltc_uid(user)
    if uid is None:
        raise HTTPException(status_code=401, detail={"code": "unauthenticated"})

    # Erwartet: agb=true und datenschutz=true (sonst 400)
    agb = bool(payload.get("agb"))
    ds = bool(payload.get("datenschutz"))
    if not (agb and ds):
        raise HTTPException(status_code=400, detail={"code": "consent_required", "consent_version": env_consent_version()})

    source = payload.get("source", "web")
    version = env_consent_version()
    accepted_at = record_consent(env_db_path(), str(uid), version, str(source))
    return {"ok": True, "consent_version": version, "accepted_at": accepted_at}
"@

  $new = $text + "`n`n" + $append
  Write-Utf8NoBom -Path $AuthPath -Content $new
  Write-Host "OK: Consent-Endpunkte an Auth-Router angehängt: $AuthPath"
}

# ---------------- main ----------------

$serverRoot = Split-Path -Parent $PSScriptRoot   # server/scripts -> server
$appDir = Join-Path $serverRoot "app"

# 1) consent_store.py (neu) wird erwartet (liegt im Repo nach Einfügen aus Chat)
$consentPath = Join-Path $appDir "consent_store.py"
if (!(Test-Path $consentPath)) {
  throw "Fehlt: $consentPath (bitte zuerst Datei aus Chat anlegen/committen)."
}

# 2) rbac.py patchen
$rbacCandidates = @(
  (Join-Path $appDir "rbac.py"),
  (Join-Path $appDir "core\rbac.py")
)
$rbacPath = Find-FirstExisting -Candidates $rbacCandidates
if (-not $rbacPath) { throw "Konnte rbac.py nicht finden. Kandidaten: $($rbacCandidates -join ', ')" }
Patch-GetCurrentUser -RbacPath $rbacPath

# 3) Auth-Datei finden und Consent-Endpunkte anhängen
$authCandidates = @(
  (Join-Path $appDir "auth\routes.py"),
  (Join-Path $appDir "auth\router.py"),
  (Join-Path $appDir "routers\auth.py"),
  (Join-Path $appDir "routers\auth_routes.py")
)
$authPath = Find-FirstExisting -Candidates $authCandidates
if (-not $authPath) { throw "Konnte Auth-Router-Datei nicht finden. Kandidaten: $($authCandidates -join ', ')" }
Patch-Auth-AddConsentEndpoints -AuthPath $authPath

Write-Host "FERTIG ✅"
Write-Host "Hinweis: Setze optional ENV:"
Write-Host "  `$env:LTC_CONSENT_VERSION='2026-01-27'"
Write-Host "  `$env:LTC_DB_PATH='.\\data\\app.db'"

