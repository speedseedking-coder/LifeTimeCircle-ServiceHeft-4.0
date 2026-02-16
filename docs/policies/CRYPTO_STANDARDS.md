// File: ./docs//policies//CRYPTO/_STANDARDS.md



\# CRYPTO\_STANDARDS – Kryptografie, Hashing, Schlüsselmanagement



\*\*Stand:\*\* 2026-01-28 (Europe/Berlin)



---



\## 1) Transport (MUST)

\- TLS 1.2+ (SHOULD: TLS 1.3)

\- HSTS aktiv

\- Secure Cookies (HttpOnly, Secure)



---



\## 2) Pseudonymisierung / HMAC (MUST)

\- HMAC-SHA256 für:

&nbsp; - email\_hmac

&nbsp; - token\_hash / otp\_hash

&nbsp; - log-safe identifiers

\- Keys:

&nbsp; - liegen in Secret Manager/KMS

&nbsp; - Rotation: mindestens jährlich oder bei Incident sofort

&nbsp; - Versionierung der Keys (key\_id) in Datensätzen speichern (MAY)



---



\## 3) Verschlüsselung at rest (MUST für RESTRICTED/SECRET)

\- DB/Storage: encryption at rest

\- Für Exporte/Archive:

&nbsp; - AES-256-GCM (oder KMS-managed envelope encryption)

&nbsp; - Unique nonce/IV pro Objekt



---



\## 4) Randomness (MUST)

\- CSPRNG für Tokens, IDs, nonces

\- Token Längen so wählen, dass brute-force unpraktikabel ist (SHOULD: ≥ 128 bit entropy)



---



\## 5) Passwordless OTP/Links (MUST)

\- Nie OTP/Magic-Link im Klartext persistieren.

\- Vergleiche constant-time.

\- Single-use Tokens.



---



\## 6) Signing (MAY, empfohlen für T3/Partner)

\- Signierte Webhooks/Requests:

&nbsp; - HMAC-SHA256 signature header

&nbsp; - Timestamp + replay protection (nonce window)

Siehe T3\_PARTNER\_DATAFLOW.md



