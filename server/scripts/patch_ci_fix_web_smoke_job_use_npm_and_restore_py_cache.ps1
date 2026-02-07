# server/scripts/patch_ci_fix_web_smoke_job_use_npm_and_restore_py_cache.ps1
# - Switches web_smoke_build job to use direct npm build (packages/web)
# - Restores actions/setup-python cache settings (pip) if missing
# Idempotent.

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$ciPath   = Join-Path $repoRoot ".github\workflows\ci.yml"

if (-not (Test-Path -LiteralPath $ciPath)) { throw "CI workflow not found: $ciPath" }

$raw = Get-Content -LiteralPath $ciPath -Raw
$lines = $raw -split "`r?`n"

$out = New-Object System.Collections.Generic.List[string]

$job = ""
$skipWebToolkitStep = $false

$inSetupPython = $false
$setupPythonHasCache = $false
$setupPythonInserted = $false

for ($i = 0; $i -lt $lines.Length; $i++) {
  $line = $lines[$i]

  # job header (2 spaces + name + :)
  if ($line -match '^\s{2}([A-Za-z0-9_]+):\s*$') {
    $job = $matches[1]
    $skipWebToolkitStep = $false
    $out.Add($line)
    continue
  }

  # ---- web_smoke_build: replace "Web build (toolkit)" step with npm build ----
  if ($job -eq "web_smoke_build") {
    if ($skipWebToolkitStep) {
      # stop skipping at next step start
      if ($line -match '^\s{6}-\s') {
        $skipWebToolkitStep = $false
        $i-- # re-process this line
      }
      continue
    }

    if ($line -match '^\s{6}- name:\s*Web build \(toolkit\)\s*$') {
      # emit replacement step
      $out.Add("      - name: Web build (packages/web)")
      $out.Add("        working-directory: packages/web")
      $out.Add("        run: |")
      $out.Add("          npm ci")
      $out.Add("          npm run build")

      # skip the following "run: pwsh ..." line(s) belonging to toolkit step
      $skipWebToolkitStep = $true
      continue
    }
  }

  # ---- pytest: restore setup-python cache lines if missing ----
  if ($job -eq "pytest") {
    if ($line -match '^\s{6}- name:\s*Setup Python\s*$') {
      $inSetupPython = $true
      $setupPythonHasCache = $false
      $setupPythonInserted = $false
      $out.Add($line)
      continue
    }

    if ($inSetupPython) {
      # leaving the step at next "- " (same indent)
      if ($line -match '^\s{6}-\s') {
        $inSetupPython = $false
        $out.Add($line)
        continue
      }

      if ($line -match '^\s{10}cache:\s*"pip"\s*$') { $setupPythonHasCache = $true }
      if ($line -match '^\s{10}cache-dependency-path:\s*server/poetry\.lock\s*$') { $setupPythonHasCache = $true }

      # insert right after python-version line if cache is missing
      if (-not $setupPythonInserted -and $line -match '^\s{10}python-version:\s*".*"\s*$') {
        $out.Add($line)

        # look ahead: if cache already present later in this step, don't add
        # (quick scan until next step)
        $hasLaterCache = $false
        for ($j = $i + 1; $j -lt $lines.Length; $j++) {
          if ($lines[$j] -match '^\s{6}-\s') { break }
          if ($lines[$j] -match '^\s{10}cache:\s*"pip"\s*$') { $hasLaterCache = $true; break }
        }

        if (-not $hasLaterCache) {
          $out.Add('          cache: "pip"')
          $out.Add('          cache-dependency-path: server/poetry.lock')
        }

        $setupPythonInserted = $true
        continue
      }
    }
  }

  $out.Add($line)
}

$new = ($out -join "`n").TrimEnd() + "`n"

if ($new -eq $raw) {
  Write-Host "OK: no changes needed." -ForegroundColor Green
  exit 0
}

Set-Content -LiteralPath $ciPath -Value $new -Encoding utf8NoBOM
Write-Host "OK: updated web_smoke_build step + restored setup-python cache (if missing) in $ciPath" -ForegroundColor Green
