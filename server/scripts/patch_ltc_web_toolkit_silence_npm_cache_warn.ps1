# server/scripts/patch_ltc_web_toolkit_silence_npm_cache_warn.ps1
<#
Idempotent Patch:
- Silenced npm Warnung "using --force Recommended protections disabled." aus `npm cache clean --force`
- Ursache: npm schreibt Warnung auf STDERR; `| Out-Null` fängt nur STDOUT.
- Fix: STDERR-Redirect `2>$null` an der Stelle ergänzen.

Run (Repo-Root):
  pwsh -NoProfile -ExecutionPolicy Bypass -File .\server\scripts\patch_ltc_web_toolkit_silence_npm_cache_warn.ps1
#>

[CmdletBinding()]
param(
  # Optional: explizit RepoRoot angeben, falls du das Script von außerhalb startest
  [string] $RepoRoot = $null
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Find-RepoRoot([string]$StartDir) {
  $resolved = (Resolve-Path -LiteralPath $StartDir).Path
  $di = [System.IO.DirectoryInfo]::new($resolved)

  while ($di -ne $null) {
    $gitDir = Join-Path $di.FullName ".git"
    if (Test-Path -LiteralPath $gitDir -PathType Container) { return $di.FullName }

    $serverDir = Join-Path $di.FullName "server"
    $docsDir   = Join-Path $di.FullName "docs"
    if ((Test-Path -LiteralPath $serverDir -PathType Container) -and (Test-Path -LiteralPath $docsDir -PathType Container)) {
      return $di.FullName
    }

    $di = $di.Parent
  }

  return $null
}

$repoRoot =
  if (-not [string]::IsNullOrWhiteSpace($RepoRoot)) {
    (Resolve-Path -LiteralPath $RepoRoot).Path
  } else {
    Find-RepoRoot (Get-Location).Path
  }

if (-not $repoRoot) {
  throw "Repo root not found. Tipp: cd in das Repo oder nutze -RepoRoot <pfad>."
}

$target = Join-Path $repoRoot "server/scripts/ltc_web_toolkit.ps1"
if (-not (Test-Path -LiteralPath $target -PathType Leaf)) {
  throw "Missing target file: $target"
}

$src = Get-Content -LiteralPath $target -Raw

# schon gepatched?
if ($src -match 'npm\s+cache\s+clean\s+--force"\s*2>\$null') {
  Write-Host "OK: npm cache clean warning already silenced."
  return
}

$pattern = '(&\s*cmd\s*/c\s*"npm\s+cache\s+clean\s+--force")\s*\|\s*Out-Null'
if ($src -notmatch $pattern) {
  throw 'Expected call not found: & cmd /c "npm cache clean --force" | Out-Null'
}

$dst = $src -replace $pattern, '$1 2>$null | Out-Null'

# UTF-8 ohne BOM
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($target, $dst, $utf8NoBom)

Write-Host "OK: silenced npm cache clean --force warning (stderr redirected)."
