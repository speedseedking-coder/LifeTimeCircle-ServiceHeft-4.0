# 99_MASTER_CHECKPOINT

Stand: 2026-02-01 (Europe/Berlin)
Ziel: produktionsreif (keine Demo), deny-by-default + least privilege, RBAC serverseitig enforced
Kontakt: lifetimecircle@online.de

## 0) Produktkern (Worum geht’s)
Vom Gebrauchtwagen zum dokumentierten Vertrauensgut.  
**Service Heft 4.0** ist das Kernmodul; **Public-QR** bewertet ausschließlich Nachweis-/Dokumentationsqualität (nie technischen Zustand).

---

## 1) Rollenmodell (RBAC)

Rollen:
- `public` (nur Public-QR Mini-Check)
- `user` (eigene Fahrzeuge + eigene Einträge)
- `vip` (erweiterte Sicht/Features)
- `dealer` (gewerblich) (VIP-nah; Verkauf/Übergabe; ggf. Multi-User)
- `moderator` (nur Blog/News, keine/kaum Halterdaten, kein Export, kein Audit)
- `admin` / `superadmin` (vollständig, Freigaben, Governance)

Sonderregel:
- VIP-Gewerbe: max. 2 Mitarbeiterplätze, Freigabe nur SUPERADMIN.

---

## 2) Auth (E-Mail OTP) & Sessions

✅ OTP Flow:
- `/auth/request` erstellt Challenge (dev-only liefert `dev_otp`)
- `/auth/verify` prüft OTP, vergibt Token
- `/auth/me` liefert `user_id` + `role`
- `/auth/logout` revoket Session

Sicherheit:
- Rate Limits (geplant/teilweise)
- TTL für Challenges/Sessions (teilweise)
- Audit Events ohne PII (Policy)

---

## 3) Audit & Governance

- Audit-Log ohne Klartext-PII
- Exporte/Quarantäne/Redaction als Policy festgelegt (Umsetzung folgt)
- Admin-Governance serverseitig enforced

---

## 4) Auth & Consent (FIX)

Consent-Gate Pflicht: AGB + Datenschutz müssen serverseitig akzeptiert sein, bevor „voller Zugang“ erfolgt.

Status (01.02.2026):
- Smoke-Test (PowerShell) läuft stabil: `/auth/request` → `/auth/verify` → `/auth/me` = 200 OK.
- Consent-Contract ist serverseitig strikt:
  - `consents[]` verlangt `accepted_at` (ISO 8601) und `source` ∈ `{ui, api}` (nicht `web`)
  - `doc_type` ∈ `{terms, privacy}`, `doc_version` aktuell: `v1`
- Hinweis: `source="web"` bleibt beim *Request* ok; für *Consent* ist `ui/api` Pflicht.

PowerShell Smoke-Test (ohne Platzhalter):
```powershell
$base  = "http://127.0.0.1:8000"
$email = "test@example.com"

# 1) Request
$req = Invoke-RestMethod -Method Post -Uri "$base/auth/request" -ContentType "application/json" `
  -Body (@{ email=$email; source="web" } | ConvertTo-Json)

$challengeId = [string]$req.challenge_id
$otp = $req.dev_otp
if ($otp -is [int] -or $otp -is [long]) { $otp = "{0:D6}" -f $otp } else { $otp = [string]$otp }

# 2) Verify (+ Consent-Contract)
$acceptedAt = (Get-Date).ToUniversalTime().ToString("o")
$verifyPayload = @{
  email=$email; challenge_id=$challengeId; otp=$otp;
  consents=@(
    @{ doc_type="terms";   doc_version="v1"; accepted_at=$acceptedAt; source="ui" }
    @{ doc_type="privacy"; doc_version="v1"; accepted_at=$acceptedAt; source="ui" }
  )
}
$verify = Invoke-RestMethod -Method Post -Uri "$base/auth/verify" -ContentType "application/json" `
  -Body ($verifyPayload | ConvertTo-Json -Depth 10)

# 3) Me
$token = [string]$verify.access_token
Invoke-RestMethod -Method Get -Uri "$base/auth/me" -Headers @{ Authorization="Bearer $token" } |
  ConvertTo-Json -Depth 10
