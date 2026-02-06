docs/04_POLICY_INDEX.md
# LifeTimeCircle – ServiceHeft 4.0
# Policy-Index (Implementierbar, deny-by-default, least privilege)
Stand: 2026-01-29 (Europe/Berlin)

> Ziel: Produktionsreif, keine Demo. Rechte serverseitig enforced. Default: deny-by-default + least privilege.

---

## 0) Begriffe & Rollen
**Brand/Produkt:** LifeTimeCircle / Service Heft 4.0  
**Kontakt:** lifetimecircle@online.de  

### Rollen (RBAC)
- **public**: nur Public-QR Mini-Check (anonym)
- **user**: eigenes Konto, eigene Fahrzeuge/Einträge/Dokumente
- **vip**: erweiterte Features (inkl. Verkauf/Übergabe-QR)
- **dealer**: gewerblich (VIP-nah), Übergabe/Verkauf, ggf. Multi-User
- **moderator**: nur Blog/News (keine PII, kein Export, kein Audit)
- **admin**: Vollzugriff + Freigaben + Governance (hochrisiko)
---
## 1) Datenklassen & Grundschutz
### Datenklassen
- **Public-Daten:** Public-QR Anzeige (Trust-Ampel + textliche Indikatoren, keine Halterdaten)
- **Account-Daten (PII):** E-Mail, Consent-Logs, Rollen, Org-Zuordnung
- **Fahrzeug-Daten:** VIN/WID, Fahrzeugprofil, Timeline-Einträge
- **Nachweise/Dokumente:** Rechnungen, Prüfberichte, Bilder (Upload-Objekte)
- **Governance-Daten:** Audit-Log, Freigaben, Rollenänderungen
- **Secrets:** niemals loggen; nur Secret-Store/Env

### Grundregeln (immer)
- **Keine Secrets in Logs.**
- **Keine Klartext-PII in Logs/Exports.**
- Pseudonymisierung via **HMAC** (kein unsalted SHA).
- Uploads: Allowlist + Limits + Quarantine-by-default; Freigabe nach Scan/Admin.
- Exporte: Standard **redacted**; Full Export nur **SUPERADMIN** + Audit + TTL/Limit + Verschlüsselung.

---

## 2) AUTH / Consent Policies (P-AUTH-*)
### P-AUTH-001 | E-Mail Login + Verifizierung (Pflicht)
**Regel:** Anmeldung per **E-Mail Login** mit **Verifizierung** (Code oder Magic-Link).  
**Enforcement:** API-first (Session erst nach erfolgreicher Verifizierung „aktiv“).  
**Security:** One-time Token, TTL, Rate-Limits, Anti-Enumeration.

### P-AUTH-002 | AGB + Datenschutz Pflicht (Version + Timestamp)
**Regel:** Ohne bestätigte AGB/Datenschutz **keine Registrierung/kein produktiver Zugriff**.  
**Speichern/Protokollieren:** consent_version, consent_timestamp, consent_source (web/app), user_id.

### P-AUTH-003 | Recovery (minimal produktionsfähig)
**Regel:** Passwort-Reset / Account-Recovery vorhanden (kein Support-Workaround im Code).  
**Enforcement:** Token TTL + Rate-Limits + Anti-Enumeration.

---

## 3) RBAC Policies (P-RBAC-*)
### P-RBAC-001 | Serverseitige Rechte-Erzwingung
**Regel:** Jede geschützte Aktion wird serverseitig anhand Rolle+Scope entschieden; UI spiegelt nur.  
**Default:** deny-by-default.

### P-RBAC-002 | Scope-Regel „Eigene Daten“
- **user/vip/dealer:** dürfen standardmäßig **nur eigene Fahrzeuge/Einträge/Dokumente** vollständig sehen/bearbeiten.  
- Fremdzugriff nur über explizite Berechtigung (z. B. Übergabe-/Freigabe-Token, org-scope, auditfähig).

### P-RBAC-003 | Verkauf/Übergabe-QR & interner Verkauf: VIP/Dealer only
**Regel:** Verkauf/Übergabe-QR und interner Verkauf **nur** für **vip** und **dealer** sichtbar/nutzbar.

### P-RBAC-004 | VIP-Gewerbe: max 2 Staff + SUPERADMIN-Freigabe
**Regel:** VIP-Gewerbe kann bis zu 2 Mitarbeiterplätze erhalten; Aktivierung nur nach SUPERADMIN-Freigabe.  
**Audit:** Freigabe-Event mit actor/admin, org_id, seats_before/after (intern), reason.

### P-RBAC-005 | Moderator strikt: nur Blog/News
**Regel:** moderator darf nur Blog/News verwalten; keine PII, kein Export, kein Audit-Log-Zugriff.

---

## 4) Public-QR Mini-Check Policies (P-PUBLIC-*)
### P-PUBLIC-001 | Bewertet nur Nachweis-/Dokumentationsqualität
**Regel:** Trust-Ampel bewertet ausschließlich Dokumentations-/Nachweisqualität, nie technischen Zustand.

### P-PUBLIC-002 | Ampel Rot/Orange/Gelb/Grün + Kriterien
**Kriterien (mindestens):**
- Historie vorhanden
- Verifizierungsgrad (T1/T2/T3)
- Aktualität/Regelmäßigkeit
- Unfalltrust: **Grün** bei Unfall nur bei **Abschluss + Belegen**

