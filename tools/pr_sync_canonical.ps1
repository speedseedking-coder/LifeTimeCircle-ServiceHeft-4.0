cd "C:\Users\stefa\Projekte\LifeTimeCircle-ServiceHeft-4.0"

@'
[CmdletBinding()]
param(
  [string]$BaseRef = "origin/main",
  [string]$Branch  = "chore/pr-sync-canonical-scripts",
  [string]$Remote  = "origin",
  [string]$RepoUrl = "https://github.com/speedseedking-coder/LifeTimeCircle-ServiceHeft-4.0.git"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# =========================================================
# TOKEN SETUP (REQUIRED)
# Set ONE of these env vars in the SAME PowerShell session:
#   $env:LTC_GH_TOKEN = "..."   # preferred
#   $env:GH_TOKEN     = "..."
#   $env:GITHUB_TOKEN = "..."
# =========================================================

function Fail([string]$message) {
  Write-Host $message
  exit 1
}

function Get-TokenFromEnv {
  $candidates = @($env:LTC_GH_TOKEN, $env:GH_TOKEN, $env:GITHUB_TOKEN)
  foreach ($c in $candidates) {
    if (-not [string]::IsNullOrWhiteSpace($c)) { return $c.Trim() }
  }
  return $null
}

function Test-TokenBasic([string]$Token) {
  if ([string]::IsNullOrWhiteSpace($Token)) { return $false }
  $t = $Token.Trim()
  if ($t.Length -lt 30) { return $false }
  if ($t -match '\s')   { return $false }   # keine Whitespaces/Zeilenumbrüche
  return $true
}

function Assert-TokenPreflight([string]$Token) {
  if (-not (Test-TokenBasic $Token)) {
    Fail "STOP(AUTH): TOKEN_MISSING_OR_WEAK (set LTC_GH_TOKEN/GH_TOKEN/GITHUB_TOKEN; length>=30; no whitespace)"
  }

  $headers = @{
    Authorization          = "Bearer $Token"
    "User-Agent"           = "PowerShell"
    Accept                 = "application/vnd.github+json"
    "X-GitHub-Api-Version" = "2022-11-28"
  }

  # 1) token gültig?
  try {
    $me = Invoke-RestMethod -Uri "https://api.github.com/user" -Headers $headers -Method Get
    if ([string]::IsNullOrWhiteSpace($me.login)) { throw "no login" }
  } catch {
    Fail "STOP(AUTH): BAD_CREDENTIALS (GitHub API /user failed) — token invalid/expired/wrong account"
  }

  # 2) token hat Repo-Zugriff? (fine-grained: Repo muss ausgewählt sein + ggf. SSO)
  try {
    $repo = Invoke-RestMethod -Uri "https://api.github.com/repos/speedseedking-coder/LifeTimeCircle-ServiceHeft-4.0" -Headers $headers -Method Get
    if ([string]::IsNullOrWhiteSpace($repo.full_name)) { throw "no repo" }
  } catch {
    Fail "STOP(AUTH): NO_REPO_ACCESS (token valid but cannot access repo) — check fine-grained token repo access / SSO authorization"
  }
}

function Get-GitAuthExtraHeader([string]$Token) {
  $bytes = [Text.Encoding]::ASCII.GetBytes("x-access-token:$Token")
  $b64   = [Convert]::ToBase64String($bytes)
  return "AUTHORIZATION: basic $b64"
}

function Git-Auth {
  param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Args)

  $hdr = Get-GitAuthExtraHeader -Token $script:Token
  & git -c credential.helper= -c credential.interactive=never -c http.extraheader="$hdr" @Args

  if ($LASTEXITCODE -ne 0) {
    Fail ("STOP(GIT): git {0} failed (exit {1})" -f ($Args -join ' '), $LASTEXITCODE)
  }
}

function Git-Checked {
  param([Parameter(ValueFromRemainingArguments = $true)][string[]]$Args)

  $out = & git @Args
  if ($LASTEXITCODE -ne 0) {
    Fail ("STOP(GIT): git {0} failed (exit {1})" -f ($Args -join ' '), $LASTEXITCODE)
  }
  return $out
}

# --- main ---
$script:Token = Get-TokenFromEnv
Assert-TokenPreflight -Token $script:Token

$root = (Git-Checked rev-parse --show-toplevel | Out-String).Trim()
Set-Location $root

# Ensure remote URL (token-free)
try {
  & git remote set-url $Remote $RepoUrl | Out-Null
} catch {
  try {
    & git remote add $Remote $RepoUrl | Out-Null
  } catch {
    Fail "STOP(GIT): cannot add/set remote 'origin' — check RepoUrl/remote permissions"
  }
}

# Fetch using token header (no prompts)
Git-Auth fetch $Remote --prune --tags

# Count commits ahead of BaseRef from CURRENT HEAD (important!)
$aheadRaw = (Git-Checked rev-list --count "$BaseRef..HEAD" | Out-String).Trim()
[int]$ahead = 0
if (-not [int]::TryParse($aheadRaw, [ref]$ahead)) {
  Fail ("STOP(GIT): cannot parse ahead count '{0}'" -f $aheadRaw)
}

if ($ahead -eq 0) {
  Write-Host ("OK: HEAD has no commits ahead of {0} — PR would be empty. Nothing to do." -f $BaseRef)
  exit 0
}

# Push CURRENT HEAD to target PR branch
Git-Auth push -u $Remote ("HEAD:refs/heads/{0}" -f $Branch)

Write-Host ("PR: https://github.com/speedseedking-coder/LifeTimeCircle-ServiceHeft-4.0/compare/main...{0}?expand=1" -f $Branch)
'@ | Set-Content -Encoding UTF8 -NoNewline .\tools\pr_sync_canonical.ps1