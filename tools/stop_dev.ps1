# tools/stop_dev.ps1
# LifeTimeCircle – Service Heft 4.0
# Stoppt DEV-Prozesse für API (8000) und WEB (5173) über Port-Auflösung.
#
# Usage:
#   pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\stop_dev.ps1
#   pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\stop_dev.ps1 -Force

[CmdletBinding()]
param(
  [switch]$Force
)

$ErrorActionPreference = "Stop"

function Stop-ByPort([int]$port) {
  $conns = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
  if (-not $conns) {
    Write-Host "PORT ${port}: kein Listener"
    return
  }

  $pids = $conns | Select-Object -ExpandProperty OwningProcess -Unique
  foreach ($pid in $pids) {
    if (-not $pid -or $pid -le 0) { continue }
    try {
      $p = Get-Process -Id $pid -ErrorAction Stop
      $name = $p.ProcessName
      Write-Host "PORT ${port}: stoppe PID=$pid ($name)"
      Stop-Process -Id $pid -Force:$Force -ErrorAction Stop
    } catch {
      Write-Host "PORT ${port}: WARN konnte PID=$pid nicht stoppen: $($_.Exception.Message)"
    }
  }
}

Stop-ByPort 8000
Stop-ByPort 5173

Write-Host "DONE."