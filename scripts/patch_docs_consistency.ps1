# scripts/patch_docs_consistency2.ps1
$ErrorActionPreference = "Stop"

function Write-Ok($msg) { Write-Host "OK: $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "WARN: $msg" -ForegroundColor Yellow }

function Patch-FileRaw([string]$path, [ScriptBlock]$patchFn) {
  if (-not (Test-Path $path)) { return $false }
  $before = Get-Content -Raw -Encoding UTF8 $path
  $after  = & $patchFn $before
  if ($before -ne $after) {
    Set-Content -Encoding UTF8 -NoNewline -Path $path -Value $after
    return $true
  }
  return $false
}

function Patch-FileLines([string]$path, [ScriptBlock]$patchLineFn) {
  if (-not (Test-Path $path)) { return $false }
  $lines = Get-Content -Encoding UTF8 $path
  $changed = $false
  for ($i=0; $i -lt $lines.Count; $i++) {
    $orig = $lines[$i]
    $new  = & $patchLineFn $orig
    if ($new -ne $orig) { $lines[$i] = $new; $changed = $true }
  }
  if ($changed) {
    Set-Content -Encoding UTF8 -Path $path -Value $lines
  }
  return $changed
}

# Repo-Root check
if (-not (Test-Path ".git")) {
  throw "Bitte aus dem Repo-Root ausführen (da wo .git liegt)."
}

$changed = New-Object System.Collections.Generic.List[string]

# 1) SUPERADMIN-Claim -> Rolle superadmin (kein Claim-Konzept)
$claimTargets = @(
  "docs/00_PROJECT_BRIEF.md",
  "docs/02_BACKLOG.md"
)
foreach ($f in $claimTargets) {
  if (Patch-FileRaw $f {
    param($t)
    $t = $t -replace "SUPERADMIN-Claim", "Rolle superadmin"
    $t = $t -replace "(?i)admin\s*\+\s*Rolle\s*superadmin", "admin + superadmin"
    $t
  }) { $changed.Add($f) }
}

# 2) Core-Rollenlisten überall auf superadmin erweitern (gezielt bekannte Stellen)
$coreRoleTargets = @(
  "docs/05_MODULE_SPEC_SCHEMA.md",
  "docs/06_TERMS_GLOSSARY.md"
)
foreach ($f in $coreRoleTargets) {
  if (Patch-FileRaw $f {
    param($t)
    # Slash-Listen
    $t = $t -replace "\bpublic/user/vip/dealer/moderator/admin\b", "public/user/vip/dealer/moderator/admin/superadmin"
    # Komma-Listen
    $t = $t -replace "\bpublic,\s*user,\s*vip,\s*dealer,\s*moderator,\s*admin\b", "public, user, vip, dealer, moderator, admin, superadmin"
    $t
  }) { $changed.Add($f) }
}

# 3) Transfer/Übergabe-Regel: vip/dealer/admin -> vip/dealer (nur dort, wo es um Transfer/Übergabe geht)
# 3a) docs/04_POLICY_INDEX.md: nur "Sichtbar/Sichtbar-nutzbar" Zeilen anpassen (nicht Vehicle/Create Zeilen)
if (Patch-FileLines "docs/04_POLICY_INDEX.md" {
  param($line)
  if ($line -match "^\s*-\s*Sichtbar" -and $line -match "vip/dealer/admin") {
    return ($line -replace "vip/dealer/admin", "vip/dealer")
  }
  return $line
}) { $changed.Add("docs/04_POLICY_INDEX.md") }

# 3b) docs/policies/ROLES_AND_PERMISSIONS.md: nur Zeilen, die Transfer/Übergabe/Verkauf enthalten
if (Patch-FileLines "docs/policies/ROLES_AND_PERMISSIONS.md" {
  param($line)
  if ($line -match "vip/dealer/admin" -and $line -match "(?i)(transfer|übergabe|verkauf|interner)") {
    return ($line -replace "vip/dealer/admin", "vip/dealer")
  }
  return $line
}) { $changed.Add("docs/policies/ROLES_AND_PERMISSIONS.md") }

# 4) Audit Enum: actor_role muss superadmin enthalten (falls vorhanden)
if (Patch-FileRaw "docs/policies/AUDIT_SCOPE_AND_ENUMS.md" {
  param($t)
  $t -replace "actor_role\s*\(public\|user\|vip\|dealer\|moderator\|admin\)", "actor_role (public|user|vip|dealer|moderator|admin|superadmin)"
}) { $changed.Add("docs/policies/AUDIT_SCOPE_AND_ENUMS.md") }

# Output
$uniq = $changed | Sort-Object -Unique
if ($uniq.Count -gt 0) {
  Write-Ok "Geänderte Dateien:"
  $uniq | ForEach-Object { Write-Host " - $_" }
} else {
  Write-Warn "Keine Änderungen (evtl. schon korrekt)."
}

Write-Host ""
Write-Ok "Next: rg-Checks + git add -A + commit"
