Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# UTF-8 Ausgabe (damit Umlaute sauber sind)
try {
  [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
  $OutputEncoding          = [System.Text.UTF8Encoding]::new($false)
} catch {}

function Ok([string]$msg)   { Write-Output "OK   $msg" }
function Warn([string]$msg) { Write-Output "WARN $msg" }
function Fail([string]$msg) { Write-Output "FAIL $msg"; exit  1 }

# RepoRoot: Skript liegt in /scripts -> Root ist Parent
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Ok "RepoRoot: $repoRoot"

$docsDir = Join-Path $repoRoot "docs"
if (-not (Test-Path -LiteralPath $docsDir)) { Fail "docs/ Ordner nicht gefunden: $docsDir" }
Ok "docs/ gefunden"

$policyFile = Join-Path $docsDir "04_POLICY_INDEX.md"
if (-not (Test-Path -LiteralPath $policyFile)) { Fail "Fehlt: $policyFile" }
Ok "Pflichtdateien vorhanden"

# ---- 1) Keine Chat-/Citation-Artefakte im Repo (oaicite/filecite/turnXfileY) ----
$forbiddenRegex = '(?i)(:contentReference\[oaicite|oaicite:|filecite|\bturn\d+file\d+\b)'

$mdFiles = Get-ChildItem -LiteralPath $docsDir -Filter "*.md" -Recurse -File

$hits = foreach ($f in $mdFiles) {
  Select-String -LiteralPath $f.FullName -Pattern $forbiddenRegex -AllMatches -ErrorAction SilentlyContinue
}

if ($hits) {
  Write-Output ""
  Write-Output "Gefundene Chat-/Citation-Artefakte:"
  $hits | Select-Object -First 50 | ForEach-Object {
    $line = ($_.Line ?? "").Trim()
    Write-Output (" - {0}:{1}: {2}" -f $_.Path, $_.LineNumber, $line)
  }
  if ($hits.Count -gt 50) { Warn "Weitere Treffer vorhanden (nur 50 angezeigt)." }
  Fail "Repo enthält Chat-/Citation-Artefakte."
}

Ok "Keine Chat-/Citation-Artefakte in docs/*.md"

# ---- 2) Pflichtstellen im Policy Index ----
$content = Get-Content -LiteralPath $policyFile -Raw -Encoding UTF8

$required = @(
  @{ name = "Trust-Ampel bewertet ausschließlich"; pattern = '(?i)Trust-Ampel\s+bewertet\s+ausschlie(ß|ss|ÃŸ|ÃY)lich' },
  @{ name = "keine Kennzahlen/Counts/Prozente/Zeiträume"; pattern = '(?i)keine\s+Kennzahlen.*Counts.*Prozente.*Zeitr(ä|ae|Ã¤)ume' }
)

$missing = @()
foreach ($r in $required) {
  if ($content -notmatch $r.pattern) { $missing += $r.name }
}

if ($missing.Count -gt 0) {
  Write-Output ""
  Write-Output "Fehlende Pflichtstellen in docs/04_POLICY_INDEX.md:"
  $missing | ForEach-Object { Write-Output (" - " + $_) }
  Fail "Policy-Index unvollständig."
}

Ok "Policy-Index Pflichtstellen vorhanden"
Ok "Quick Check abgeschlossen."
exit 0
