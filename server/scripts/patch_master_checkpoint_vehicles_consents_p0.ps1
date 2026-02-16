# server/scripts/patch_master_checkpoint_vehicles_consents_p0.ps1
# RUN (Repo-Root):
#   pwsh -NoProfile -ExecutionPolicy Bypass -File .\server\scripts\patch_master_checkpoint_vehicles_consents_p0.ps1
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function _AsText { param([AllowNull()][object]$v) if($null -eq $v){""} else {[string]$v} }

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $repoRoot

$path = "docs/99_MASTER_CHECKPOINT.md"
if (!(Test-Path $path)) { throw "FEHLT: $path" }

$txt = (_AsText (Get-Content $path -Raw -ErrorAction SilentlyContinue)).Replace("`r`n","`n")

# Stand aktualisieren (best effort)
$txt = [regex]::Replace($txt, "(?m)^(Stand:\s*\*\*)\d{4}-\d{2}-\d{2}(\*\*\s*)$", "`${1}2026-02-08`${2}")

$marker = "feat/next10-vehicles-consent-e2e"
if ($txt -notmatch [regex]::Escape($marker)) {
  $insert = @"
✅ PR (offen): **Vehicles MVP + Consent Gate (Next10 E2E)**  
- Branch: `$marker  
- Neu: `/vehicles` Router (Create/List/Get), object-level, Moderator 403, VIN nur masked  
- Neu: `require_consent(db, actor)` Gate (deny-by-default, 403 consent_required)  
- Docs: Rights-Matrix korrigiert (Moderator nur Blog/News; Consent/Profile/Support = 403)

"@

  # Einfügen direkt nach "## Aktueller Stand (main)" wenn vorhanden, sonst oben nach Headerblock
  if ($txt -match "(?m)^##\s+Aktueller Stand\s*\(main\)\s*$") {
    $txt = [regex]::Replace($txt, "(?m)^(##\s+Aktueller Stand\s*\(main\)\s*\n)", "`${1}`n$insert", 1)
  } else {
    $txt = $insert + "`n" + $txt
  }
}

$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($path, $txt, $utf8NoBom)
Write-Host "OK: updated $path"