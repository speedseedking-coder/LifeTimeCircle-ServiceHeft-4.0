# server/scripts/patch_documents_download_requires_approved.ps1
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$target = Resolve-Path (Join-Path $PSScriptRoot "..\app\routers\documents.py")
if (-not (Test-Path $target)) { throw "Target file not found: $target" }

$src = Get-Content -Raw -Path $target

$marker = "LTC_PATCH: download requires approved for non-admin"
if ($src -match [regex]::Escape($marker)) {
  Write-Host "OK: Patch already present in $target"
  exit 0
}

# 1) Ensure HTTPException import exists
$fastapiImportPattern = '(?m)^from\s+fastapi\s+import\s+(.+)$'
$m = [regex]::Match($src, $fastapiImportPattern)
if ($m.Success) {
  $imports = $m.Groups[1].Value
  if ($imports -notmatch '\bHTTPException\b') {
    $newImports = ($imports.TrimEnd() + ", HTTPException")
    $src = [regex]::Replace(
      $src,
      $fastapiImportPattern,
      ("from fastapi import " + $newImports),
      1
    )
    Write-Host "OK: Added HTTPException to fastapi imports"
  }
} else {
  $src = "from fastapi import HTTPException`n" + $src
  Write-Host "OK: Added standalone HTTPException import (fallback)"
}

# 2) Locate download route block
$downloadDecorator = [regex]::Match($src, '(?m)^\s*@router\.get\(\s*["'']/?\{doc_id\}/download["''].*$')
if (-not $downloadDecorator.Success) {
  throw "Could not find download route decorator (@router.get('/{doc_id}/download')) in $target"
}

# Define a slice starting from the decorator
$tail = $src.Substring($downloadDecorator.Index)

# Find end of this handler block (next @router.* at column 0-ish OR EOF)
$nextRoute = [regex]::Match($tail, '(?m)^\s*@router\.', $downloadDecorator.Length)
$handlerText = if ($nextRoute.Success) { $tail.Substring(0, $nextRoute.Index) } else { $tail }

# 3) Find which variable holds status in this handler (something.get("status") or ["status"])
$statusVarMatch = [regex]::Match($handlerText, '(?m)(\w+)\s*(?:\.get\(\s*["'']status["'']|\[\s*["'']status["'']\s*\])')
if (-not $statusVarMatch.Success) {
  throw "Could not detect status variable in download handler. Expected something like X.get('status') or X['status']."
}
$statusVar = $statusVarMatch.Groups[1].Value

# 4) Find the first assignment to that status var in this handler, capture indentation
$assignPattern = "(?m)^(?<indent>\s+)$statusVar\s*=\s*.*$"
$assignMatch = [regex]::Match($handlerText, $assignPattern)
if (-not $assignMatch.Success) {
  throw "Detected status var '$statusVar' but could not find its assignment line in download handler."
}
$indent = $assignMatch.Groups["indent"].Value

# 5) Detect actor variable used for role checks (something['role'] or something.get('role'))
$roleVarMatch = [regex]::Match($handlerText, '(?m)(\w+)\s*(?:\.get\(\s*["'']role["'']|\[\s*["'']role["'']\s*\])')
$actorVar = if ($roleVarMatch.Success) { $roleVarMatch.Groups[1].Value } else { "actor" }

# 6) Insert guard directly after the assignment line
$inject = @"
$indent# $marker (SoT: docs/03_RIGHTS_MATRIX.md 3/3b)
$indent# user/vip/dealer dürfen Content nur bei Status APPROVED abrufen.
$indent# admin/superadmin dürfen in Quarantäne zum Review zugreifen.
$indent`$_role = ""
$indentif (`$null -ne $actorVar) {
$indent    if ($actorVar -is [hashtable] -or $actorVar -is [System.Collections.IDictionary]) {
$indent        `$_role = [string]($actorVar["role"] ?? "")
$indent    } else {
$indent        `$_role = [string]($actorVar.role ?? "")
$indent    }
$indent}
$indent`$_role = `$_role.ToLowerInvariant()

$indent`$_status = ""
$indentif (`$null -ne $statusVar) {
$indent    if ($statusVar -is [hashtable] -or $statusVar -is [System.Collections.IDictionary]) {
$indent        `$_status = [string]($statusVar["status"] ?? "")
$indent    } else {
$indent        `$_status = [string]($statusVar.status ?? "")
$indent    }
$indent}
$indent`$_status = `$_status.ToLowerInvariant()

$indentif (`$_role -notin @("admin","superadmin") -and `$_status -ne "approved") {
$indent    raise HTTPException(status_code=403, detail="document not approved")
$indent}
"@

# Insert after the assignment line (end of line)
$insertPosInHandler = $assignMatch.Index + $assignMatch.Length
$patchedHandler = $handlerText.Insert($insertPosInHandler, "`n$inject")

# Replace original handlerText inside $tail, then splice back into full source
$tailPatched = $tail.Replace($handlerText, $patchedHandler)

# Splice back
$src = $src.Substring(0, $downloadDecorator.Index) + $tailPatched

Set-Content -Path $target -Value $src -Encoding UTF8
Write-Host "OK: Patched download guard in $target (status-var=$statusVar, actor-var=$actorVar)"