Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-FileUtf8NoBom([string]$Path, [string]$Content) {
  $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($Path, $Content.Replace("`r`n","`n"), $utf8NoBom)
}

$scriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Path
$serverRoot = Split-Path -Parent $scriptDir
$mainPath   = Join-Path $serverRoot "app\main.py"
$bakPath    = "$mainPath.bak"

if (-not (Test-Path $mainPath)) { throw "FEHLT: $mainPath" }

# 1) Restore from backup if present
if (Test-Path $bakPath) {
  Copy-Item $bakPath $mainPath -Force
  Write-Host "OK: main.py aus Backup wiederhergestellt: $bakPath -> $mainPath"
} else {
  throw "FEHLT: $bakPath (kein Backup vorhanden). Alternative: git restore app/main.py"
}

$src = Get-Content -Raw -Path $mainPath

$importLine  = "from app.routers.consent import router as consent_router"
$includeLine = "app.include_router(consent_router)"

# 2) Ensure import line (insert after last 'from app.routers.... router as ...' if possible)
if ($src -notmatch [regex]::Escape($importLine)) {
  $lines = $src -split "`n"
  $lastRouterImportIdx = -1
  for ($i=0; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -match "^\s*from\s+app\.routers\..*\s+import\s+router\s+as\s+.*") {
      $lastRouterImportIdx = $i
    }
  }

  if ($lastRouterImportIdx -ge 0) {
    $before = @()
    if ($lastRouterImportIdx -ge 0) { $before = $lines[0..$lastRouterImportIdx] }
    $after = @()
    if ($lastRouterImportIdx + 1 -lt $lines.Count) { $after = $lines[($lastRouterImportIdx+1)..($lines.Count-1)] }

    $lines = @($before + $importLine + $after)
  } else {
    # fallback: put at very top
    $lines = @($importLine) + $lines
  }

  $src = ($lines -join "`n")
  Write-Host "OK: consent_router import eingefügt"
} else {
  Write-Host "OK: consent_router import schon vorhanden"
}

# 3) Ensure include_router with correct indent (use indent of last existing app.include_router(...) line)
if ($src -notmatch [regex]::Escape($includeLine)) {
  $lines = $src -split "`n"

  $lastIncludeIdx = -1
  $indent = ""

  for ($i=0; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -match '^(\s*)app\.include_router\(') {
      $lastIncludeIdx = $i
      $indent = $matches[1]
    }
  }

  if ($lastIncludeIdx -lt 0) {
    throw "PATCH FAILED: Keine app.include_router(...) Zeilen gefunden in app/main.py"
  }

  $before = $lines[0..$lastIncludeIdx]
  $after = @()
  if ($lastIncludeIdx + 1 -lt $lines.Count) { $after = $lines[($lastIncludeIdx+1)..($lines.Count-1)] }

  $lines = @($before + ($indent + $includeLine) + $after)
  $src = ($lines -join "`n")

  Write-Host "OK: app.include_router(consent_router) mit korrekter Einrückung eingefügt"
} else {
  Write-Host "OK: app.include_router(consent_router) schon vorhanden"
}

Write-FileUtf8NoBom -Path $mainPath -Content $src
Write-Host "OK: geschrieben: $mainPath"
Write-Host "DONE"
