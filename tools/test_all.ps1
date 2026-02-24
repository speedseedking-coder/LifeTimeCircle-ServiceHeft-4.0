# tools/test_all.ps1
# LifeTimeCircle – ServiceHeft 4.0
# Ziel: deterministisch fail-fast (kein "False-Green")
# - Repo-Root BOM Gate (UTF-8 no BOM)
# - Repo-Root Encoding/Mojibake Gate (rg-basiert)
# - Backend: pytest
# - Web: npm ci + build
# - Web: mini-e2e (Playwright) standardmäßig AN, opt-out via LTC_SKIP_E2E=1

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Invoke-Step {
  param(
    [Parameter(Mandatory=$true)][string]$Name,
    [Parameter(Mandatory=$true)][scriptblock]$Script
  )

  Write-Host ""
  Write-Host "==> $Name"
  & $Script

  if ($LASTEXITCODE -ne 0) {
    throw "FAILED: $Name (exit=$LASTEXITCODE)"
  }

  Write-Host "OK: $Name"
}

function Invoke-BomScan {
  if (Get-Command python -ErrorAction SilentlyContinue) {
    & python ".\tools\bom_scan.py" --root "."
    return
  }
  if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 ".\tools\bom_scan.py" --root "."
    return
  }
  throw "Weder 'python' noch 'py' gefunden fuer BOM-Gate."
}

try {
  $repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
  Set-Location $repoRoot
  [Environment]::CurrentDirectory = $repoRoot

  Invoke-Step -Name "BOM gate (repo): python ./tools/bom_scan.py --root ." -Script {
    Invoke-BomScan
    if ($LASTEXITCODE -ne 0) { throw "BOM scan failed (exit=$LASTEXITCODE)" }
  }

  Invoke-Step -Name "Encoding gate (repo): node ./tools/mojibake_scan.js --root ." -Script {
    & node ".\tools\mojibake_scan.js" --root "."
    if ($LASTEXITCODE -ne 0) { throw "mojibake scan failed (exit=$LASTEXITCODE)" }
  }

  # Tests brauchen einen starken Secret-Key (>=16) für Export/Redaction/HMAC
  if (-not $env:LTC_SECRET_KEY -or $env:LTC_SECRET_KEY.Trim().Length -lt 16) {
    $env:LTC_SECRET_KEY = "dev_test_secret_key_32_chars_minimum__OK"
  }

  Invoke-Step -Name "Backend tests (server): poetry run pytest -q" -Script {
    Push-Location (Join-Path $repoRoot "server")
    try {
      & poetry run pytest -q
      if ($LASTEXITCODE -ne 0) { throw "pytest failed (exit=$LASTEXITCODE)" }
    } finally {
      Pop-Location
    }
  }

  Invoke-Step -Name "Web build (packages/web): npm ci + npm run build" -Script {
    Push-Location (Join-Path $repoRoot "packages/web")
    try {
      & npm ci --no-audit --fund=false
      if ($LASTEXITCODE -ne 0) { throw "npm ci failed (exit=$LASTEXITCODE)" }

      # sanity: tsc muss nach npm ci existieren (Windows/Linux)
      if ((Test-Path ".\node_modules\.bin\tsc.cmd") -or (Test-Path "./node_modules/.bin/tsc")) {
        & npx --no-install tsc -v | Out-Host
      } else {
        throw "tsc fehlt nach npm ci (packages/web/node_modules/.bin/tsc(.cmd))."
      }

      & npm run build
      if ($LASTEXITCODE -ne 0) { throw "npm run build failed (exit=$LASTEXITCODE)" }

      # Mini-E2E (Playwright): standardmäßig AN, opt-out via LTC_SKIP_E2E=1
      if ($env:LTC_SKIP_E2E -eq "1") {
        Write-Host ""
        Write-Host "==> Web e2e (packages/web): SKIP (set LTC_SKIP_E2E=1)"
      } else {
        & npm run e2e
        if ($LASTEXITCODE -ne 0) { throw "npm run e2e failed (exit=$LASTEXITCODE)" }
      }
    } finally {
      Pop-Location
    }
  }

  Write-Host ""
  Write-Host "ALL GREEN ✅"
  exit 0
}
catch {
  Write-Error $_
  exit 1
}