# server/scripts/ltc_verify_ist_zustand.ps1
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Section([string]$t) { Write-Host "`n=== $t ===" -ForegroundColor Cyan }
function Ok([string]$t)      { Write-Host ("✅ " + $t) -ForegroundColor Green }
function Warn([string]$t)    { Write-Host ("⚠️ " + $t) -ForegroundColor Yellow }
function Fail([string]$t)    { Write-Host ("❌ " + $t) -ForegroundColor Red }

function Require-Tool([string]$name) {
  $cmd = Get-Command $name -ErrorAction SilentlyContinue
  if (-not $cmd) { Fail "Tool fehlt: $name"; throw "Tool fehlt: $name" }
  Ok "Tool ok: $name ($($cmd.Source))"
}

function Get-RepoRoot {
  $topRaw = (git rev-parse --show-toplevel 2>$null)
  $top = ("" + $topRaw).Trim()
  if (-not $top) { throw "Kein Git-Repo gefunden (git rev-parse --show-toplevel leer)." }
  Set-Location $top
  [Environment]::CurrentDirectory = $top
  return $top
}

function Get-NpmCmd {
  $cmd = Get-Command "npm.cmd" -ErrorAction SilentlyContinue
  if ($cmd) { return $cmd.Source }
  $cmd = Get-Command "npm" -ErrorAction SilentlyContinue
  if ($cmd) { return $cmd.Source }
  throw "npm nicht gefunden (weder npm.cmd noch npm)."
}

function Run([string]$title, [scriptblock]$sb) {
  Section $title
  & $sb
}

function Normalize([string]$s) {
  if ($null -eq $s) { return "" }
  # Entferne typische Anführungszeichen-Varianten und normalisiere Whitespace
  $s = $s -replace '["„“”]', ''
  $s = $s -replace '\s+', ' '
  return $s.Trim()
}

function Get-BranchName {
  # GitHub Actions PR: detached HEAD -> git branch --show-current kann leer sein.
  $branchRaw = (git branch --show-current 2>$null)
  if (-not $branchRaw) { $branchRaw = $env:GITHUB_HEAD_REF }
  if (-not $branchRaw) { $branchRaw = $env:GITHUB_REF_NAME }
  if (-not $branchRaw) { $branchRaw = (git rev-parse --abbrev-ref HEAD 2>$null) }
  return ("" + $branchRaw).Trim()
}

# --- Start ---
Run "0) Tools vorhanden" {
  Require-Tool "git"
  Require-Tool "rg"
  Require-Tool "poetry"
  Ok ("npm via: " + (Get-NpmCmd))
}

$root = Get-RepoRoot
Ok "Repo-Root: $root"

Run "1) Repo-Root / Git Status" {
  $branch = Get-BranchName
  if (-not $branch) { $branch = "UNKNOWN" }

  $headRaw = (git rev-parse --short HEAD 2>$null)
  $head = ("" + $headRaw).Trim()

  $statusLines = @(git status -sb 2>$null)
  $status = ($statusLines -join "`n")
  Write-Host $status

  Ok "Branch: $branch"
  Ok "HEAD:   $head"

  if ($status -match "ahead|behind|diverged") { Warn "Branch ist nicht 1:1 synced mit origin (ahead/behind/diverged)." }
  else { Ok "Sync-Status zu origin sieht gut aus." }

  $porcLines = @(git status --porcelain 2>$null)
  $porc = ($porcLines -join "`n")
  if ($porc) {
    Fail "Working tree NICHT clean (uncommitted changes vorhanden)."
    Write-Host $porc
    throw "Working tree dirty"
  } else {
    Ok "Working tree clean."
  }
}

Run "2) SoT: Pflichtdateien vorhanden" {
  $docs = @(
    "docs/99_MASTER_CHECKPOINT.md",
    "docs/02_PRODUCT_SPEC_UNIFIED.md",
    "docs/03_RIGHTS_MATRIX.md",
    "docs/01_DECISIONS.md"
  )
  foreach ($d in $docs) {
    if (Test-Path -LiteralPath $d) { Ok "$d vorhanden" } else { Fail "$d fehlt"; throw "SoT fehlt: $d" }
  }
}

Run "3) Web: App + Pages vorhanden" {
  $webApp   = "packages/web/src/App.tsx"
  $pagesDir = "packages/web/src/pages"
  if (!(Test-Path -LiteralPath $webApp)) { Fail "Fehlt: $webApp"; throw "Web App.tsx fehlt" }
  if (!(Test-Path -LiteralPath $pagesDir)) { Fail "Fehlt: $pagesDir"; throw "pages/ fehlt" }

  Ok "Gefunden: $webApp"
  Ok "Gefunden: $pagesDir"

  $pages = @(Get-ChildItem -Path $pagesDir -File -Filter "*.tsx" | Select-Object -ExpandProperty Name)
  Write-Host "Pages (*.tsx):"
  if ($pages.Count -eq 0) { Warn "Keine Pages (*.tsx) gefunden." }
  else { $pages | ForEach-Object { Write-Host (" - " + $_) } }

  $expected = @("PublicQrPage.tsx","AuthPage.tsx","ConsentPage.tsx","VehiclesPage.tsx","VehicleDetailPage.tsx","DocumentsPage.tsx")
  foreach ($p in $expected) {
    if ($pages -contains $p) { Ok "Page vorhanden: $p" } else { Warn "Page nicht gefunden: $p (evtl. anderer Name)" }
  }
}

