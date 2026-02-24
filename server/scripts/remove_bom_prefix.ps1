Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

param(
  [Parameter(Mandatory=$true)]
  [string[]] $Files
)

$root = (git rev-parse --show-toplevel).Trim()
Set-Location $root
[Environment]::CurrentDirectory = $root

$bom = [byte[]](0xEF,0xBB,0xBF)

foreach ($rel in $Files) {
  $p = Join-Path $root $rel
  if (-not (Test-Path -LiteralPath $p)) { throw "Missing: $rel" }

  $bytes = [System.IO.File]::ReadAllBytes($p)

  if ($bytes.Length -ge 3 -and $bytes[0] -eq $bom[0] -and $bytes[1] -eq $bom[1] -and $bytes[2] -eq $bom[2]) {
    if ($bytes.Length -eq 3) {
      [System.IO.File]::WriteAllBytes($p, [byte[]]@())
    } else {
      [System.IO.File]::WriteAllBytes($p, $bytes[3..($bytes.Length-1)])
    }
    Write-Host "BOM removed: $rel"
  }
}

Write-Host "DONE: BOM removal pass completed."