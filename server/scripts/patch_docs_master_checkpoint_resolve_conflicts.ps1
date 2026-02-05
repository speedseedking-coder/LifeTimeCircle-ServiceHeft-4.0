param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$target   = Join-Path $repoRoot "docs\99_MASTER_CHECKPOINT.md"

if (-not (Test-Path $target)) { throw "Target not found: $target" }

$text  = Get-Content -Raw -Encoding UTF8 $target
$lines = $text -split "`r?`n", 0, "RegexOptions"

$out = New-Object System.Collections.Generic.List[string]
$hasConflicts = $false

$i = 0
while ($i -lt $lines.Count) {
  $line = $lines[$i]

  if ($line -match '^(<<<<<<<)\s') {
    $hasConflicts = $true

    # skip left side until =======
    $i++
    while ($i -lt $lines.Count -and $lines[$i] -notmatch '^=======$') { $i++ }
    if ($i -ge $lines.Count) { throw "Unclosed conflict: missing ======= in $target" }

    # skip ======= line
    $i++

    # keep right side until >>>>>>>
    while ($i -lt $lines.Count -and $lines[$i] -notmatch '^(>>>>>>>)\s') {
      $out.Add($lines[$i])
      $i++
    }
    if ($i -ge $lines.Count) { throw "Unclosed conflict: missing >>>>>>> in $target" }

    # skip >>>>>>> line
    $i++
    continue
  }

  $out.Add($line)
  $i++
}

if (-not $hasConflicts) {
  Write-Host "OK: no conflict markers found in $target"
  exit 0
}

# join with CRLF and ensure EOF newline
$result = ($out -join "`r`n")
if (-not $result.EndsWith("`r`n")) { $result += "`r`n" }

Set-Content -Encoding UTF8 -NoNewline -Path $target -Value $result
Write-Host "OK: resolved conflict markers in $target (kept right-hand side after =======)"