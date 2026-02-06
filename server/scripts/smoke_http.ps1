param(
  [string]$Base = "http://127.0.0.1:8000",
  [string]$Email = "test@example.com",
  [string]$DocVersion = "v1"
)

function Invoke-Api {
  param(
    [ValidateSet("GET","POST")] [string]$Method,
    [string]$Path,
    [hashtable]$Headers = @{},
    [string]$Body = $null
  )
  $uri = $Base + $Path
  if ($null -ne $Body -and $Body.Length -gt 0) {
    $r = Invoke-WebRequest -Method $Method -Uri $uri -Headers $Headers -ContentType "application/json" -Body $Body -SkipHttpErrorCheck
  } else {
    $r = Invoke-WebRequest -Method $Method -Uri $uri -Headers $Headers -SkipHttpErrorCheck
  }

  $snippet = ""
  if ($r.Content) {
    $snippet = $r.Content
    if ($snippet.Length -gt 500) { $snippet = $snippet.Substring(0, 500) + "..." }
  }
  [PSCustomObject]@{
    Method = $Method
    Path   = $Path
    Status = $r.StatusCode
    Body   = $snippet
  }
}

Write-Host "== OPENAPI ==" -ForegroundColor Cyan
$info = Invoke-RestMethod "$Base/openapi.json" | Select-Object -ExpandProperty info
$info | Format-Table -AutoSize

Write-Host "== AUTH REQUEST ==" -ForegroundColor Cyan
$challenge = Invoke-RestMethod -Method Post -Uri ($Base + "/auth/request") -ContentType "application/json" -Body (@{ email=$Email } | ConvertTo-Json)
$challenge | Format-Table -AutoSize

if (-not $challenge.dev_otp) {
  throw "dev_otp fehlt. Stelle sicher, dass LTC_DEV_EXPOSE_OTP=true gesetzt ist."
}

$now = (Get-Date).ToString("o")
$consents = @(
  @{ doc_type="terms";   doc_version=$DocVersion; accepted_at=$now; source="api" },
  @{ doc_type="privacy"; doc_version=$DocVersion; accepted_at=$now; source="api" }
)

Write-Host "== AUTH VERIFY ==" -ForegroundColor Cyan
$verify = Invoke-RestMethod -Method Post -Uri ($Base + "/auth/verify") -ContentType "application/json" -Body (@{
  email=$Email
  challenge_id=$challenge.challenge_id
  otp=$challenge.dev_otp
  consents=$consents
} | ConvertTo-Json -Depth 8)
$verify | Format-Table -AutoSize

$token = $verify.access_token
$h = @{ Authorization = "Bearer $token" }

Write-Host "== SMOKE ==" -ForegroundColor Cyan
$fake = "00000000-0000-0000-0000-000000000000"

$tests = @()
$tests += Invoke-Api GET  "/auth/me" -Headers $h
$tests += Invoke-Api GET  "/admin/users" -Headers $h
$tests += Invoke-Api POST "/api/masterclipboard/sessions" -Headers $h -Body "{}"
$tests += Invoke-Api GET  "/export/vehicle/$fake" -Headers $h
$tests += Invoke-Api GET  "/export/servicebook/$fake" -Headers $h
$tests += Invoke-Api GET  "/export/masterclipboard/$fake" -Headers $h
$tests += Invoke-Api GET  "/public/qr/$fake"
$tests += Invoke-Api POST "/auth/logout" -Headers $h

$tests | Format-Table -AutoSize

Write-Host "== POST-LOGOUT CHECK ==" -ForegroundColor Cyan
$after = Invoke-Api GET "/auth/me" -Headers $h
$after | Format-Table -AutoSize
