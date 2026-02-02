Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-FileUtf8NoBom([string]$Path, [string]$Content) {
  $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($Path, $Content.Replace("`r`n","`n"), $utf8NoBom)
}

$scriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Path
$serverRoot = Split-Path -Parent $scriptDir
$mainPath   = Join-Path $serverRoot "app\main.py"

if (-not (Test-Path $mainPath)) { throw "FEHLT: $mainPath" }

# sanity: consent router file should exist
$consentRouterPath = Join-Path $serverRoot "app\routers\consent.py"
if (-not (Test-Path $consentRouterPath)) {
  throw "FEHLT: $consentRouterPath (Router-Datei existiert nicht)"
}

$src = Get-Content -Raw -Path $mainPath

if ($src -match "routers\.consent" -or $src -match "consent_router") {
  Write-Host "OK: consent router scheint bereits referenziert."
  exit 0
}

# backup
Copy-Item $mainPath "$mainPath.bak" -Force

# 1) Insert import
$importLine = "from app.routers.consent import router as consent_router"
if ($src -notmatch [regex]::Escape($importLine)) {
  # try after last "from app.routers." import
  $m = [regex]::Match($src, "(?ms)^from\s+app\.routers\..*?\r?\n(?!from\s+app\.routers\.)")
  if ($m.Success) {
    $idx = $m.Index + $m.Length
    $src = $src.Insert($idx, $importLine + "`n")
  } else {
    # fallback: after other imports block
    $m2 = [regex]::Match($src, "(?ms)^(import .*?\r?\n|from .*? import .*?\r?\n)+")
    if ($m2.Success) {
      $idx = $m2.Index + $m2.Length
      $src = $src.Insert($idx, $importLine + "`n")
    } else {
      $src = $importLine + "`n" + $src
    }
  }
}

# 2) Insert include_router
$includeLine = "app.include_router(consent_router)"
if ($src -notmatch [regex]::Escape($includeLine)) {
  # after last app.include_router(...)
  $m3 = [regex]::Match($src, "(?ms)(^.*app\.include_router\([^\)]*\).*\r?\n)(?!.*app\.include_router\()")
  if ($m3.Success) {
    $idx = $m3.Index + $m3.Length
    $src = $src.Insert($idx, $includeLine + "`n")
  } else {
    # fallback: after "app = FastAPI(...)" if present
    $m4 = [regex]::Match($src, "(?m)^app\s*=\s*FastAPI\(.*\)\s*\r?\n")
    if ($m4.Success) {
      $idx = $m4.Index + $m4.Length
      $src = $src.Insert($idx, $includeLine + "`n")
    } else {
      # last resort: append
      $src = $src.TrimEnd() + "`n`n" + $includeLine + "`n"
    }
  }
}

Write-FileUtf8NoBom -Path $mainPath -Content $src
Write-Host "OK: consent router import + include_router gepatcht:"
Write-Host " - $mainPath"
Write-Host "Backup: $mainPath.bak"
