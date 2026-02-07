# server/scripts/patch_decisions_pr79_ci_guard.ps1
[CmdletBinding()]
param(
  [Parameter(Mandatory = $false)]
  [string]$Path = "docs/01_DECISIONS.md"
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

# idempotent: falls D-030 oder Text schon existiert, nichts tun
if ($raw -match "(?m)^\s*##\s*D-030:" -or $raw -match "CI Guard.*pytest" -or $raw -match "ci_guard_required_job_pytest\.ps1") {
  Write-Host "OK: Decisions enthält CI-Guard Eintrag bereits." -ForegroundColor Green
  exit 0
}

$block = @"

---

## D-030: CI Guard verhindert Drift/Rename des Required Checks `pytest`
**Status:** beschlossen  
**Warum:** Branch Protection required checks hängen am stabilen **Check-Run/Job-Namen** (`pytest`). Wenn der Job-Key/Name driftet/umbenannt wird, zeigt GitHub oft „Expected/Waiting“ und blockt Merges.  
**Konsequenz:**  
- CI führt vor Tests einen Guard aus: `server/scripts/ci_guard_required_job_pytest.ps1`  
- Guard bricht CI ab, wenn `jobs: -> pytest:` im Workflow fehlt (Fail-fast statt „hängen“)  
- Required Check bleibt stabil: Branch Protection strict=true + required `pytest`
"@

$patched = $raw.TrimEnd() + $block + "`n"
Set-Content -LiteralPath $Path -Value $patched -Encoding UTF8
Write-Host "OK: Decisions gepatcht (D-030 CI Guard hinzugefügt)." -ForegroundColor Green
exit 0
