[CmdletBinding()]
param(
  [string]$BaseRef = "origin/main",
  [string]$Branch  = "chore/pr-sync-canonical-scripts",
  [string]$Remote  = "origin",
  [string]$RepoUrl = "https://github.com/speedseedking-coder/LifeTimeCircle-ServiceHeft-4.0.git"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function StopAuth([string]$reason) {
  Write-Host ("STOP(AUTH): {0}" -f $reason)
  exit 0
}

# Repo root
$root = (git rev-parse --show-toplevel).Trim()
Set-Location $root

# Remote token-frei setzen (kein Secret)
try { git remote set-url $Remote $RepoUrl | Out-Null } catch { git remote add $Remote $RepoUrl | Out-Null }

# Base holen
git fetch $Remote --prune --tags | Out-Null

# Token aus ENV (non-interactive Gate)
$token = $env:LTC_GH_TOKEN
if ([string]::IsNullOrWhiteSpace($token)) { $token = $env:GH_TOKEN }
if ([string]::IsNullOrWhiteSpace($token)) { $token = $env:GITHUB_TOKEN }

if ([string]::IsNullOrWhiteSpace($token)) { StopAuth "TOKEN_MISSING" }
if ($token.Length -lt 16) { StopAuth "TOKEN_TOO_SHORT" }

# Placeholder-Block (genau das war der Bug)
if ($token -match "DEIN_TOKEN|NICHT_LOGGEN|PASTE_REAL_TOKEN_HERE|YOUR_TOKEN|TOKEN_HERE|<|>") {
  StopAuth "TOKEN_PLACEHOLDER"
}

# AskPass ohne Token in Remote/Config zu schreiben
$env:LTC_ASKPASS_TOKEN = $token
$askPass = Join-Path $env:TEMP ("ltc_askpass_{0}.cmd" -f ([guid]::NewGuid().ToString("N")))
@"
@echo off
set "p=%*"
echo %p% | findstr /I "username" >nul && (echo x-access-token & exit /b 0)
powershell -NoProfile -Command "Write-Output \$env:LTC_ASKPASS_TOKEN"
"@ | Set-Content -Encoding ASCII $askPass

$env:GIT_ASKPASS = $askPass
$env:GIT_TERMINAL_PROMPT = "0"
$env:GCM_INTERACTIVE = "never"

try {
  # Branch auf Base setzen
  git checkout -B $Branch $BaseRef | Out-Null

  # Push (ohne Credential-Manager, komplett non-interactive)
  git -c credential.helper= push --force-with-lease $Remote ("HEAD:{0}" -f $Branch)

  Write-Host ("PR: https://github.com/speedseedking-coder/LifeTimeCircle-ServiceHeft-4.0/compare/main...{0}?expand=1" -f $Branch)
}
finally {
  Remove-Item Env:\LTC_ASKPASS_TOKEN -ErrorAction SilentlyContinue
  Remove-Item Env:\GIT_ASKPASS -ErrorAction SilentlyContinue
  Remove-Item Env:\GIT_TERMINAL_PROMPT -ErrorAction SilentlyContinue
  Remove-Item Env:\GCM_INTERACTIVE -ErrorAction SilentlyContinue
  Remove-Item $askPass -Force -ErrorAction SilentlyContinue
}
