Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$path = "docs/04_POLICY_INDEX.md"
if (-not (Test-Path $path -PathType Leaf)) { throw "Fehlt: $path" }

$before = Get-Content -LiteralPath $path -Raw

# Exakt die Zeile korrigieren (nur wenn sie genau so vorkommt)
$after = [regex]::Replace(
  $before,
  '(?m)^\s*-\s*Sichtbar:\s*vip/dealer/admin/superadmin\s*$',
  '- Sichtbar: vip/dealer'
)

if ($after -eq $before) {
  Write-Host "OK: Keine Änderung (Zeile nicht gefunden oder schon korrekt)."
  exit 0
}

Set-Content -LiteralPath $path -Value $after -Encoding utf8
Write-Host "OK: Korrigiert: '- Sichtbar: vip/dealer/admin/superadmin' -> '- Sichtbar: vip/dealer' in $path"
exit 0
