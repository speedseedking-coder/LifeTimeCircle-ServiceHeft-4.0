param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$target   = Join-Path $repoRoot "docs\99_MASTER_CHECKPOINT.md"

if (-not (Test-Path $target)) { throw "Target not found: $target" }

$text = Get-Content -Raw -Encoding UTF8 $target

# quick exit
if ($text -notmatch "(?m)^(<<<<<<<|=======|>>>>>>>)") {
  Write-Host "OK: no conflict markers found in $target"
  exit 0
}

# Split into lines (supports LF or CRLF)
$lines = $text -split "\r?\n"

# State machine:
# 0 = normal, 1 = in-left, 2 = in-right
$state = 0
$out = New-Object System.Collections.Generic.List[string]

foreach ($line in $lines) {
  if ($state -eq 0 -and $line -match '^(<<<<<<<)\s') {
    $state = 1
    continue
  }
  if ($state -eq 1 -and $line -match '^=======$') {
    $state = 2
    continue
  }
  if ($state -eq 2 -and $line -match '^(>>>>>>>)\s') {
    $state = 0
    continue
  }

  if ($state -eq 0) {
    $out.Add($line)
    continue
  }

  if ($state -eq 2) {
    # keep RIGHT side (after =======)
    $out.Add($line)
    continue
  }

  # state==1 (LEFT side) -> drop
}

if ($state -ne 0) {
  throw "Unclosed conflict block in $target (state=$state). File is malformed."
}

# Re-join as CRLF and ensure EOF newline
$result = ($out -join "`r`n")
if (-not $result.EndsWith("`r`n")) { $result += "`r`n" }

Set-Content -Encoding UTF8 -NoNewline -Path $target -Value $result
Write-Host "OK: resolved conflict markers in $target (kept right-hand side)"