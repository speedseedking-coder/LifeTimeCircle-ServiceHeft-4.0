# server/scripts/patch_master_checkpoint_pr79_ci_guard.ps1
[CmdletBinding()]
param(
  [Parameter(Mandatory = $false)]
  [string]$Path = "docs/99_MASTER_CHECKPOINT.md"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Fail([string]$msg) {
  Write-Host "ERROR: $msg" -ForegroundColor Red
  exit 1
}

if (-not (Test-Path -LiteralPath $Path)) {
  Fail "Datei nicht gefunden: $Path (Repo-Root erwartet)"
}

$raw = Get-Content -LiteralPath $Path -Raw -Encoding UTF8

if ($raw -match "(?m)^\s*✅\s*PR\s*#79\b" -or $raw -match "CI:\s*harden required 'pytest' check \+ add guard") {
  Write-Host "OK: Master Checkpoint enthält PR #79 bereits." -ForegroundColor Green
  exit 0
}

$block = @"
✅ PR #79 **gemerged** (squash): `CI: harden required 'pytest' check + add guard` (#79)
- CI-Workflow bereinigt: keine doppelten Job-Keys; Jobs: `pytest` (required) + `web_build`
- Fail-fast Guard gegen Drift/Rename des Required Checks:
  - Script: `server/scripts/ci_guard_required_job_pytest.ps1`
  - CI-Step im `pytest` Job → bricht ab, wenn `jobs: -> pytest:` fehlt (sonst Branch-Protection hängt in „Expected/Waiting“)
- Ergebnis: Branch-Protection bleibt stabil (strict=true + required `pytest`) und ist lokal verifizierbar via:
  - `server/scripts/verify_ci_branch_protection.ps1`
"@

# Einfügen direkt nach der Überschrift "## Aktueller Stand (main)"
$pattern = "(?m)^## Aktueller Stand \(main\)\s*$"
if ($raw -notmatch $pattern) {
  Fail "Marker nicht gefunden: '## Aktueller Stand (main)' in $Path"
}

$patched = [regex]::Replace($raw, $pattern, "## Aktueller Stand (main)`n$block", 1)

# sauberes EOF newline
if ($patched -notmatch "(\r?\n)$") { $patched += "`n" }

Set-Content -LiteralPath $Path -Value $patched -Encoding UTF8
Write-Host "OK: Master Checkpoint gepatcht (PR #79 Note eingefügt)." -ForegroundColor Green
exit 0