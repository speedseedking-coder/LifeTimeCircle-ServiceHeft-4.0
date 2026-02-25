# server/scripts/ltc_verify_p0_mojibake_next10.ps1
# Repo-Root safe. Read-mostly. Optional: redundanten Remote-Branch löschen.
#
# Usage:
#   pwsh -NoProfile -ExecutionPolicy Bypass -File .\server\scripts\ltc_verify_p0_mojibake_next10.ps1
#
# Optional:
#   pwsh -NoProfile -ExecutionPolicy Bypass -File .\server\scripts\ltc_verify_p0_mojibake_next10.ps1 -QuickOnly
#   pwsh -NoProfile -ExecutionPolicy Bypass -File .\server\scripts\ltc_verify_p0_mojibake_next10.ps1 -CleanupBranch "fix/mojibake-deterministic-gate"
#   pwsh -NoProfile -ExecutionPolicy Bypass -File .\server\scripts\ltc_verify_p0_mojibake_next10.ps1 -AllowDirty -SkipPull
#   pwsh -NoProfile -ExecutionPolicy Bypass -File .\server\scripts\ltc_verify_p0_mojibake_next10.ps1 -RunBomAllFiles

[CmdletBinding()]
param(
  [switch]$SkipPull,
  [switch]$AllowDirty,
  [switch]$QuickOnly,
  [switch]$RunBomAllFiles,
  [string]$CleanupBranch = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

function Info([string]$m) { Write-Host "INFO: $m" }
function Warn([string]$m) { Write-Host "WARN: $m" -ForegroundColor Yellow }
function Fail([string]$m) { throw "FAIL: $m" }
function Ok([string]$m)   { Write-Host "OK: $m" -ForegroundColor Green }

function Assert-Command([string]$name) {
  if (-not (Get-Command $name -ErrorAction SilentlyContinue)) { Fail "Missing command: $name" }
}

function Get-RepoRoot {
  Assert-Command git
  $root = (& git rev-parse --show-toplevel 2>$null) | Select-Object -First 1
  if (-not $root) { Fail "Not inside a git work tree (git rev-parse --show-toplevel failed)." }
  $p = $root.Trim()
  try { (Resolve-Path -LiteralPath $p).Path } catch { $p }
}

function Ensure-Root([string]$root) {
  Set-Location $root
  [Environment]::CurrentDirectory = $root
}

function Assert-WorkingTreeClean() {
  $porc = (& git status --porcelain) | Out-String
  if (-not [string]::IsNullOrWhiteSpace($porc)) {
    Write-Host "---- git status -sb ----" -ForegroundColor Yellow
    & git status -sb
    Write-Host "---- git status --porcelain ----" -ForegroundColor Yellow
    & git status --porcelain
    Fail "Working tree is NOT clean. Commit or discard changes first."
  }
  Ok "Working tree clean"
}

function Assert-OriginRemoteHealthy() {
  # D-031: echter origin + ls-remote muss funktionieren
  $originUrl = (& git remote get-url origin 2>$null) | Select-Object -First 1
  if (-not $originUrl) { Fail "origin remote missing (git remote get-url origin failed). STOP (D-031)." }

  $u = $originUrl.Trim()

  # blockiere lokale Pfade / '.' / file://
  if ($u -eq "." -or $u -match '^[A-Za-z]:\\' -or $u -match '^(file://|/)' ) {
    Fail "origin is not a real remote URL: '$u'. STOP (D-031)."
  }

  & git ls-remote --heads origin | Out-Null
  Ok "origin remote OK + git ls-remote --heads origin OK"
}

function Ensure-MainFastForward() {
  if ($SkipPull) { Warn "SkipPull set: not fetching/pulling." ; return }

  & git fetch --prune origin | Out-Null

  $hasMain = $true
  try { & git show-ref --verify --quiet "refs/heads/main" } catch { $hasMain = $false }

  if (-not $hasMain) {
    $hasOriginMain = $false
    try { & git show-ref --verify --quiet "refs/remotes/origin/main"; $hasOriginMain = $true } catch {}
    if (-not $hasOriginMain) { Fail "Neither local main nor origin/main exists. Cannot fast-forward." }

    & git branch main origin/main | Out-Null
    Ok "Created local branch main from origin/main"
  }

  & git switch main | Out-Null
  & git pull --ff-only origin main | Out-Null
  Ok "main fast-forwarded to origin/main"
}

function Assert-CIWorkflowHasMojibakeGate([string]$root) {
  $wf = Join-Path $root ".github/workflows/ci.yml"
  if (-not (Test-Path $wf)) { Fail "Missing workflow: $wf" }

  $txt = Get-Content -LiteralPath $wf -Raw -Encoding UTF8

  if ($txt -notmatch '(?ms)jobs:\s*.*\n\s*pytest:\s*') {
    Fail "CI workflow drift: jobs: pytest: missing (Required Check must be 'pytest')."
  }

  if ($txt -notmatch 'mojibake_scan\.js' -or $txt -notmatch 'node\s+tools\/mojibake_scan\.js\s+--root\s+\.' ) {
    Fail "CI workflow missing Mojibake gate invocation: node tools/mojibake_scan.js --root ."
  }

  Ok "CI workflow contains pytest job + Mojibake gate step"
}

function Run-MojibakeScan([string]$root) {
  Assert-Command node

  $scan = Join-Path $root "tools/mojibake_scan.js"
  if (-not (Test-Path $scan)) { Fail "Missing SoT scanner: $scan" }

  $artDir = Join-Path $root "artifacts"
  if (-not (Test-Path $artDir)) { New-Item -ItemType Directory -Path $artDir | Out-Null }

  $report = Join-Path $artDir "mojibake_report.jsonl"

  $out = & node $scan --root $root 2>&1
  $code = $LASTEXITCODE

  $out | Out-File -FilePath $report -Encoding UTF8

  $lineCount = 0
  if (Test-Path $report) { $lineCount = (Get-Content -LiteralPath $report -Encoding UTF8 | Measure-Object -Line).Lines }

  if ($code -eq 0) {
    Ok "Mojibake scan OK (0 hits). Report: artifacts/mojibake_report.jsonl (lines=$lineCount)"
    return
  }

  if ($code -eq 1) {
    Fail "Mojibake scan found hits (exit=1). See artifacts/mojibake_report.jsonl (lines=$lineCount). Fix-policy: only fix reported path/line/col."
  }

  Fail "Mojibake scan unexpected exit code: $code. Output written to artifacts/mojibake_report.jsonl"
}

function Run-BomScan([string]$root) {
  Assert-Command python

  $bom = Join-Path $root "tools/bom_scan.py"
  if (-not (Test-Path $bom)) { Fail "Missing BOM scanner: $bom" }

  & python $bom --root $root | Out-Null
  Ok "BOM scan OK (tracked-only default)"

  if ($RunBomAllFiles) {
    & python $bom --root $root --all-files | Out-Null
    Ok "BOM scan OK (--all-files)"
  }
}

function Assert-ExactPublicDisclaimer([string]$root) {
  $needle = "Die Trust-Ampel bewertet ausschließlich die Dokumentations- und Nachweisqualität. Sie ist keine Aussage über den technischen Zustand des Fahrzeugs."

  $paths = @(
    "packages/web/src/components/TrustAmpelDisclaimer.tsx",
    "packages/web/src/pages/PublicQrPage.tsx",
    "server/app/public/routes.py",
    "server/app/routers/public_site.py"
  )

  foreach ($rel in $paths) {
    $p = Join-Path $root $rel
    if (-not (Test-Path $p)) { Fail "Missing required file for disclaimer check: $rel" }
    $raw = Get-Content -LiteralPath $p -Raw -Encoding UTF8
    if ($raw -notlike "*$needle*") { Fail "Required public disclaimer text missing or altered in: $rel" }
  }

  Ok "Public disclaimer text present (exact sentence) in web + backend"
}

function Assert-Next10GatesWired([string]$root) {
  $vehicles   = Join-Path $root "server/app/routers/vehicles.py"
  $publicSite = Join-Path $root "server/app/routers/public_site.py"
  $publicQr   = Join-Path $root "server/app/public/routes.py"

  foreach ($p in @($vehicles, $publicSite, $publicQr)) {
    if (-not (Test-Path $p)) { Fail "Missing file: $p" }
  }

  $v = Get-Content -LiteralPath $vehicles -Raw -Encoding UTF8
  if ($v -notmatch 'detail\s*=\s*"consent_required"') { Fail "Vehicles consent gate missing: detail=`"consent_required`" not found in server/app/routers/vehicles.py" }
  if ($v -notmatch 'Depends\(\s*forbid_moderator\s*\)') { Fail "Vehicles moderator block missing: Depends(forbid_moderator) not found in vehicles router deps" }

  $ps = Get-Content -LiteralPath $publicSite -Raw -Encoding UTF8
  if ($ps -notmatch 'Depends\(\s*forbid_moderator\s*\)') { Fail "/public/site moderator block missing: Depends(forbid_moderator) not found" }

  $pq = Get-Content -LiteralPath $publicQr -Raw -Encoding UTF8
  if ($pq -notmatch 'Depends\(\s*forbid_moderator\s*\)') { Fail "/public/qr moderator block missing: Depends(forbid_moderator) not found" }

  Ok "Next10 gates wired (public/public_site moderator 403 + vehicles consent_required + moderator block)"
}

function Run-FullLocalSuite([string]$root) {
  $testAll = Join-Path $root "tools/test_all.ps1"
  $ist     = Join-Path $root "tools/ist_check.ps1"

  if (-not (Test-Path $testAll)) { Fail "Missing: tools/test_all.ps1" }
  if (-not (Test-Path $ist))     { Fail "Missing: tools/ist_check.ps1" }

  & $testAll
  Ok "tools/test_all.ps1 OK"

  & $ist
  Ok "tools/ist_check.ps1 OK"
}

function Cleanup-RemoteBranch([string]$branch) {
  if ([string]::IsNullOrWhiteSpace($branch)) { return }
  Assert-OriginRemoteHealthy

  $branch = $branch.Trim()

  $hit = $false
  try {
    $res = & git ls-remote --heads origin $branch
    if (-not [string]::IsNullOrWhiteSpace(($res | Out-String))) { $hit = $true }
  } catch {
    Fail "Cannot query remote branch via ls-remote: $branch"
  }

  if (-not $hit) { Ok "Remote branch not found (nothing to delete): $branch"; return }

  & git push origin --delete $branch | Out-Null
  Ok "Deleted remote branch: $branch"

  $localName = $branch
  if ($localName.StartsWith("refs/heads/")) { $localName = $localName.Substring("refs/heads/".Length) }

  $localExists = $true
  try { & git show-ref --verify --quiet ("refs/heads/" + $localName) } catch { $localExists = $false }

  if ($localExists) {
    & git branch -D $localName | Out-Null
    Ok "Deleted local branch: $localName"
  }
}

# ---- Main ----
$root = Get-RepoRoot
Ensure-Root $root

Info "RepoRoot: $root"

Assert-Command git
Assert-Command node
Assert-Command python

if (-not $AllowDirty) { Assert-WorkingTreeClean } else { Warn "AllowDirty set: skipping clean-tree enforcement." }

Assert-OriginRemoteHealthy
Ensure-MainFastForward

Assert-CIWorkflowHasMojibakeGate -root $root

Run-MojibakeScan -root $root
Run-BomScan -root $root
Assert-ExactPublicDisclaimer -root $root
Assert-Next10GatesWired -root $root

if (-not $QuickOnly) {
  Run-FullLocalSuite -root $root
} else {
  Warn "QuickOnly set: skipping tools/test_all.ps1 and tools/ist_check.ps1"
}

Cleanup-RemoteBranch -branch $CleanupBranch

Ok "DONE"