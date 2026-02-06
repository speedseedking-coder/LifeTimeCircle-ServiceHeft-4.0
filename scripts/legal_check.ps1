# scripts/legal_check.ps1
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Resolve-RepoRoot {
  param([string]$StartDir)
  # repo root = parent of scripts\
  $p = Resolve-Path $StartDir
  return (Get-Item $p).Parent.FullName
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Resolve-RepoRoot -StartDir $scriptDir

$toolPath = Join-Path $repoRoot "tools\license_asset_audit.py"
if (-not (Test-Path $toolPath)) {
  throw "Tool fehlt: $toolPath"
}

# Output dir in docs/legal
$outDir = Join-Path $repoRoot "docs\legal"
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

# poetry lives in server\
$serverDir = Join-Path $repoRoot "server"
if (-not (Test-Path $serverDir)) {
  throw "Server-Ordner fehlt: $serverDir"
}

Write-Host "[INFO] RepoRoot: $repoRoot"
Write-Host "[INFO] OutDir:   $outDir"
Write-Host "[INFO] Tool:     $toolPath"

Push-Location $serverDir
try {
  # basic presence check
  if (-not (Test-Path ".\poetry.lock")) {
    Write-Warning "server\poetry.lock nicht gefunden. Python-Report wird unvollständig."
  }

  # If poetry missing -> clear error message
  $poetryOk = $true
  try {
    poetry --version | Out-Null
  } catch {
    $poetryOk = $false
  }
  if (-not $poetryOk) {
    throw "Poetry nicht gefunden. Installiere Poetry und führe dann erneut aus."
  }

  # Wichtig: für vollständige Lizenzinfos müssen deps installiert sein:
  # poetry install
  # (Wir erzwingen das NICHT automatisch.)
  Write-Host "[INFO] Starte Audit via poetry run ..."
  poetry run python "$toolPath" --repo-root "$repoRoot" --out-dir "docs/legal" --json

  Write-Host "[OK] Fertig. Öffne: docs\legal\LEGAL_SUMMARY.md"
} finally {
  Pop-Location
}
