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
  return Get-Content -LiteralPath $path -Raw
}

function Write-TextRaw {
  param([string]$path, [string]$text)
  Set-Content -LiteralPath $path -Value $text -Encoding utf8
}

function Replace-InFile {
  param(
    [string]$path,
    [string]$pattern,
    [string]$replacement,
    [string]$label
  )
  if (-not (Test-Path $path -PathType Leaf)) { return $false }

  $before = Read-TextRaw $path
  $after  = [regex]::Replace($before, $pattern, $replacement)

  if ($after -ne $before) {
    Write-TextRaw $path $after
    $script:Changed.Add($path) | Out-Null
    Write-Host "OK: Patch: $label -> $path"
    return $true
  }
  return $false
}

function Patch-TransferModulePolicyIndex {
  param([string]$path)
  if (-not (Test-Path $path -PathType Leaf)) { return $false }

  $txt = Read-TextRaw $path

  # Nur Modul M-06 block patchen (keine globalen Ersetzungen!)
  $blockPattern = '(?ms)^###\s+Modul\s+M-06\s+\|\s+Verkauf/Übergabe-QR\s+&\s+Interner\s+Verkauf\s+\(VIP/Dealer\).*?(?=^###\s+Modul\s+M-\d+|\z)'
  $m = [regex]::Match($txt, $blockPattern)
  if (-not $m.Success) { return $false }

  $block = $m.Value
  $patched = $block

  # Transfer muss VIP/Dealer-only sein (admin/superadmin ausdrücklich NICHT)
  $patched = [regex]::Replace($patched, 'vip/dealer/admin\b', 'vip/dealer')
  $patched = [regex]::Replace($patched, 'vip/dealer/admin/superadmin\b', 'vip/dealer')
  $patched = [regex]::Replace($patched, 'vip/dealer/superadmin\b', 'vip/dealer')

  if ($patched -eq $block) { return $false }

  $newTxt = $txt.Substring(0, $m.Index) + $patched + $txt.Substring($m.Index + $m.Length)
  Write-TextRaw $path $newTxt
  $script:Changed.Add($path) | Out-Null
  Write-Host "OK: Patch: Transfer-Modul M-06 roles (vip/dealer only) -> $path"
  return $true
}

function Patch-PolicyIndex-AdminSuperadminSplit {
  param([string]$path)
  if (-not (Test-Path $path -PathType Leaf)) { return $false }

  $txt = Read-TextRaw $path
  $before = $txt

  # 1) Bullet "admin (SUPERADMIN)" -> "admin"
  $txt = [regex]::Replace($txt, '^- \*\*admin\s+\(SUPERADMIN\)\*\*:\s*', '- **admin**: ', [Text.RegularExpressions.RegexOptions]::Multiline)

  # 2) Hinweis entfernen: "admin wird ... als SUPERADMIN behandelt"
  $txt = [regex]::Replace(
    $txt,
    '(?ms)^\s*Hinweis:\s*„admin“\s+wird\s+im\s+System\s+als\s+\*\*SUPERADMIN\*\*\s+behandelt.*?\n\s*---\s*\n',
    "---`n"
  )

  # 3) Falls irgendwo "SUPERADMIN-Claim" auftaucht -> Rolle
  $txt = $txt -replace 'SUPERADMIN-Claim', 'superadmin'

  # 4) Rollenliste (Slash-Format) wo vorhanden: .../admin -> .../admin/superadmin
  # NUR wo explizit Core-Rollenliste gemeint ist (typische Schreibweise).
  $txt = [regex]::Replace($txt, 'public/user/vip/dealer/moderator/admin(?!/superadmin)\b', 'public/user/vip/dealer/moderator/admin/superadmin')

  if ($txt -ne $before) {
    Write-TextRaw $path $txt
    $script:Changed.Add($path) | Out-Null
    Write-Host "OK: Patch: Policy-Index admin≠superadmin (Altlogik raus) -> $path"
    return $true
  }
  return $false
}

