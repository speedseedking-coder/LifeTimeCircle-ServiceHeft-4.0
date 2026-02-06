# server/scripts/patch_public_qr_disclaimer_exact.ps1
# Setzt den Public-QR Disclaimer exakt (SoT) als single-line String (ohne Split/Trailing Spaces).
# Run:
#   cd server
#   pwsh -NoProfile -ExecutionPolicy Bypass -File .\scripts\patch_public_qr_disclaimer_exact.ps1

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$serverDir = Resolve-Path (Join-Path $scriptDir "..")
$target    = Join-Path $serverDir "app\public\routes.py"

if (-not (Test-Path $target)) {
  throw "Zieldatei nicht gefunden: $target"
}

$exact = 'Die Trust-Ampel bewertet ausschließlich die Dokumentations- und Nachweisqualität. Sie ist keine Aussage über den technischen Zustand des Fahrzeugs.'

$content = Get-Content -Path $target -Raw -Encoding UTF8

$pattern = '(?ms)^[ \t]*DISCLAIMER_TEXT[ \t]*=[ \t]*.*?(?=^[ \t]*class[ \t]+PublicQrResponse\b)'
$replacement = "DISCLAIMER_TEXT = `"$exact`"`r`n`r`n"

if ($content -notmatch 'DISCLAIMER_TEXT') {
  throw "DISCLAIMER_TEXT nicht gefunden in app/public/routes.py"
}

if ($content -match [regex]::Escape($replacement.Trim())) {
  Write-Host "OK: DISCLAIMER_TEXT ist bereits exakt gesetzt."
  exit 0
}

$new = [regex]::Replace($content, $pattern, $replacement)

if ($new -eq $content) {
  throw "Patch konnte nicht angewendet werden (Pattern hat nichts ersetzt). Bitte DISCLAIMER_TEXT-Block prüfen."
}

$bak = "$target.bak"
Copy-Item -Path $target -Destination $bak -Force
Set-Content -Path $target -Value $new -Encoding UTF8

Write-Host "OK: DISCLAIMER_TEXT exakt gesetzt."
Write-Host "Backup: $bak"
