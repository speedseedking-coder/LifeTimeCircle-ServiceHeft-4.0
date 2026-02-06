# Fix: main.py -> "return app" außerhalb Funktion reparieren
# - rückt den create_app()-Body korrekt ein
# Ausführen in: server\
#   pwsh -ExecutionPolicy Bypass -File .\scripts\fix_main_create_app_indent.ps1

$ErrorActionPreference = "Stop"

$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$main = Join-Path $root "app\main.py"

if (!(Test-Path $main)) {
  Write-Error "Nicht gefunden: $main"
  exit 1
}

$content = Get-Content -Raw -Path $main

# Newline erkennen (CRLF vs LF)
$nl = "`n"
if ($content -match "`r`n") { $nl = "`r`n" }

$lines = $content -split "`r?`n", 0, "RegexMatch"

# def create_app finden
$defIdx = -1
for ($i=0; $i -lt $lines.Count; $i++) {
  if ($lines[$i] -match '^\s*def\s+create_app\b') { $defIdx = $i; break }
}
if ($defIdx -lt 0) {
  Write-Error "Kein 'def create_app' in app/main.py gefunden."
  exit 1
}

# return app nach def finden
$retIdx = -1
for ($i=$defIdx+1; $i -lt $lines.Count; $i++) {
  if ($lines[$i] -match '^\s*return\s+app\s*$') { $retIdx = $i; break }
}
if ($retIdx -lt 0) {
  Write-Error "Kein 'return app' nach create_app gefunden."
  exit 1
}

# Body einrücken: alle nicht-leeren Zeilen zwischen def und return (inkl. return)
$indent = "    "  # 4 spaces
for ($i=$defIdx+1; $i -le $retIdx; $i++) {
  $line = $lines[$i]
  if ($line -match '^\s*$') { continue }                 # leer -> lassen
  if ($line -match '^\s+') { continue }                  # schon eingerückt -> lassen
  $lines[$i] = $indent + $line                            # sonst einrücken
}

$newContent = [string]::Join($nl, $lines)
Set-Content -Path $main -Value $newContent -Encoding UTF8

Write-Host "OK: create_app()-Einrückung repariert in $main"
