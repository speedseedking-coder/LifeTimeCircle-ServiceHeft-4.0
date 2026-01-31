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

function Save-IfChanged {
  param([string]$path, [string]$before, [string]$after)
  if ($after -ne $before) {
    Write-TextRaw $path $after
    $script:Changed.Add($path) | Out-Null
    return $true
  }
  return $false
}

function Patch-GlobalRoleLists {
  param([string]$text)

  $t = $text

  # Core-Rollenlisten: überall wo admin in Slash-Listen steht -> superadmin ergänzen
  $t = [regex]::Replace($t, '\buser/vip/dealer/admin(?!/superadmin)\b', 'user/vip/dealer/admin/superadmin')
  $t = [regex]::Replace($t, '\bvip/dealer/admin(?!/superadmin)\b', 'vip/dealer/admin/superadmin')
  $t = [regex]::Replace($t, '\bpublic/user/vip/dealer/moderator/admin(?!/superadmin)\b', 'public/user/vip/dealer/moderator/admin/superadmin')

  return $t
}

function Patch-TransferBlockM06_VipDealerOnly {
  param([string]$text)

  # Patch nur im Modul-M-06 Block, damit wir nichts anderes kaputt machen.
  # Block beginnt bei "### Modul M-06" und endet vor dem nächsten "### Modul M-"
  $blockPattern = '(?ms)^###\s+Modul\s+M-06\b.*?(?=^###\s+Modul\s+M-\d+|\z)'
  $m = [regex]::Match($text, $blockPattern)
  if (-not $m.Success) { return $text }

  $block = $m.Value
  $patched = $block

  # Transfer/Übergabe muss vip/dealer only sein (kein admin/superadmin)
  $patched = [regex]::Replace($patched, '\bvip/dealer/admin/superadmin\b', 'vip/dealer')
  $patched = [regex]::Replace($patched, '\bvip/dealer/admin\b', 'vip/dealer')
  $patched = [regex]::Replace($patched, '\bvip/dealer/superadmin\b', 'vip/dealer')

  if ($patched -eq $block) { return $text }

  return $text.Substring(0, $m.Index) + $patched + $text.Substring($m.Index + $m.Length)
}

function Patch-RolesAndPermissions_SafeLineWise {
  param([string]$text)

  # In ROLES_AND_PERMISSIONS.md wollen wir superadmin ergänzen,
  # aber NICHT in Transfer/Übergabe/Verkauf-Zeilen rumfummeln.
  $lines = $text -split "`n", -1
  for ($i=0; $i -lt $lines.Count; $i++) {
    $line = $lines[$i]

    $isTransferLine = $line -match '(?i)(übergabe|transfer|verkauf|interner\s+verkauf)'
    if ($isTransferLine) { continue }

    # Ergänze superadmin in "vip/dealer/admin" Listen
    $line2 = [regex]::Replace($line, '\bvip/dealer/admin(?!/superadmin)\b', 'vip/dealer/admin/superadmin')
    $lines[$i] = $line2
  }

  return ($lines -join "`n")
}

$root = Find-RepoRoot -startDir $PSScriptRoot
$script:Changed = New-Object System.Collections.Generic.HashSet[string]
$docs = Join-Path $root "docs"

# --- A) docs/04_POLICY_INDEX.md: Rollenlisten konsistent + Transfer M-06 VIP/Dealer-only ---
$policyIndex = Join-Path $docs "04_POLICY_INDEX.md"
if (Test-Path $policyIndex -PathType Leaf) {
  $before = Read-TextRaw $policyIndex
  $after = $before

  # 1) superadmin in generischen Listen ergänzen
  $after = Patch-GlobalRoleLists -text $after

  # 2) Transfer-Modul M-06 hart auf vip/dealer only setzen (überschreibt ggf. globale Ergänzungen im Block)
  $after = Patch-TransferBlockM06_VipDealerOnly -text $after

  if (Save-IfChanged -path $policyIndex -before $before -after $after) {
    Write-Host "OK: Patch: 04_POLICY_INDEX.md (Rollenlisten + M-06 vip/dealer only)"
  }
}

# --- B) docs/policies/ROLES_AND_PERMISSIONS.md: vip/dealer/admin -> vip/dealer/admin/superadmin (ohne Transfer-Zeilen) ---
$rolesPerm = Join-Path $docs "policies/ROLES_AND_PERMISSIONS.md"
if (Test-Path $rolesPerm -PathType Leaf) {
  $before = Read-TextRaw $rolesPerm
  $after = $before

  $after = Patch-RolesAndPermissions_SafeLineWise -text $after
  $after = Patch-GlobalRoleLists -text $after

  if (Save-IfChanged -path $rolesPerm -before $before -after $after) {
    Write-Host "OK: Patch: policies/ROLES_AND_PERMISSIONS.md (superadmin ergänzt, Transfer-Zeilen unangetastet)"
  }
}

# --- Report ---
if ($script:Changed.Count -eq 0) {
  Write-Host "OK: Keine Änderungen nötig (keine relevanten Treffer)."
} else {
  Write-Host ""
  Write-Host "OK: Geänderte Dateien:"
  $script:Changed | Sort-Object | ForEach-Object { Write-Host " - $_" }
}

Write-Host ""
Write-Host "NEXT (prüfen):"
Write-Host "  rg -n `"vip/dealer/admin|user/vip/dealer/admin|admin \(SUPERADMIN\)|als \*\*SUPERADMIN\*\* behandelt|SUPERADMIN-Claim`" docs -S"
exit 0
