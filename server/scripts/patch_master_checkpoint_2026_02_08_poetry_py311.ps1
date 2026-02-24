# server/scripts/patch_master_checkpoint_2026_02_08_poetry_py311.ps1
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

function Detect-NL([string]$t) { if ($t -match "`r`n") { "`r`n" } else { "`n" } }

function Write-Utf8NoBom([string]$path, [string]$content) {
  $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($path, $content, $utf8NoBom)
}

function Ensure-StandDate([string]$text, [string]$date) {
  if ($text -match '(?m)^Stand:\s+\*\*\d{4}-\d{2}-\d{2}\*\*') {
    return ($text -replace '(?m)^Stand:\s+\*\*\d{4}-\d{2}-\d{2}\*\*', "Stand: **$date**")
  }
  return $text
}

function Remove-PRLines([string[]]$lines) {
  $filtered = New-Object System.Collections.Generic.List[string]
  foreach ($l in $lines) {
    if ($l -match '^\s*✅\s+PR\s+#95\b') { continue }
    if ($l -match '^\s*✅\s+PR\s+#94\b') { continue }
    if ($l -match '^\s*✅\s+PR\s+#93\b') { continue }
    if ($l -match '^\s*-\s*`server/scripts/patch_ci_add_web_build_job\.ps1`') { continue }
    if ($l -match '^\s*-\s*`server/poetry\.lock`') { continue }
    $filtered.Add($l)
  }
  # führende Leerzeilen entfernen
  while ($filtered.Count -gt 0 -and [string]::IsNullOrWhiteSpace($filtered[0])) { $filtered.RemoveAt(0) }
  return ,$filtered.ToArray()
}

function Insert-PRBlockAfterAktuellerStand([string[]]$lines) {
  $idx = -1
  for ($i = 0; $i -lt $lines.Count; $i++) {
    if ($lines[$i].Trim() -match '^##\s+Aktueller\s+Stand\b') { $idx = $i; break }
  }
  if ($idx -lt 0) { throw "docs/99_MASTER_CHECKPOINT.md: '## Aktueller Stand' nicht gefunden." }

  $block = @(
    "",
    "✅ PR #95 **gemerged**: `chore/ci-helper-script`",
    "- `server/scripts/patch_ci_add_web_build_job.ps1` hinzugefügt (helper patch script, kein Workflow-Change)",
    "",
    "✅ PR #94 **gemerged**: `chore/poetry-lock-py311`",
    "- `server/poetry.lock` unter **Python 3.11** + `poetry 1.8.3` regeneriert; Tests grün",
    "",
    "✅ PR #93 **gemerged**: `chore/add-master-checkpoint-patch-script`",
    ""
  )

  $out = New-Object System.Collections.Generic.List[string]
  for ($i = 0; $i -le $idx; $i++) { $out.Add($lines[$i]) }
  foreach ($b in $block) { $out.Add($b) }
  for ($i = $idx + 1; $i -lt $lines.Count; $i++) { $out.Add($lines[$i]) }
  return ,$out.ToArray()
}

function Ensure-Py311AfterPoetryRun([string[]]$lines) {
  $out = New-Object System.Collections.Generic.List[string]
  for ($i = 0; $i -lt $lines.Count; $i++) {
    $line = $lines[$i]
    $out.Add($line)

    $m = [regex]::Match($line, '^(?<ind>\s*)poetry\s+run\s+pytest\s+-q\s*$')
    if ($m.Success) {
      $ind = $m.Groups['ind'].Value
      $next = if ($i + 1 -lt $lines.Count) { $lines[$i + 1] } else { "" }
      if ($next -notmatch '^\s*py\s+-3\.11\s+-m\s+poetry\s+run\s+pytest\s+-q\s*$') {
        $out.Add($ind + 'py -3.11 -m poetry run pytest -q')
      }
    }
  }
  return ,$out.ToArray()
}

function Patch-File([string]$path, [scriptblock]$mutator) {
  if (!(Test-Path $path)) { throw "Nicht gefunden: $path" }
  $orig = Get-Content -Raw -Encoding UTF8 $path
  $nl = Detect-NL $orig
  $text = & $mutator $orig $nl
  $text = $text.TrimEnd("`r","`n") + $nl
  if ($text -ne $orig) {
    Write-Utf8NoBom $path $text
    Write-Host "OK: patched $path"
  } else {
    Write-Host "OK: no changes needed $path"
  }
}

$root = Resolve-RepoRoot

Patch-File (Join-Path $root "docs/99_MASTER_CHECKPOINT.md") {
  param($t, $nl)

  $t = Ensure-StandDate $t "2026-02-08"
  $lines = $t -split "\r\n|\n"
  $lines = Remove-PRLines $lines
  $lines = Insert-PRBlockAfterAktuellerStand $lines
  $lines = Ensure-Py311AfterPoetryRun $lines

  ($lines -join $nl)
}

Patch-File (Join-Path $root "docs/04_REPO_STRUCTURE.md") {
  param($t, $nl)

  $t = Ensure-StandDate $t "2026-02-08"
  $lines = $t -split "\r\n|\n"
  $lines = Ensure-Py311AfterPoetryRun $lines

  ($lines -join $nl)
}
