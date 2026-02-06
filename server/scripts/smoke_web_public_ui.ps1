# server/scripts/smoke_web_public_ui.ps1
# Smoke: prüft, ob Vite-Proxy + Public-Endpunkte durch den Browser/HTTP erreichbar sind.
# Erwartung:
# - API läuft auf :8000
# - WEB läuft auf :5173
# - Vite Proxy /api/* -> :8000/*

$ErrorActionPreference = "Stop"

function Assert-Status($Url, $ExpectedMin = 200, $ExpectedMax = 399) {
  $r = Invoke-WebRequest -Uri $Url -UseBasicParsing -MaximumRedirection 5
  if ($r.StatusCode -lt $ExpectedMin -or $r.StatusCode -gt $ExpectedMax) {
    throw "FAIL: $Url -> $($r.StatusCode) (expected $ExpectedMin..$ExpectedMax)"
  }
  Write-Host ("OK: {0} -> {1}" -f $Url, $r.StatusCode)
}

Write-Host "== NetConnection =="
Test-NetConnection 127.0.0.1 -Port 8000 | Out-Host
Test-NetConnection 127.0.0.1 -Port 5173 | Out-Host

Write-Host "== API direct =="
Assert-Status "http://127.0.0.1:8000/public/site"
Assert-Status "http://127.0.0.1:8000/blog"
Assert-Status "http://127.0.0.1:8000/news"

Write-Host "== Via Vite Proxy (/api/*) =="
Assert-Status "http://127.0.0.1:5173/api/public/site"
Assert-Status "http://127.0.0.1:5173/api/blog"
Assert-Status "http://127.0.0.1:5173/api/news"

Write-Host "DONE"