# server/scripts/patch_ci_add_web_build_job.ps1
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-RepoRoot {
  $dir = Get-Location
  for ($i = 0; $i -lt 12; $i++) {
    if (Test-Path (Join-Path $dir ".git")) { return (Resolve-Path $dir).Path }
    if (Test-Path (Join-Path $dir "docs")) { return (Resolve-Path $dir).Path }
    $parent = Split-Path -Parent $dir
    if ($parent -eq $dir) { break }
    $dir = $parent
  }
  throw "Repo-Root nicht gefunden (erwarte .git oder docs/). Bitte im Repo-Root ausführen."
}

$root = Resolve-RepoRoot
$ciPath = Join-Path $root ".github/workflows/ci.yml"
if (!(Test-Path $ciPath)) { throw "Nicht gefunden: $ciPath" }

$text = Get-Content -Raw -Encoding UTF8 $ciPath

# Idempotenz: nicht doppelt einfügen
if ($text -match "(?m)^\s*web_build\s*:\s*$" -or $text -match "(?m)^\s*name:\s*web_build\s*$") {
  Write-Host "OK: ci.yml enthält bereits web_build."
  exit 0
}

# Newline-Stil beibehalten
$nl = "`n"
if ($text -match "`r`n") { $nl = "`r`n" }

# Jobs-Block (2-space indent unter jobs:)
$jobBlock = @(
  "  web_build:",
  "    name: web_build",
  "    runs-on: ubuntu-latest",
  "    steps:",
  "      - name: Checkout",
  "        uses: actions/checkout@v4",
  "      - name: Setup Node",
  "        uses: actions/setup-node@v4",
  "        with:",
  "          node-version: 20",
  "          cache: npm",
  "          cache-dependency-path: packages/web/package-lock.json",
  "      - name: Install",
  "        working-directory: packages/web",
  "        run: npm ci",
  "      - name: Build",
  "        working-directory: packages/web",
  "        run: npm run build"
) -join $nl

# Einfügeposition: direkt im jobs:-Block, vor dem nächsten Top-Level-Key (Spalte 0)
$lines = $text -split "(`r`n|`n)", 0, "SimpleMatch"
$jobsIdx = -1
for ($i = 0; $i -lt $lines.Count; $i++) {
  if ($lines[$i] -match "^(jobs):\s*(#.*)?$") { $jobsIdx = $i; break }
}
if ($jobsIdx -lt 0) { throw "ci.yml: Kein 'jobs:' gefunden." }

$insertAt = $lines.Count
for ($i = $jobsIdx + 1; $i -lt $lines.Count; $i++) {
  $line = $lines[$i]
  if ([string]::IsNullOrWhiteSpace($line)) { continue }
  if ($line -match "^\s+#") { continue }
  # Top-Level Key (keine Einrückung)
  if ($line -match "^[A-Za-z0-9_.-]+:\s*(#.*)?$" -and $line -notmatch "^\s") {
    $insertAt = $i
    break
  }
}

# Vorher/Nachher sauber zusammensetzen
$before = ($lines[0..($insertAt-1)] -join $nl).TrimEnd()
$after  = ""
if ($insertAt -lt $lines.Count) {
  $after = ($lines[$insertAt..($lines.Count-1)] -join $nl).TrimStart()
}

$newText = $before + $nl + $nl + $jobBlock.TrimEnd() + $nl + $nl + $after.TrimEnd() + $nl

# UTF-8 ohne BOM schreiben (pwsh)
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($ciPath, $newText, $utf8NoBom)

Write-Host "OK: web_build Job in ci.yml ergänzt."