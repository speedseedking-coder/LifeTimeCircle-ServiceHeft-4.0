# DATA CLASSIFICATION – LifeTimeCircle / Service Heft 4.0

Version: 1.0  
Stand: 2026-01-27  
Owner: SUPERADMIN

---

## 1) Klassen (Kurz)
- PII-A: Halterdaten/Identität/Bewegungsprofile (hoch)
- PII-B: indirekt identifizierend (mittel)
- NON-PII: ohne Personenbezug (frei)
- SECRETS (S0): Zugriffsdaten (immer verboten in Logs/Export)

---

## 2) Fahrzeug-Grenzfälle (verbindlich)

### 2.1 VIN (Fahrgestellnummer)
- Klasse: PII-B
- Logs/Export: nie Klartext, nur Hash oder gekürzt (z. B. letzte 4)

### 2.2 Kennzeichen
- Klasse: PII-B (wird PII-A wenn mit Halterdaten kombiniert)
- Public: nie vollständig anzeigen
- Logs/Export: nur Hash/gekürzt

### 2.3 Fahrzeug-ID / QR-ID (intern)
- Klasse: NON-PII, solange nicht öffentlich auflösbar
- Wenn öffentlich resolvable: PII-B

### 2.4 Standortdaten / Probefahrt-Zeitreihen
- Klasse: PII-A
- Public: niemals
- Retention: kurz (siehe DATA_RETENTION)
- Export: redacted by default (siehe EXPORT_POLICY)

### 2.5 Dokumente/Bilder (Rechnung/Gutachten/Werkstattbericht)
- Klasse: PII-A
- Anzeige/Sharing nur redacted/autorisiert
- Logs: niemals Inhalt, nur Metadaten (doc_id/type/status)

---
