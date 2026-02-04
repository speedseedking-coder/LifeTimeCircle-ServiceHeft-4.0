param(
  [string]$BaseBranch = "main",
  [string]$HeadBranch = "feat/uploads-quarantine-p0"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Repo-Root ermitteln (Script liegt unter server/scripts)
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Push-Location $repoRoot

try {
  $title = "P0 Uploads: Quarantine-by-default + Admin Approve/Reject (RBAC serverseitig)"

  $body = @"
SoT:
- docs/99_MASTER_CHECKPOINT.md (Uploads Quarantine-by-default; Export redaction: nur APPROVED)
- docs/03_RIGHTS_MATRIX.md (3b Quarantine Workflow: approve/reject nur admin/superadmin; moderator strikt nur Blog/News)
- docs/01_DECISIONS.md (D-001 deny-by-default; D-002/D-011 moderator; D-016 uploads quarantine)

Merge-Gates:
- pytest grün (inkl. RBAC-Guard Tests)
- keine StaticFiles-Mounts/öffentlichen Uploads
- /documents/* hat forbid_moderator
- Download/Content für user/vip/dealer nur bei APPROVED
- admin/quarantine + approve/reject nur admin/superadmin
"@

  # PR-Text als Datei + Clipboard
  $tmp = Join-Path $env:TEMP "pr_body_uploads_quarantine_p0.txt"
  $body | Set-Content -Encoding UTF8 $tmp
  Set-Clipboard -Value $body

  Write-Host ""
  Write-Host "PR Title (kopieren):"
  Write-Host $title
  Write-Host ""
  Write-Host "PR Body liegt in:" $tmp
  Write-Host "PR Body ist im Clipboard."

  # GitHub Compare-URL optional öffnen, wenn origin GitHub ist
  $origin = (git remote get-url origin 2>$null)
  if ($origin) {
    $origin = $origin.Trim()

    # ssh: git@github.com:owner/repo.git
    if ($origin -match "^git@github\.com:(.+?)/(.+?)(\.git)?$") {
      $owner = $Matches[1]
      $repo  = $Matches[2]
      $url = "https://github.com/$owner/$repo/compare/${BaseBranch}...${HeadBranch}?expand=1"
      Write-Host ""
      Write-Host "Öffne Browser (Compare/PR):" $url
      Start-Process $url | Out-Null
      return
    }

    # https: https://github.com/owner/repo.git
    if ($origin -match "^https://github\.com/(.+?)/(.+?)(\.git)?$") {
      $owner = $Matches[1]
      $repo  = $Matches[2]
      $url = "https://github.com/$owner/$repo/compare/${BaseBranch}...${HeadBranch}?expand=1"
      Write-Host ""
      Write-Host "Öffne Browser (Compare/PR):" $url
      Start-Process $url | Out-Null
      return
    }
  }

  Write-Host ""
  Write-Host "Kein GitHub-origin erkannt. Manuell: GitHub -> Pull requests -> New pull request"
  Write-Host "Base:" $BaseBranch " Compare:" $HeadBranch
  Write-Host "Body ist bereits im Clipboard."
}
finally {
  Pop-Location
}