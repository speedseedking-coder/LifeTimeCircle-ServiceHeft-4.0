# UPLOAD SECURITY POLICY – LifeTimeCircle / Service Heft 4.0

Version: 1.1  
Stand: 2026-01-27  
Owner: SUPERADMIN

---

## 0) Zweck
Verbindliche Sicherheitsregeln für Uploads (Dokumente/Bilder): Malware/PII-Risiko, Zugriffsschutz, Logging/Audit.

---

## 1) Grundregeln (Non-Negotiable)
- Uploads sind niemals öffentlich per Default.
- Public-QR zeigt keine Uploads und keine uploadbezogenen Identifikatoren.
- Raw Uploads mit potenzieller PII-A nur berechtigt sichtbar.
- Jede Verfügbarkeit eines Uploads ist ein **expliziter Statuswechsel** (kein “sofort online”).

---

## 2) Dateitypen (Allowlist)
- Bilder: JPG/JPEG, PNG, WEBP
- Dokumente: PDF
Alles andere blocken.

---

## 3) Limits (Defaults)
- Max pro Datei: 10 MB
- Max pro Vorgang: 5 Dateien
- Max pro Tag pro User: 50 Dateien (oder enger nach Betrieb)

---

## 4) Sicherheitsprüfungen (Pflicht – Mindeststandard)
### 4.1 Immer verpflichtend
- MIME sniffing + Extension Check (beides muss passen)
- Upload startet immer als: `QUARANTINED`

### 4.2 Scan/Approval Regeln (Minimum)
Es gilt genau eine der beiden Betriebsarten:

**A) AV/Scanner verfügbar (Preferred)**
- Datei bleibt `QUARANTINED` bis Scan abgeschlossen.
- Ergebnis:
  - clean → `AVAILABLE`
  - fail/suspicious → `REJECTED` (+ Audit)

**B) Kein AV/Scanner verfügbar (Fallback, aber verbindlich)**
- Datei bleibt `QUARANTINED` bis **manuelle Freigabe** (ADMIN oder SUPERADMIN).
- Ohne Freigabe: keine Anzeige/kein Download.
- Für Bilder: bei Freigabe nur als serverseitig neu-encodetes Derivat ausliefern (Metadaten/EXIF entfernen).
- Für PDF: ohne Scan nur freigeben, wenn zwingend benötigt; sonst blocken (Policy-Entscheid im Betrieb).

---

## 5) PII Handling / Redaction
- Wenn Inhalte Kennzeichen/Personen/Adressen enthalten können:
  - Redaction/Anonymisierung muss möglich sein (wenn Feature vorgesehen)
- Public liefert niemals unredacted Inhalte.

---

## 6) Zugriff (RBAC)
- USER: nur eigene Uploads (Ownership)
- VIP/DEALER/VIP_BIZ: scope-basiert (Org/zugewiesene Fahrzeuge)
- MODERATOR: keine Upload-Einsicht
- ADMIN/SUPERADMIN: operativ (PII-minimiert), nur bei Bedarf

---

## 7) Logging/Audit
- Logs: keine Dateiinhalte, keine EXIF-Daten, keine OCR-Ausgaben
- Audit Events:
  - upload_received, upload_quarantined, upload_approved, upload_rejected
  - download_attempted, download_denied (optional)

---

## 8) Retention
Siehe `DATA_RETENTION.md`

---
