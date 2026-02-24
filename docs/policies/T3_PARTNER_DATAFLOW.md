// File: ./docs/policies/T3_PARTNER_DATAFLOW.md

# T3_PARTNER_DATAFLOW – Akkreditierte Verifizierung (T3), Datenflüsse & Minimierung

**Stand:** 2026-01-28 (Europe/Berlin)  
**Ziel:** T3-Verifizierung ermöglicht, ohne PII-Leakage und mit Auditability.

---

## 1) Rollen & Akteure
- **T3 Partner**: dealer-Org (oder explizit akkreditierte Stelle)
- **Admin**: akkreditiert/entzieht Partnerstatus
- **User/VIP**: initiiert Verifizierungsanfrage (own)
- **System**: prüft Scope/RBAC, schreibt Audit

---

## 2) Akkreditierung (MUST)
- Nur admin kann T3 Partner akkreditieren.
- Jede Akkreditierung/Entzug schreibt AuditEvent:
  - T3_PARTNER_ACCREDITED / T3_PARTNER_REVOKED

---

## 3) Datenminimierung (MUST)
T3 Partner bekommt nur, was zur Verifizierung nötig ist:
- vehicle_id / entry_id / document_id (interne IDs)
- Dokumentansicht nur, wenn user/org dies explizit erlaubt (shared scope)
- **Keine PII** (E-Mail/Name/Adresse) an Partner im Standardflow

---

## 4) Flows (MVP)
### 4.1 In-App Verifizierung (ohne externe Integration)
1) User/VIP/Dealer requestet T3 für Entry/Document
2) System validiert:
   - scope own/org/shared
   - partner ist akkreditiert
3) Partner sieht Verifizierungs-Queue (nur erlaubte Targets)
4) Partner bestätigt/ablehnt
5) System setzt VERIFICATION_SET_T3 oder VERIFICATION_REVOKED + Audit

### 4.2 API Integration (optional später)
- Signed requests (HMAC-SHA256):
  - Header: signature + timestamp + nonce
- Replay protection: nonce window
- Partner erhält nur redacted payload
- Response: signed acknowledgement

---

## 5) Sicherheit (MUST)
- Step-up für Admin-Akkreditierung (siehe ADMIN_SECURITY_BASELINE.md)
- Partner-Aktionen auditpflichtig
- Partner kann keine Exporte erzeugen
- Rate-limits auf Partner endpoints

---

## 6) Privacy (MUST)
- Keine Klartext-PII im Partnerflow.
- Public-QR bleibt unabhängig; T3 beeinflusst Trustscore intern, aber public bleibt ohne Metrics.
