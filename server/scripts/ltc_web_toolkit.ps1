# LifeTimeCircle – Web Toolkit (PowerShell)
# Usage:
#   pwsh -NoProfile -ExecutionPolicy Bypass -File server/scripts/ltc_web_toolkit.ps1 -Smoke
#   pwsh -NoProfile -ExecutionPolicy Bypass -File server/scripts/ltc_web_toolkit.ps1 -Smoke -Clean

[CmdletBinding()]
param(
  [switch]$Smoke,
  [switch]$Clean
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

# PS7+: verhindert, dass stderr von native commands als terminating error behandelt wird
if (Get-Variable -Name PSNativeCommandUseErrorActionPreference -Scope Global -ErrorAction SilentlyContinue) {
  $global:PSNativeCommandUseErrorActionPreference = $false
}

function Set-RepoRoot {
  $root = (git rev-parse --show-toplevel 2>$null)
  if (-not $root) { throw "Not in git repo. cd in Repo und nochmal." }
  Set-Location $root.Trim()
  (Get-Location).Path
}

function NpmCmd {
  param([Parameter(ValueFromRemainingArguments=$true)][string[]]$Args)
  & cmd /c npm @Args
  if ($LASTEXITCODE -ne 0) { throw "npm failed (exit=$LASTEXITCODE)" }
}

function Invoke-CmdQuiet([string]$CmdLine) {
  & cmd /c "$CmdLine >NUL 2>NUL" | Out-Null
}

function Kill-Node { Invoke-CmdQuiet "taskkill /F /IM node.exe" }
function Rm-NodeModules { Invoke-CmdQuiet "rmdir /s /q node_modules" }

function Web-Smoke {
  param([switch]$Clean)

  $repo = Set-RepoRoot
  Set-Location (Join-Path $repo "packages\web")

  Kill-Node

  if ($Clean) {
    Rm-NodeModules
    try { & cmd /c "npm cache clean --force" 2>$null | Out-Null } catch { }
  }

  NpmCmd ci --no-audit --no-fund
  NpmCmd run build
}

if ($Smoke) {
  Web-Smoke -Clean:$Clean
  exit 0
}

Write-Host "No action selected. Use: -Smoke [-Clean]"
exit 2
