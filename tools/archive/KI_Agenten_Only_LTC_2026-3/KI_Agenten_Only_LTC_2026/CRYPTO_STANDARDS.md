# CRYPTO STANDARDS – LifeTimeCircle / Service Heft 4.0

Version: 1.0  
Stand: 2026-01-27  
Owner: SUPERADMIN

---

## 0) Zweck
Verbindliche kryptografische Standards für:
- Hashing/Pseudonymisierung (PII-B) in Logs/Audit/Exports
- Token-Hashes (Verify/Magic-Link)
- Signaturen (T3)
- Verschlüsselung (Exports/Backups)

---

## 1) Grundregeln (Non-Negotiable)
1. Kein unsalted SHA256 für E-Mail/IP/VIN/Kennzeichen.
2. Stabile Pseudonymisierung via HMAC-SHA256 mit Secret-Key.
3. Verify-/Magic-Link Tokens nur gehashed persistent speichern.
4. Verschlüsselung nur AEAD (AES-256-GCM oder ChaCha20-Poly1305).
5. Keys/Secrets niemals im Repo; nur Env/Secret-Store.

---

## 2) Hashing-Standards
### 2.1 Stabile Pseudonymisierung (Logs/Audit/Exports)
- Algorithmus: HMAC-SHA256
- Key: `HMAC_PSEUDO_KEY` (Secret)
- Inputs normalisieren:
  - E-Mail: trim + lowercase
  - VIN/Kennzeichen: trim + uppercase (optional)
- Outputs: base64url oder hex
- Felder:
  - email_hash, ip_hash, vin_hash, plate_hash, user_agent_hash

### 2.2 Token-Hashes (Verify/Magic-Link)
- Persistiert wird nur token_hash
- Algorithmus: SHA-256 über (token + TOKEN_PEPPER)
- Pepper: `TOKEN_PEPPER` (Secret, rotierbar)
- Token Entropie: mindestens 128 Bit (besser 192–256 Bit)

---

## 3) Randomness
- CSPRNG (OS random)
- Keine Zeitstempel/IDs als Tokens

---

## 4) Password Hashing (nur falls Passwörter genutzt werden)
- Argon2id
- Unique salt pro Passwort
- Pepper optional im Secret-Store

---

## 5) Encryption
### 5.1 Exporte/Backups (at rest)
- AES-256-GCM oder ChaCha20-Poly1305
- Unique nonce/iv pro Datei
- Key Rotation: mindestens jährlich oder nach Incident

### 5.2 Transport
- TLS überall (auch intern, wenn möglich)

---

## 6) T3 Signaturen (Partner)
- Signatur über canonical JSON payload
- Algorithmus: Ed25519 oder ECDSA P-256
- Partner Public Keys: allowlist

---

## 7) Logging/Audit
- Nie Keys/Pepper/Token loggen
- Hashes (HMAC-basiert) sind ok

---
