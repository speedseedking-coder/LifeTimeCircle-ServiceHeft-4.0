# scripts/patch_docs_consistency.ps1
$ErrorActionPreference = "Stop"

function Write-Ok($msg) { Write-Host "OK: $msg" -ForegroundColor Green }
function Write-Warn($msg) { Write-Host "WARN: $msg" -ForegroundColor Yellow }

function Ensure-Dir([string]$path) {
  if (-not (Test-Path $path)) { New-Item -ItemType Directory -Path $path | Out-Null }
}

function Move-FolderOutOfDocs([string]$src, [string]$dst) {
  if (-not (Test-Path $src)) { return }
  Ensure-Dir (Split-Path $dst -Parent)
  if (Test-Path $dst) {
    throw "Ziel existiert bereits: $dst (bitte manuell prüfen/umbenennen)."
  }
  Move-Item -Force $src $dst
  Write-Ok "Verschoben: $src -> $dst"
}

function Replace-InFile([string]$path, [string]$pattern, [string]$replacement) {
  if (-not (Test-Path $path)) { return $false }
  $before = Get-Content -Raw -Encoding UTF8 $path
  $after  = [regex]::Replace($before, $pattern, $replacement)
  if ($before -ne $after) {
    Set-Content -Encoding UTF8 -NoNewline -Path $path -Value $after
    return $true
  }
  return $false
}

# Repo-Root check (muss aus Root laufen)
if (-not (Test-Path ".git")) {
  throw "Bitte aus dem Repo-Root ausführen (da wo .git liegt)."
}

# 1) Altpfade/Altversionen aus docs/ herausziehen (nicht löschen, nur archivieren)
Ensure-Dir "tools/archive"
Move-FolderOutOfDocs "docs/routine" "tools/archive/docs_routine"
Move-FolderOutOfDocs "docs/policies/KI_Agenten_Only_LTC_2026-3" "tools/archive/KI_Agenten_Only_LTC_2026-3"

# 2) Kanonische Docs an Checkpoint-FIX anpassen (gezielt, nicht global)
$changed = @()

# Transfer-Regel: vip/dealer/admin -> vip/dealer (nur in den bekannten Problemdateien)
$transferFiles = @(
  "docs/06_TERMS_GLOSSARY.md",
  "docs/07_CONTEXT_PACK.md",
  "docs/policies/AGENT_BRIEF.md"
)
foreach ($f in $transferFiles) {
  if (Replace-InFile $f "(?i)\bvip/dealer/admin\b" "vip/dealer") { $changed += $f }
}

# VIP-Gewerbe Freigabe: admin -> SUPERADMIN (gezielt)
$staffFiles = @(
  "docs/04_MODULE_CATALOG.md",
  "docs/07_CONTEXT_PACK.md",
  "docs/policies/AGENT_BRIEF.md",
  "docs/policies/POLICY_INDEX.md"
)
foreach ($f in $staffFiles) {
  if (Replace-InFile $f "(?i)Freigabe\s+nur\s+admin" "Freigabe nur SUPERADMIN") { $changed += $f }
  if (Replace-InFile $f "(?i)Freigabe\s+\*\*nur\s+admin\*\*" "Freigabe **nur SUPERADMIN**") { $changed += $f }
}

# Admin-Security-Baseline: Admin darf Transfer nicht erzeugen/widerrufen
if (Replace-InFile "docs/policies/ADMIN_SECURITY_BASELINE.md" "(?m)^\s*-\s*Übergabe-QR erstellen/widerrufen.*$" "- Übergabe-QR erstellen/widerrufen: **nur VIP/DEALER** (kein Admin-Write)") {
  $changed += "docs/policies/ADMIN_SECURITY_BASELINE.md"
}

# Audit Enums: actor_role um superadmin erweitern
if (Replace-InFile "docs/policies/AUDIT_SCOPE_AND_ENUMS.md" "actor_role\s*\(public\|user\|vip\|dealer\|moderator\|admin\)" "actor_role (public|user|vip|dealer|moderator|admin|superadmin)") {
  $changed += "docs/policies/AUDIT_SCOPE_AND_ENUMS.md"
}

# Module Spec Schema: Core-Rollenliste inkl. superadmin
if (Replace-InFile "docs/05_MODULE_SPEC_SCHEMA.md" "(?i)public/user/vip/dealer/moderator/admin\b" "public/user/vip/dealer/moderator/admin/superadmin") {
  $changed += "docs/05_MODULE_SPEC_SCHEMA.md"
}

# 3) Ergebnis
$changed = $changed | Sort-Object -Unique
if ($changed.Count -gt 0) {
  Write-Ok "Geänderte Dateien:"
  $changed | ForEach-Object { Write-Host " - $_" }
} else {
  Write-Warn "Keine Text-Patches angewendet (entweder schon korrekt oder Dateien fehlen)."
}

Write-Host ""
Write-Ok "Next: git add -A + rg-Checks + commit"
