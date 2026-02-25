// File: ./docs/policies/NEWSLETTER_CONSENT_POLICY.md

# NEWSLETTER_CONSENT_POLICY – Newsletter Opt-in/Opt-out, Nachweis

**Stand:** 2026-01-28 (Europe/Berlin)  
**Prinzip:** Explicit Consent, Double Opt-in, jederzeit abmeldbar

---

## 1) Consent-Modell (MUST)
- Newsletter ist optional.
- Versand nur an `opted_in`.
- Consent wird dokumentiert:
  - user_id, status, updated_at
  - double_opt_in: confirmed_at, confirmation_source (email link)
  - evidence_hash optional (HMAC)

---

## 2) Double Opt-in (MUST)
Flow:
1) User aktiviert Newsletter in UI
2) System sendet Bestätigungslink (single-use, TTL)
3) Erst nach Klick: status = opted_in, confirmed_at gesetzt

Anti-Enumeration: Bestätigung darf keine Account-Existenz leaken.

---

## 3) Opt-out (MUST)
- Jeder Newsletter enthält Opt-out Link.
- Opt-out ist sofort wirksam.
- Opt-out erzeugt AuditEvent (NEWSLETTER_SUBSCRIPTION updated) – ohne PII.

---

## 4) Datenminimierung (MUST)
- Newsletter System speichert keine zusätzlichen PII außer Account E-Mail.
- Exporte: redacted default (keine E-Mail Klartext).

---

## 5) Audit (SHOULD)
- CONSENT_ACCEPTED (Newsletter)
- NEWSLETTER_SUBSCRIPTION status changes
