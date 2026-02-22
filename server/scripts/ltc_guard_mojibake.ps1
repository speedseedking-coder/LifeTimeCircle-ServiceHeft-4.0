Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$root = (git rev-parse --show-toplevel).Trim()
Set-Location $root
[Environment]::CurrentDirectory = $root

New-Item -ItemType Directory -Force -Path .\artifacts | Out-Null

# 1) Block: archived node_modules snapshots
$old = Get-ChildItem -Recurse -Directory -Filter "node_modules__old_*" -ErrorAction SilentlyContinue
if ($old) {
  $old | Select-Object -First 20 FullName | ForEach-Object { $_.FullName }
  throw "BLOCK: node_modules__old_* found. Delete them before commit."
}

# 2) Block: mojibake
node .\tools\mojibake_scan.js --root . |
  Out-File -FilePath .\artifacts\mojibake_report.jsonl -Encoding utf8

$hits = ((Get-Content .\artifacts\mojibake_report.jsonl -ErrorAction SilentlyContinue) | Measure-Object -Line).Lines
if ($hits -ne 0) {
  Get-Content .\artifacts\mojibake_report.jsonl -Encoding UTF8 | Select-Object -First 10
  throw "BLOCK: Mojibake hits=$hits. Fix before commit."
}

"OK: no old snapshots + mojibake hits=0"