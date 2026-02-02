param(
  [string]$Base  = "http://127.0.0.1:8000",
  [string]$Email = "test@example.com"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Server erreichbar?
try { Invoke-RestMethod "$Base/openapi.json" -Method Get | Out-Null }
catch { throw "Server nicht erreichbar unter $Base (läuft Fenster A?)" }

# Request
$req = Invoke-RestMethod "$Base/auth/request" -Method Post -ContentType "application/json" `
  -Body (@{ email = $Email } | ConvertTo-Json)

$challengeId = [string]$req.challenge_id
if ([string]::IsNullOrWhiteSpace($challengeId)) { throw "Kein challenge_id in /auth/request" }

$otp = [string]$req.dev_otp
if ([string]::IsNullOrWhiteSpace($otp)) {
  throw "dev_otp ist null/leer. Stelle sicher: LTC_DEV_EXPOSE_OTP=1 im Server-Fenster (A) gesetzt VOR dem Start."
}

# Consent-Contract
$acceptedAt = (Get-Date).ToUniversalTime().ToString("o")
$consents = @(
  @{ doc_type="terms";   doc_version="v1"; accepted_at=$acceptedAt; source="ui"  },
  @{ doc_type="privacy"; doc_version="v1"; accepted_at=$acceptedAt; source="api" }
)

# Verify (Login)
$verify = Invoke-RestMethod "$Base/auth/verify" -Method Post -ContentType "application/json" `
  -Body (@{ email=$Email; challenge_id=$challengeId; otp=$otp; consents=$consents } | ConvertTo-Json -Depth 10)

$token = [string]$verify.access_token
if ([string]::IsNullOrWhiteSpace($token)) { throw "Kein access_token erhalten." }

$h = @{ Authorization = "Bearer $token" }

"AUTH ME:"
Invoke-RestMethod "$Base/auth/me" -Headers $h | ConvertTo-Json -Depth 10

# Consent ACCEPT (persistiert in DB)
"CONSENT ACCEPT:"
Invoke-RestMethod "$Base/consent/accept" -Method Post -Headers $h -ContentType "application/json" `
  -Body (@{ consents=$consents } | ConvertTo-Json -Depth 10) | ConvertTo-Json -Depth 10

# Status erneut prüfen
"CONSENT STATUS:"
$st = Invoke-RestMethod "$Base/consent/status" -Headers $h
$st | ConvertTo-Json -Depth 10

if ($st.is_complete -ne $true) {
  throw "Consent ist nach /consent/accept immer noch nicht komplett. Prüfe Consent-Store/DB."
}

"OK: Auth + Consent komplett."
