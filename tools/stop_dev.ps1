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

  $procIds = $conns | Select-Object -ExpandProperty OwningProcess -Unique
  foreach ($procId in $procIds) {
    if (-not $procId -or $procId -le 0) { continue }
    try {
      $p = Get-Process -Id $procId -ErrorAction Stop
      $name = $p.ProcessName
      Write-Host "PORT ${port}: stoppe PID=$procId ($name)"
      Stop-Process -Id $procId -Force:$Force -ErrorAction Stop
    } catch {
      Write-Host "PORT ${port}: WARN konnte PID=$procId nicht stoppen: $($_.Exception.Message)"
    }
  }
}

Stop-ByPort 8000
Stop-ByPort 5173

Write-Host "DONE."