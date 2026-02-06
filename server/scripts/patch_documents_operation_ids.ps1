# server/scripts/patch_documents_operation_ids.ps1
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$target = Join-Path $PSScriptRoot "..\app\routers\documents.py"
if (-not (Test-Path -LiteralPath $target)) {
  throw "ERROR: target not found: $target"
}

$original = Get-Content -LiteralPath $target -Raw

$routes = @(
  @{ method = "post"; route = "/upload";            opid = "documents_upload" }
  @{ method = "get";  route = "/{doc_id}";          opid = "documents_get" }
  @{ method = "get";  route = "/{doc_id}/download"; opid = "documents_download" }
  @{ method = "get";  route = "/admin/quarantine";  opid = "documents_admin_quarantine" }
  @{ method = "post"; route = "/{doc_id}/scan";     opid = "documents_scan" }
  @{ method = "post"; route = "/{doc_id}/approve";  opid = "documents_approve" }
  @{ method = "post"; route = "/{doc_id}/reject";   opid = "documents_reject" }
)

$lines = $original -split "`n", 0
$found = @{}
$changed = 0

function Update-DecoratorLine {
  param(
    [Parameter(Mandatory=$true)][string]$line,
    [Parameter(Mandatory=$true)][string]$method,
    [Parameter(Mandatory=$true)][string]$route,
    [Parameter(Mandatory=$true)][string]$opid
  )

  $m = $method.ToLowerInvariant()
  $routeEsc = [regex]::Escape($route)

  # Match single-line decorators like:
  # @router.get("/x", response_model=Y)
  # @router.get("/x")
  $pattern = "^(?<prefix>\s*@router\.$m\(\s*[""']$routeEsc[""'])(?<args>.*)\)\s*$"

  $mm = [regex]::Match($line, $pattern)
  if (-not $mm.Success) { return @{ matched = $false; line = $line } }

  if ($line -match "operation_id\s*=") {
    return @{ matched = $true; line = $line; changed = $false }
  }

  $prefix = $mm.Groups["prefix"].Value
  $args   = $mm.Groups["args"].Value

  if ([string]::IsNullOrWhiteSpace($args)) {
    $newline = "$prefix, operation_id=`"$opid`")"
  } else {
    $newline = "$prefix$args, operation_id=`"$opid`")"
  }

  return @{ matched = $true; line = $newline; changed = $true }
}

for ($i = 0; $i -lt $lines.Count; $i++) {
  $line = $lines[$i]

  foreach ($r in $routes) {
    $method = [string]$r.method
    $route  = [string]$r.route
    $opid   = [string]$r.opid

    $res = Update-DecoratorLine -line $line -method $method -route $route -opid $opid
    if ($res.matched) {
      $found["$method $route"] = $true
      if ($res.changed) {
        $lines[$i] = $res.line
        $changed++
      }
      break
    }
  }
}

$missing = @()
foreach ($r in $routes) {
  $k = "$($r.method) $($r.route)"
  if (-not $found.ContainsKey($k)) { $missing += $k }
}

if ($missing.Count -gt 0) {
  # FIX: ${target} statt $target: (PowerShell Parser)
  $msg = "ERROR: expected decorators not found in ${target}:`n - " + ($missing -join "`n - ")
  throw $msg
}

$newText = [string]::Join("`n", $lines)
if (-not $newText.EndsWith("`n")) { $newText += "`n" }

if ($newText -ne $original) {
  $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText($target, $newText, $utf8NoBom)
  Write-Host "OK: operation_id set on documents routes ($changed changes) -> $target"
} else {
  Write-Host "OK: no changes needed -> $target"
}