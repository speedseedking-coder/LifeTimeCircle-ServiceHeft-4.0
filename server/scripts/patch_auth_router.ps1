# Patch: hängt Auth-Router in app/main.py ein (idempotent)
# Nutzung: im server-Ordner ausführen:
#   pwsh -ExecutionPolicy Bypass -File .\scripts\patch_auth_router.ps1

$ErrorActionPreference = "Stop"

$serverRoot = Split-Path -Parent $PSScriptRoot
$mainPath = Join-Path $serverRoot "app\main.py"
$authInitPath = Join-Path $serverRoot "app\auth\__init__.py"

if (-not (Test-Path $mainPath)) {
  throw "Nicht gefunden: $mainPath"
}

# Sicherstellen, dass auth als Package importierbar ist
if (-not (Test-Path $authInitPath)) {
  New-Item -ItemType File -Path $authInitPath -Force | Out-Null
  Set-Content -Path $authInitPath -Value "# auth package marker`r`n" -Encoding UTF8
  Write-Host "OK: angelegt -> $authInitPath"
} else {
  Write-Host "OK: vorhanden -> $authInitPath"
}

$lines = Get-Content -Path $mainPath -Encoding UTF8

$importLine = "from app.auth.routes import router as auth_router"
$includeLine = "app.include_router(auth_router)"

$hasImport  = $lines | Where-Object { $_.Trim() -eq $importLine } | Measure-Object | Select-Object -ExpandProperty Count
$hasInclude = $lines | Where-Object { $_.Trim() -eq $includeLine } | Measure-Object | Select-Object -ExpandProperty Count

# Position von "app = FastAPI(" finden
$appIndex = -1
for ($i=0; $i -lt $lines.Count; $i++) {
  if ($lines[$i] -match '^\s*app\s*=\s*FastAPI\s*\(') { $appIndex = $i; break }
}
if ($appIndex -lt 0) {
  throw "In main.py kein 'app = FastAPI(' gefunden."
}

# Import einfügen (nach letztem Import vor app = FastAPI)
if ($hasImport -eq 0) {
  $insertAt = 0
  for ($i=0; $i -lt $appIndex; $i++) {
    if ($lines[$i] -match '^\s*(from|import)\s+') { $insertAt = $i + 1 }
  }

  $before = @()
  $after  = @()
  if ($insertAt -gt 0) { $before = $lines[0..($insertAt-1)] }
  $after = $lines[$insertAt..($lines.Count-1)]

  $newLines = @()
  $newLines += $before
  $newLines += $importLine
  # Leerzeile, falls zwischen Importblock und Code keine ist
  if ($after.Count -gt 0 -and $after[0].Trim().Length -ne 0) {
    $newLines += ""
  }
  $newLines += $after

  $lines = $newLines
  Write-Host "OK: Import eingefügt"
} else {
  Write-Host "OK: Import war schon drin"
}

# appIndex nach möglicher Einfügung neu bestimmen
$appIndex = -1
for ($i=0; $i -lt $lines.Count; $i++) {
  if ($lines[$i] -match '^\s*app\s*=\s*FastAPI\s*\(') { $appIndex = $i; break }
}
if ($appIndex -lt 0) {
  throw "Nach Patch kein 'app = FastAPI(' gefunden."
}

# Ende der FastAPI()-Klammer finden (für multiline FastAPI(...))
$balance = 0
$started = $false
$appEnd = $appIndex
for ($i=$appIndex; $i -lt $lines.Count; $i++) {
  $line = $lines[$i]
  foreach ($ch in $line.ToCharArray()) {
    if ($ch -eq '(') { $balance++; $started = $true }
    elseif ($ch -eq ')') { $balance-- }
  }
  $appEnd = $i
  if ($started -and $balance -le 0) { break }
}

# include_router einfügen (direkt nach app = FastAPI(...))
if ($hasInclude -eq 0) {
  $insertAt = $appEnd + 1

  $before = $lines[0..$appEnd]
  $after = @()
  if ($insertAt -le ($lines.Count-1)) { $after = $lines[$insertAt..($lines.Count-1)] }

  $newLines = @()
  $newLines += $before
  # Leerzeile, dann include
  $newLines += ""
  $newLines += $includeLine
  $newLines += ""
  $newLines += $after

  $lines = $newLines
  Write-Host "OK: app.include_router(...) eingefügt"
} else {
  Write-Host "OK: include_router war schon drin"
}

Set-Content -Path $mainPath -Value ($lines -join "`r`n") -Encoding UTF8
Write-Host "FERTIG: $mainPath gepatcht"