$root = Find-RepoRoot -startDir $PSScriptRoot
$script:Changed = New-Object System.Collections.Generic.HashSet[string]
$docs = Join-Path $root "docs"

# A) Claim-Altlogik MUSS weg (superadmin ist Rolle, kein Claim)
$projectBrief = Join-Path $docs "00_PROJECT_BRIEF.md"
Replace-InFile -path $projectBrief `
  -pattern 'Hochrisiko\s+nur\s+mit\s+\*\*SUPERADMIN-Claim\*\*' `
  -replacement 'Hochrisiko nur durch **superadmin**' `
  -label '00_PROJECT_BRIEF: Claim -> Rolle (Satz)'

Replace-InFile -path $projectBrief `
  -pattern 'SUPERADMIN-Claim' `
  -replacement 'superadmin' `
  -label '00_PROJECT_BRIEF: Claim -> Rolle (Fallback)'

$backlog = Join-Path $docs "02_BACKLOG.md"
Replace-InFile -path $backlog `
  -pattern 'public/user/vip/dealer/moderator/admin\s*\+\s*SUPERADMIN-Claim' `
  -replacement 'public/user/vip/dealer/moderator/admin/superadmin' `
  -label '02_BACKLOG: Rollenmodell Claim -> superadmin'

Replace-InFile -path $backlog `
  -pattern 'SUPERADMIN-Claim' `
  -replacement 'superadmin' `
  -label '02_BACKLOG: Claim -> superadmin (Fallback)'

# B) Rollenlisten ergänzen (wo Core-Rollen im Slash-Format stehen)
$glossary = Join-Path $docs "06_TERMS_GLOSSARY.md"
Replace-InFile -path $glossary `
  -pattern 'public/user/vip/dealer/moderator/admin(?!/superadmin)\b' `
  -replacement 'public/user/vip/dealer/moderator/admin/superadmin' `
  -label '06_TERMS_GLOSSARY: Core-Rollen inkl. superadmin'

$rolesPolicy = Join-Path $docs "policies/ROLES_AND_PERMISSIONS.md"
Replace-InFile -path $rolesPolicy `
  -pattern 'public/user/vip/dealer/moderator/admin(?!/superadmin)\b' `
  -replacement 'public/user/vip/dealer/moderator/admin/superadmin' `
  -label 'policies/ROLES_AND_PERMISSIONS: Core-Rollen inkl. superadmin'

# C) Policy Index: admin(SUPERADMIN)-Altlogik raus + Transfer-Modul VIP/Dealer-only
$policyIndex = Join-Path $docs "04_POLICY_INDEX.md"
Patch-PolicyIndex-AdminSuperadminSplit -path $policyIndex | Out-Null
Patch-TransferModulePolicyIndex -path $policyIndex | Out-Null

# D) Optional: falls dein Patch-Skript vorher noch ein "policies/POLICY_INDEX.md" nutzt
$policyIndex2 = Join-Path $docs "policies/POLICY_INDEX.md"
if (Test-Path $policyIndex2 -PathType Leaf) {
  Patch-TransferModulePolicyIndex -path $policyIndex2 | Out-Null
  Patch-PolicyIndex-AdminSuperadminSplit -path $policyIndex2 | Out-Null
}

# Report
if ($script:Changed.Count -eq 0) {
  Write-Host "OK: Keine Änderungen nötig (keine Treffer für die Patches gefunden)."
} else {
  Write-Host ""
  Write-Host "OK: Geänderte Dateien:"
  $script:Changed | Sort-Object | ForEach-Object { Write-Host " - $_" }
}

Write-Host ""
Write-Host "NEXT (prüfen):"
Write-Host "  rg -n `"admin \(SUPERADMIN\)|als \*\*SUPERADMIN\*\* behandelt|SUPERADMIN-Claim|vip/dealer/admin`" docs -S"
exit 0
