# Patch: export_servicebook router in app/main.py registrieren
# - Import hinzufügen: from app.routers.export_servicebook import router as export_servicebook_router
# - include_router hinzufügen: app.include_router(export_servicebook_router)
# - robust gegen doppelte Einträge

$ErrorActionPreference = "Stop"

$mainPath = Join-Path (Get-Location) "app\main.py"
if (!(Test-Path $mainPath)) {
  throw "main.py nicht gefunden: $mainPath (bitte im server\ Ordner ausführen)"
}

$text = Get-Content -Raw -Encoding UTF8 $mainPath

$importLine = "from app.routers.export_servicebook import router as export_servicebook_router"
$includeLine = "app.include_router(export_servicebook_router)"

# 1) Import einfügen (nach letztem app.routers Import)
if ($text -notmatch [regex]::Escape($importLine)) {
  $lines = Get-Content -Encoding UTF8 $mainPath
  $idx = -1
  for ($i = 0; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -match '^\s*from\s+app\.routers\.') { $idx = $i }
  }

  if ($idx -ge 0) {
    $before = $lines[0..$idx]
    $after  = @()
    if ($idx + 1 -lt $lines.Count) { $after = $lines[($idx+1)..($lines.Count-1)] }
    $newLines = @()
    $newLines += $before
    $newLines += $importLine
    $newLines += $after
    Set-Content -Path $mainPath -Value ($newLines -join "`r`n") -Encoding UTF8
  } else {
    # fallback: oben einfügen
    Set-Content -Path $mainPath -Value (($importLine + "`r`n") + $text) -Encoding UTF8
  }

  $text = Get-Content -Raw -Encoding UTF8 $mainPath
}

# 2) include_router einfügen (vor "return app" innerhalb create_app)
if ($text -notmatch [regex]::Escape($includeLine)) {
  $lines = Get-Content -Encoding UTF8 $mainPath

  $returnIdx = -1
  for ($i = 0; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -match '^\s*return\s+app\s*$') { $returnIdx = $i; break }
  }
  if ($returnIdx -lt 0) {
    throw "Konnte 'return app' in main.py nicht finden."
  }

  $indent = ""
  if ($lines[$returnIdx] -match '^(\s*)return\s+app\s*$') {
    $indent = $Matches[1]
  }

  $insertLine = $indent + $includeLine

  $newLines = @()
  for ($i = 0; $i -lt $lines.Count; $i++) {
    if ($i -eq $returnIdx) {
      $newLines += $insertLine
    }
    $newLines += $lines[$i]
  }

  Set-Content -Path $mainPath -Value ($newLines -join "`r`n") -Encoding UTF8
}

Write-Host "OK: Router export_servicebook registriert in $mainPath"