### P-PUBLIC-003 | Public Response: keine Metrics + Disclaimer Pflicht
**Regel:** In Public-QR **keine** Kennzahlen/Counts/Prozente/Zeiträume ausgeben.  
**Pflicht-Disclaimer (UI Copy, Public):**
> „Die Trust-Ampel bewertet ausschließlich die Dokumentations- und Nachweisqualität. Sie ist keine Aussage über den technischen Zustand des Fahrzeugs.“

---

## 5) Service Heft Kern Policies (P-SH-*)
### P-SH-001 | Fahrzeug anlegen/suchen (VIN/WID)
**Regel:** Fahrzeuge können von user/vip/dealer angelegt werden; public/moderator nicht.  
**Validierung:** VIN/WID Eingabe strikt validieren; Fehlertexte ohne Datenleak.

### P-SH-002 | Einträge & Verifizierungslevel (T1/T2/T3)
**Regel:** Einträge sind strukturiert, versioniert; Verifizierungsstufe je Eintrag wird gespeichert.  
**Hinweis:** Exakte Definition T1/T2/T3 ist offen, aber Speicherung/Workflow muss vorgesehen sein.

### P-SH-003 | Dokumente/Nachweise: Upload + Sichtbarkeit nach Rolle
- user: Metadaten + Inhalt nur im eigenen Scope
- vip/dealer: erweiterte Sichtbarkeit (z. B. Bildansicht „VIP only“)
- public: keine Dokument-Metadaten/Downloads
- moderator: kein Zugriff
- admin: Vollzugriff

---

## 6) Upload & Dokumenten-Sicherheit (P-UP-*)
### P-UP-001 | Allowlist + Limits + Quarantine-by-default
**Regel:** Uploads nur definierte Dateitypen, Größenlimits, Quarantine default.  
**Freigabe:** nach Scan oder Admin-Approval (SUPERADMIN).  
**Public:** keine öffentlichen Uploads/Links.

### P-UP-002 | Sichtbare Metadaten minimieren
**Regel:** Metadaten im UI so knapp wie möglich (Titel/Datum/Typ); keine versteckten PII.

---

## 7) Logging / Audit / Export (P-AUDIT-*, P-EXP-*)
### P-AUDIT-001 | Audit-Minimum für Security-relevante Aktionen
Audit-Events mindestens für:
- Rollenänderungen / Sperren / Freigaben
- Übergabe-QR/Verkaufsvorgänge
- Verifizierungsstatus-Änderungen

### P-AUDIT-002 | Keine Secrets/PII im Klartext im Audit
**Regel:** actor_id, target_id, org_id, action, timestamp, pseudonymisierte Marker (HMAC).

### P-EXP-001 | Export standard redacted
**Regel:** Standard-Export ist redacted; Full Export nur SUPERADMIN, zeitlich begrenzt, verschlüsselt.

---

## 8) Module & Feature-Gates (Produktions-UI)
> UI zeigt nur Module, die für die Rolle zulässig sind; Server bleibt Quelle der Wahrheit.

### Modul M-01 | Frontpage/Hub + Navigation
- Sichtbar für alle Rollen, inkl. public (ohne Accountfeatures)
- Login-Panel standard links (konfigurierbar)

### Modul M-02 | Auth (Login/Verify/Consent/Recovery)
- Alle Rollen (Accountflow); public nur Public-QR ohne Login
- Consent Pflicht, Version+Timestamp

### Modul M-03 | Service Heft 4.0 Kern (Fahrzeug/Timeline/Dokumente)
- user/vip/dealer: ja
- public/moderator: nein
- Rechte gemäß Matrix

### Modul M-04 | Public-QR Mini-Check
- Alle Rollen + anonym (public): ja
- Ampel + Indikatoren, keine Halterdaten, kein technischer Zustand
- Keine Metrics + Pflicht-Disclaimer

### Modul M-05 | Blogbase (Admin) + Newsletter
- Lesen: alle
- Schreiben: moderator/admin (moderator nur News/Blog)
- Newsletter Versand: nur admin

### Modul M-06 | Verkauf/Übergabe-QR & Interner Verkauf (VIP/Dealer)
- Sichtbar/nutzbar: vip/dealer
- Audit: Pflicht
- Versteckt für user/public/moderator

### Modul M-07 | VIP-Bereich: Checklisten & Ankauf privat (PDF/Papier only)
- Sichtbar: vip/dealer
- Ausgabe: nur PDF-Download/Print-Ansicht (keine editierbaren Online-Checklisten für Free)
- Moderator/public: nie

---

## 9) DoD (Abnahme-Check, verbindlich)
- Navigation/Buttons ok, Empty States ok
- RBAC serverseitig enforced
- Public-QR ohne Metrics + Disclaimer vorhanden
- Logs/Audit/Export konform (keine Secrets/PII Klartext)
- Uploads allowlist+limits+quarantine
- Keine Pfadfehler/Altpfade (Branding konsistent: LifeTimeCircle / Service Heft 4.0)


> Hinweis: Es werden keine Kennzahlen/Counts/Prozente/Zeiträume ausgewiesen.







