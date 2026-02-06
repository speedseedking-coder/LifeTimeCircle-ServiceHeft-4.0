Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Find-RepoRoot {
  param([string]$startDir)
  $dir = Resolve-Path $startDir
  while ($true) {
    if (Test-Path (Join-Path $dir ".git") -PathType Container) { return $dir }
    if (Test-Path (Join-Path $dir "docs") -PathType Container) { return $dir }
    $parent = Split-Path $dir -Parent
    if ($parent -eq $dir) { throw "Repo-Root nicht gefunden (kein .git und kein docs/ im Parent-Tree)." }
    $dir = $parent
  }
}

function Read-TextRaw {
  param([string]$path)
  Get-Content -LiteralPath $path -Raw
}

function Write-TextRaw {
  param([string]$path, [string]$text)
  Set-Content -LiteralPath $path -Value $text -Encoding utf8
}

function Patch-M06-Block {
  param([string]$text)

  # Robust: match "M-06" irgendwo in einer Modul-Überschrift, bis zur nächsten Modul-Überschrift.
  # Akzeptiert "### Modul M-06 | ..." oder "### M-06 | ..." etc.
  $blockPattern = '(?ms)^###\s+.*?\bM-06\b.*?(?=^###\s+|\z)'
  $m = [regex]::Match($text, $blockPattern)
  if (-not $m.Success) { return @{ changed=$false; text=$text; reason="M-06 Block nicht gefunden" } }

  $block = $m.Value
  $patched = $block

  # In M-06: Transfer/Übergabe & interner Verkauf ist VIP/DEALER only
  $patched = [regex]::Replace($patched, '\bvip/dealer/admin/superadmin\b', 'vip/dealer')
  $patched = [regex]::Replace($patched, '\bvip/dealer/admin\b', 'vip/dealer')
  $patched = [regex]::Replace($patched, '\bvip/dealer/superadmin\b', 'vip/dealer')

  if ($patched -eq $block) { return @{ changed=$false; text=$text; reason="M-06 Block gefunden, aber keine Rollenlisten zu patchen" } }

  $newText = $text.Substring(0, $m.Index) + $patched + $text.Substring($m.Index + $m.Length)
  return @{ changed=$true; text=$newText; reason="M-06 Rollenlisten auf vip/dealer only gesetzt" }
}

$root = Find-RepoRoot -startDir $PSScriptRoot
$path = Join-Path $root "docs/04_POLICY_INDEX.md"

if (-not (Test-Path $path -PathType Leaf)) {
  throw "Datei fehlt: $path"
}

$before = Read-TextRaw $path
$result = Patch-M06-Block -text $before

if ($result.changed) {
  Write-TextRaw $path $result.text
  Write-Host "OK: $($result.reason) -> $path"
} else {
  Write-Host "OK: Keine Änderungen nötig -> $path ($($result.reason))"
}

Write-Host ""
Write-Host "NEXT (prüfen):"
Write-Host "  rg -n `"M-06|Übergabe|Transfer|interner Verkauf|Sichtbar`" docs/04_POLICY_INDEX.md -n"
Write-Host "  rg -n `"vip/dealer/admin|vip/dealer/admin/superadmin|vip/dealer/superadmin`" docs/04_POLICY_INDEX.md -n"
exit 0