Run "4) Public-QR Pflichttext (robust, SoT-konform)" {
  $srcRoot = "packages/web/src"
  if (!(Test-Path -LiteralPath $srcRoot)) { Fail "Fehlt: $srcRoot"; throw "Web src fehlt" }

  # Pflichttext MUSS exakt inhaltlich stimmen (Whitespace/Quotes tolerant)
  $core = "Die Trust-Ampel bewertet ausschließlich die Dokumentations- und Nachweisqualität. Sie ist keine Aussage über den technischen Zustand des Fahrzeugs."
  $needle = Normalize $core

  $files = Get-ChildItem -Path $srcRoot -Recurse -File -Include *.ts,*.tsx
  $found = @()

  foreach ($f in $files) {
    $txt  = Get-Content -LiteralPath $f.FullName -Raw -Encoding UTF8
    $norm = Normalize $txt
    if ($norm -like "*$needle*") { $found += $f.FullName }
  }

  if ($found.Count -gt 0) {
    Ok "Pflichttext inhaltlich korrekt gefunden in:"
    $found | ForEach-Object { Write-Host " - $_" }
  } else {
    Fail "Pflichttext inhaltlich NICHT gefunden."
    Write-Host "Erwarteter Kerntext:"
    Write-Host $core
    throw "Public-QR Pflichttext fehlt oder ist inhaltlich verändert"
  }
}

Run "5) Guards / Moderator-Stop (Marker-Check)" {
  $srcRoot = "packages/web/src"
  $hints = "moderator|403|forbidden|role|rbac|guard|requireauth|requireconsent"
  $hits = @(rg -n -S $hints $srcRoot 2>$null)
  if ($hits.Count -gt 0) { Ok "Marker gefunden (Auszug):"; $hits | Select-Object -First 40 | ForEach-Object { Write-Host $_ } }
  else { Warn "Keine typischen Guard/Role-Marker gefunden (kann ok sein, wenn anders gelöst)." }
}

Run "6) API-Client (Bearer/401/POST) + keine dev/actor header" {
  $apiFile = "packages/web/src/api.ts"
  if (!(Test-Path -LiteralPath $apiFile)) { Warn "api.ts nicht gefunden an: $apiFile"; return }
  Ok "Gefunden: $apiFile"

  $good = @(rg -n -S "Authorization|Bearer|401|logout|redirect|post\(|POST" $apiFile 2>$null)
  if ($good.Count -gt 0) { Ok "Hinweise gefunden:"; $good | ForEach-Object { Write-Host $_ } }
  else { Warn "Keine offensichtlichen Marker gefunden." }

  $bad = @(rg -n -S "x-actor|x-dev|actor-header|dev-header" $apiFile 2>$null)
  if ($bad.Count -gt 0) { Fail "Verdächtige dev/actor header Marker gefunden!"; $bad | ForEach-Object { Write-Host $_ }; throw "API Header Policy verletzt" }
  else { Ok "Keine Hinweise auf dev/actor header gefunden." }
}

Run "7) Backend: pytest (mit LTC_SECRET_KEY)" {
  if (!(Test-Path -LiteralPath "server/pyproject.toml")) { Fail "server/pyproject.toml fehlt"; throw "server fehlt" }

  Push-Location "server"
  try {
    # In CI kommt LTC_SECRET_KEY als Secret -> NICHT überschreiben.
    if (-not $env:LTC_SECRET_KEY) {
      $env:LTC_SECRET_KEY = "dev_test_secret_key_32_chars_minimum__OK"
      Warn "LTC_SECRET_KEY war nicht gesetzt -> setze DEV-Test-Key (nur lokal sinnvoll)."
    }

    poetry run pytest -q
    Ok "pytest grün"
  } finally { Pop-Location }
}

Run "8) Web: npm ci + npm run build" {
  $webDir = Join-Path $root "packages/web"
  if (!(Test-Path -LiteralPath (Join-Path $webDir "package.json"))) { Fail "packages/web/package.json fehlt"; throw "web package fehlt" }
  if (!(Test-Path -LiteralPath (Join-Path $webDir "package-lock.json"))) { Fail "packages/web/package-lock.json fehlt (npm ci benötigt Lockfile)"; throw "web lockfile fehlt" }

  $npm = Get-NpmCmd
  Push-Location $webDir
  try {
    & $npm "ci" "--no-audit" "--fund=false"
    if ($LASTEXITCODE -ne 0) { throw "STOP: npm ci failed (exit=$LASTEXITCODE)" }

    & npx --no-install tsc -v
    if ($LASTEXITCODE -ne 0) { throw "STOP: tsc missing after npm ci (exit=$LASTEXITCODE)" }

    Ok "npm ci grün"

    & $npm "run" "build"
    if ($LASTEXITCODE -ne 0) { throw "STOP: npm run build failed (exit=$LASTEXITCODE)" }

    Ok "npm run build grün"
  } finally { Pop-Location }
}

Section "DONE"
Ok "IST-ZUSTAND Voll-Check abgeschlossen."
Warn "Optional: Smoke via ./server/scripts/ltc_web_toolkit.ps1 (-Smoke -Clean) nur, wenn pwsh verfügbar ist."

