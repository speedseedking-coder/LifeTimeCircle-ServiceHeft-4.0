# server/scripts/ltc_verify_ist_zustand.ps1
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Section([string]$t) { Write-Host "`n=== $t ===" -ForegroundColor Cyan }
function Ok([string]$t)      { Write-Host "✅ $t" -ForegroundColor Green }
function Warn([string]$t)    { Write-Host "⚠️ $t" -ForegroundColor Yellow }
function Fail([string]$t)    { Write-Host "❌ $t" -ForegroundColor Red }

function Require-Tool([string]$name) {
  $cmd = Get-Command $name -ErrorAction SilentlyContinue
  if (-not $cmd) { Fail "Tool fehlt: $name"; throw "Tool fehlt: $name" }
  Ok "Tool ok: $name ($($cmd.Source))"
}

function Run([string]$title, [scriptblock]$sb) {
  Section $title
  & $sb
}

function Get-NpmCmd {
  $cmd = Get-Command "npm.cmd" -ErrorAction SilentlyContinue
  if ($cmd) { return $cmd.Source }
  $cmd = Get-Command "npm" -ErrorAction SilentlyContinue
  if ($cmd) { return $cmd.Source }
  throw "npm nicht gefunden (weder npm.cmd noch npm)."
}

Run "0) Tools vorhanden" {
  Require-Tool "git"
  Require-Tool "rg"
  Require-Tool "poetry"
  Ok ("npm via: " + (Get-NpmCmd))
}

Run "1) Repo-Root / Git Status" {
  $top = (git rev-parse --show-toplevel).Trim()
  if (-not $top) { throw "Kein Git-Repo gefunden (rev-parse leer)." }
  Ok "Repo-Root: $top"
  Set-Location $top

  $branch = (git branch --show-current).Trim()
  $head   = (git rev-parse --short HEAD).Trim()
  $status = (git status -sb)

  Write-Host $status
  Ok "Branch: $branch"
  Ok "HEAD:   $head"

  if ($status -match "ahead|behind|diverged") { Warn "Branch ist nicht 1:1 synced mit origin (ahead/behind/diverged)." }
  else { Ok "Sync-Status zu origin sieht gut aus." }

  $porc = (git status --porcelain)
  if ($porc) {
    Warn "Working tree NICHT clean (uncommitted changes vorhanden)."
    Write-Host $porc
  }
  else { Ok "Working tree clean." }
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
  $webApp = "packages/web/src/App.tsx"
  $pagesDir = "packages/web/src/pages"
  if (!(Test-Path -LiteralPath $webApp)) { Fail "Fehlt: $webApp"; throw "Web App.tsx fehlt" }
  if (!(Test-Path -LiteralPath $pagesDir)) { Fail "Fehlt: $pagesDir"; throw "pages/ fehlt" }
  Ok "Gefunden: $webApp"
  Ok "Gefunden: $pagesDir"

  $pages = @(Get-ChildItem -Path $pagesDir -File -Filter "*.tsx" | Select-Object -ExpandProperty Name)
  Write-Host "Pages (*.tsx):"
  if ($pages.Count -eq 0) { Warn "Keine Pages (*.tsx) gefunden." }
  else { $pages | ForEach-Object { Write-Host (" - " + $_) } }

  $expectedPages = @("PublicQrPage.tsx","AuthPage.tsx","ConsentPage.tsx","VehiclesPage.tsx","VehicleDetailPage.tsx","DocumentsPage.tsx")
  foreach ($p in $expectedPages) {
    if ($pages -contains $p) { Ok "Page vorhanden: $p" }
    else { Warn "Page nicht gefunden: $p (evtl. anderer Name)" }
  }
}

Run "4) Public-QR Pflichttext (robust, SoT-konform)" {
  $srcRoot = "packages/web/src"
  if (!(Test-Path -LiteralPath $srcRoot)) {
    Fail "Fehlt: $srcRoot"
    throw "Web src fehlt"
  }

  # SoT-Kerntest (INHALTLICH exakt, unabhängig von Quotes/Zeilenumbrüchen)
  $core = "Die Trust-Ampel bewertet ausschließlich die Dokumentations- und Nachweisqualität. Sie ist keine Aussage über den technischen Zustand des Fahrzeugs."

  function Normalize([string]$s) {
    if ($null -eq $s) { return "" }
    $s = $s -replace '["„“]', ''   # ASCII " sowie „ und “
    $s = $s -replace '\s+', ' '    # alle Whitespaces -> Single Space
    return $s.Trim()
  }

  $needle = Normalize $core
  $files  = Get-ChildItem -Path $srcRoot -Recurse -File -Include *.ts,*.tsx

  $found = @()
  foreach ($f in $files) {
    $txt = Get-Content -LiteralPath $f.FullName -Raw -Encoding UTF8
    $norm = Normalize $txt
    if ($norm -like "*$needle*") { $found += $f.FullName }
  }

  if ($found.Count -gt 0) {
    Ok "Pflichttext inhaltlich korrekt gefunden in:"
    $found | ForEach-Object { Write-Host " - $_" }
  }
  else {
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
    $env:LTC_SECRET_KEY = "dev_test_secret_key_32_chars_minimum__OK"
    poetry run pytest -q
    Ok "pytest grün"
  }
  finally { Pop-Location }
}

Run "8) Web: npm ci + npm run build" {
  if (!(Test-Path -LiteralPath "packages/web/package.json")) { Fail "packages/web/package.json fehlt"; throw "web package fehlt" }
  $npm = Get-NpmCmd
  Push-Location "packages/web"
  try {
    & $npm "ci" "--no-audit" "--no-fund"
    Ok "npm ci grün"
    & $npm "run" "build"
    Ok "npm run build grün"
  }
  finally { Pop-Location }
}

Section "DONE"
Ok "IST-ZUSTAND Voll-Check abgeschlossen."
Warn "Optional: Smoke via ./server/scripts/ltc_web_toolkit.ps1 (-Smoke -Clean) nur, wenn pwsh verfügbar ist."
