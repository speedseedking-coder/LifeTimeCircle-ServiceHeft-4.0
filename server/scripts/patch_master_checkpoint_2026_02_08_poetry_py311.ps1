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

function Get-NewLine([string]$text) {
  if ($text -match "`r`n") { return "`r`n" }
  return "`n"
}

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

function Ensure-Py311PoetryFallback([string]$text, [string]$nl) {
  if ($text -match '(?m)^\s*py\s+-3\.11\s+-m\s+poetry\s+run\s+pytest\s+-q\s*$') { return $text }

  $lines = $text -split "\r\n|\n", 0, "SimpleMatch"
  for ($i = 0; $i -lt $lines.Count; $i++) {
    if ($lines[$i].TrimEnd() -eq 'poetry run pytest -q') {
      $out = New-Object System.Collections.Generic.List[string]
      for ($j = 0; $j -lt $lines.Count; $j++) {
        $out.Add($lines[$j])
        if ($j -eq $i) { $out.Add('py -3.11 -m poetry run pytest -q') }
      }
      return ($out.ToArray() -join $nl)
    }
  }
  return $text
}

function Ensure-PRBlock([string]$text, [string]$nl) {
  if ($text -match '(?m)^\s*✅\s+PR\s+#95\b') { return $text }

  $lines = $text -split "\r\n|\n", 0, "SimpleMatch"
  $idx = -1
  for ($i = 0; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -eq '## Aktueller Stand (main)') { $idx = $i; break }
  }
  if ($idx -lt 0) { throw "Master Checkpoint: '## Aktueller Stand (main)' nicht gefunden." }

  $insert = @(
    '',
    '✅ PR #95 **gemerged**: `chore/ci-helper-script`',
    '- `server/scripts/patch_ci_add_web_build_job.ps1` hinzugefügt (helper patch script, kein Workflow-Change)',
    '',
    '✅ PR #94 **gemerged**: `chore/poetry-lock-py311`',
    '- `server/poetry.lock` unter **Python 3.11** + `poetry 1.8.3` regeneriert; Tests grün',
    '',
    '✅ PR #93 **gemerged**: `chore/add-master-checkpoint-patch-script`',
    ''
  )

  $newLines = New-Object System.Collections.Generic.List[string]
  for ($i = 0; $i -le $idx; $i++) { $newLines.Add($lines[$i]) }
  foreach ($l in $insert) { $newLines.Add($l) }
  for ($i = $idx + 1; $i -lt $lines.Count; $i++) { $newLines.Add($lines[$i]) }

  return ($newLines.ToArray() -join $nl)
}

function Patch-File([string]$path, [scriptblock]$mutator) {
  if (!(Test-Path $path)) { throw "Nicht gefunden: $path" }
  $orig = Get-Content -Raw -Encoding UTF8 $path
  $nl = Get-NewLine $orig
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

Patch-File (Join-Path $root 'docs/99_MASTER_CHECKPOINT.md') {
  param($t, $nl)
  $t = Ensure-StandDate $t '2026-02-08'
  $t = Ensure-PRBlock $t $nl
  $t = Ensure-Py311PoetryFallback $t $nl
  return $t
}

Patch-File (Join-Path $root 'docs/04_REPO_STRUCTURE.md') {
  param($t, $nl)
  $t = Ensure-StandDate $t '2026-02-08'
  $t = Ensure-Py311PoetryFallback $t $nl
  return $t
}
