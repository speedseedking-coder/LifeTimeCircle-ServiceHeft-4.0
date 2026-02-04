param(
  [string]$Base  = "http://127.0.0.1:8000",
  [string]$EmailVip = "vip@example.com",
  [string]$EmailDealer = "dealer@example.com",
  [string]$EmailUser = "user@example.com"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not $env:LTC_DB_PATH) { throw "LTC_DB_PATH fehlt (muss auf eure SQLite-DB zeigen)" }
if (-not $env:LTC_SECRET_KEY -or $env:LTC_SECRET_KEY.Length -lt 32) { throw "LTC_SECRET_KEY fehlt/zu kurz (>=32)" }

function Get-VerifyConsents {
  $cc = irm "$Base/consent/current" -Method Get
  $docs = $null

  $cc = irm "$Base/consent/current"

$docs = $null
if ($cc -is [System.Array]) {
  $docs = $cc
} elseif ($cc.documents) {
  $docs = $cc.documents
} elseif ($cc.docs) {
  $docs = $cc.docs
} elseif ($cc.consents) {
  $docs = $cc.consents
} elseif ($cc.items) {
  $docs = $cc.items
} else {
  throw ("Unexpected /consent/current payload: " + ($cc | ConvertTo-Json -Depth 20))
}

$acceptedAt = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")

$consents = @()
foreach ($d in $docs) {
  $dt = $d.doc_type; if (-not $dt) { $dt = $d.docType }; if (-not $dt) { $dt = $d.type }
  $dv = $d.doc_version; if (-not $dv) { $dv = $d.docVersion }; if (-not $dv) { $dv = $d.version }
  if (-not $dt -or -not $dv) { continue }
  $consents += @{ doc_type = $dt; doc_version = $dv; accepted_at = $acceptedAt }
}


  $out = @()
  foreach ($d in $docs) {
    if ($null -eq $d) { continue }
    $dt = $d.doc_type
    if (-not $dt) { $dt = $d.type }
    if (-not $dt) { $dt = $d.docType }
    if (-not $dt) { $dt = $d.name }

    $dv = $d.doc_version
    if (-not $dv) { $dv = $d.version }
    if (-not $dv) { $dv = $d.docVersion }

    if ($dt -and $dv) {
      $out += @{ doc_type = [string]$dt; doc_version = [string]$dv }
    }
  }

  if ($out.Count -eq 0) {
    $out = @(
      @{ doc_type="terms"; doc_version="v1" },
      @{ doc_type="privacy"; doc_version="v1" }
    )
  }
  return $out
}

function Auth-Login([string]$Email) {
  $r1 = irm "$Base/auth/request" -Method Post -ContentType "application/json" -Body (@{ email = $Email } | ConvertTo-Json)
  $cid = $r1.challenge_id
  $otp = $r1.dev_otp
  if (-not $cid -or -not $otp) { throw "Auth request liefert kein challenge_id/dev_otp (LTC_DEV_EXPOSE_OTP aktiv?)" }

  $consents = Get-VerifyConsents

  $body = @{
    challenge_id = $cid
    otp          = $otp
    email        = $Email
    consents     = $consents
  } | ConvertTo-Json -Depth 10

  $r2 = irm "$Base/auth/verify" -Method Post -ContentType "application/json" -Body $body
  $token = $r2.access_token
  if (-not $token) { throw "Auth verify liefert kein access_token" }

  $me = irm "$Base/auth/me" -Headers @{ Authorization = "Bearer $token" }
  $uid = $me.user_id
  if (-not $uid) { throw "auth/me liefert kein user_id" }

  return @{ token=$token; user_id=$uid }
}

function Set-Role([string]$UserId, [string]$Role) {
  python -c @"
import os, sqlite3
db=os.environ['LTC_DB_PATH']
uid='$UserId'
role='$Role'
con=sqlite3.connect(db)
con.execute("UPDATE auth_users SET role=? WHERE user_id=?", (role, uid))
con.commit()
con.close()
print("OK role set", uid, role)
"@
}

Write-Host "Login VIP..."
$vip = Auth-Login $EmailVip
Set-Role $vip.user_id "vip"

Write-Host "Login DEALER..."
$dealer = Auth-Login $EmailDealer
Set-Role $dealer.user_id "dealer"

Write-Host "Login USER..."
$user = Auth-Login $EmailUser
Set-Role $user.user_id "user"

Write-Host "Check: USER create must be 403..."
try {
  irm "$Base/sale/transfer/create" -Method Post -ContentType "application/json" -Headers @{ Authorization="Bearer $($user.token)" } -Body (@{ vehicle_id="veh-smoke" } | ConvertTo-Json) | Out-Null
  throw "FEHLER: USER create war nicht geblockt"
} catch {
  if ($_.Exception.Response.StatusCode.value__ -ne 403) { throw $_ }
  Write-Host "OK: USER create blocked (403)"
}

Write-Host "VIP creates transfer..."
$create = irm "$Base/sale/transfer/create" -Method Post -ContentType "application/json" -Headers @{ Authorization="Bearer $($vip.token)" } -Body (@{ vehicle_id="veh-smoke" } | ConvertTo-Json)
$tid = $create.transfer_id
$ttok = $create.transfer_token
if (-not $tid -or -not $ttok) { throw "Create response unvollständig" }
Write-Host "OK: created transfer_id=$tid (token nicht ausgegeben)"

Write-Host "DEALER redeems transfer..."
$redeem = irm "$Base/sale/transfer/redeem" -Method Post -ContentType "application/json" -Headers @{ Authorization="Bearer $($dealer.token)" } -Body (@{ transfer_token=$ttok } | ConvertTo-Json)
if ($redeem.status -ne "redeemed") { throw "Redeem status != redeemed" }
Write-Host "OK: redeemed transfer_id=$($redeem.transfer_id) ownership_transferred=$($redeem.ownership_transferred)"

Write-Host "VIP reads status..."
$st1 = irm "$Base/sale/transfer/status/$tid" -Headers @{ Authorization="Bearer $($vip.token)" }
Write-Host "OK: status=$($st1.status)"

Write-Host "DEALER reads status..."
$st2 = irm "$Base/sale/transfer/status/$tid" -Headers @{ Authorization="Bearer $($dealer.token)" }
Write-Host "OK: status=$($st2.status)"

Write-Host "DONE."
