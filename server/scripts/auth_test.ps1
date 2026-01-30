param(
  [Parameter(Mandatory=$true)]
  [string]$Email,

  [string]$BaseUrl = "http://127.0.0.1:8000"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function PostJson($url, $obj) {
  $json = $obj | ConvertTo-Json -Depth 8
  return Invoke-RestMethod -Method Post -Uri $url -ContentType "application/json" -Body $json
}

Write-Host "== AUTH TEST =="
Write-Host "BaseUrl: $BaseUrl"
Write-Host "Email:   $Email"
Write-Host ""

# 1) Request
$r = PostJson "$BaseUrl/auth/request" @{ email = $Email }
Write-Host "REQUEST OK"
Write-Host ("challenge_id: {0}" -f $r.challenge_id)
if ($null -ne $r.dev_otp -and $r.dev_otp.ToString().Trim().Length -gt 0) {
  Write-Host ("dev_otp:      {0}" -f $r.dev_otp)
} else {
  Write-Host "dev_otp:      (nicht im Response) -> OTP muss aus E-Mail kommen"
}
Write-Host ""

# 2) OTP bestimmen
$otp = $null
if ($null -ne $r.dev_otp -and $r.dev_otp.ToString().Trim().Length -gt 0) {
  $otp = $r.dev_otp.ToString().Trim()
} else {
  $otp = Read-Host "OTP aus E-Mail eingeben"
}
if (-not $otp -or $otp.Trim().Length -lt 4) {
  throw "Kein gültiger OTP eingegeben."
}

# 3) Verify
$verifyBody = @{
  email = $Email
  challenge_id = $r.challenge_id
  otp = $otp
  consents = @(
    @{ doc_type="terms";   doc_version="v1"; accepted_at=(Get-Date).ToString("o"); source="ui" },
    @{ doc_type="privacy"; doc_version="v1"; accepted_at=(Get-Date).ToString("o"); source="ui" }
  )
}

$login = PostJson "$BaseUrl/auth/verify" $verifyBody
Write-Host "VERIFY OK"
Write-Host ("access_token: {0}..." -f $login.access_token.Substring(0, [Math]::Min(24, $login.access_token.Length)))
Write-Host ("expires_at:   {0}" -f $login.expires_at)
Write-Host ""

# 4) /me
$headers = @{ Authorization = "Bearer $($login.access_token)" }
$me = Invoke-RestMethod -Method Get -Uri "$BaseUrl/auth/me" -Headers $headers
Write-Host "ME OK"
Write-Host ("user_id: {0}" -f $me.user_id)
Write-Host ("role:    {0}" -f $me.role)
Write-Host ""

# 5) Logout
$lo = Invoke-RestMethod -Method Post -Uri "$BaseUrl/auth/logout" -Headers $headers
Write-Host "LOGOUT OK"
Write-Host ($lo | ConvertTo-Json -Depth 5)
Write-Host ""

Write-Host "FERTIG ✅"
