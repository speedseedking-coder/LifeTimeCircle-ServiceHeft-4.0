# 99_MASTER_CHECKPOINT — LifeTimeCircle / Service Heft 4.0

Stand: 2026-02-01 (Europe/Berlin)  
Checkpoint: **Lizenzkontrolle ergänzt + Smoke stabil (Logout ok) + Export-Missing-Tables = 404 statt 500**  
Ziel: produktionsreif (keine Demo), stabiler MVP → danach Ausbau  
Kontakt: lifetimecircle@online.de  
Source of Truth (Docs): `...\LifeTimeCircle-ServiceHeft-4.0\docs\` (keine Altpfade/Altversionen)

---

## 0) Projektidentität (FIX)

- Brand: **LifeTimeCircle**
- Produkt/Modul: **Service Heft 4.0**
- Ziel: **produktionsreif**, kein Demo-Modus, stabiler MVP → danach Ausbau
- Design-Regel: Look nicht „wild“ ändern — Fokus auf Module/Komponenten & Aktualität
- Source of Truth: **`\docs\`** (keine Doppel-/Altversionen an anderen Pfaden)

---

## 1) Nicht verhandelbare Leitplanken (FIX)

### 1.1 Security/Privacy (serverseitig, zwingend)
- **deny-by-default** + **least privilege**
- **RBAC serverseitig enforced** (UI ist nie Sicherheitsinstanz)
- **keine Secrets in Logs**, keine Tokens/Codes/Links im Klartext loggen
- **keine Klartext-PII** in Logs/Audit/Exports
- Pseudonymisierung: **HMAC** (kein unsalted SHA)
- Uploads: **Allowlist + Limits + Quarantine by default**, Freigabe nur nach Scan/Admin-Approval, **keine öffentlichen Uploads**
- Exports: **redacted default**, Full nur **SUPERADMIN** + Audit + TTL/Limit + Verschlüsselung

### 1.2 Public-QR (öffentlich)
- Bewertet ausschließlich **Dokumentations-/Nachweisqualität**, **nie technischen Zustand**
- Public Response: **keine Metrics/Counts/Percentages/Zeiträume**
- Pflicht-Disclaimer (exakt, ohne Abwandlung):

  > „Die Trust-Ampel bewertet ausschließlich die Dokumentations- und Nachweisqualität. Sie ist keine Aussage über den technischen Zustand des Fahrzeugs.“

### 1.3 Business-Gating
- Verkauf/Übergabe-QR & interner Verkauf: nur **VIP** & **DEALER**
- VIP-Gewerbe: **max. 2 Staff**, Freigabe nur **SUPERADMIN**

---

## 2) Rollenmodell (RBAC) (FIX)

Rollen:
- `public`
- `user`
- `vip`
- `dealer`
- `moderator`
- `admin`
- `superadmin`

Sonderregeln:
- `moderator`: **nur Blog/News**, keine PII, **kein Export**, **kein Audit-Read**
- `superadmin` Provisioning: **out-of-band** (nicht über normale Admin-Endpunkte)

---

## 3) Auth & Consent (FIX)

- E-Mail Login + Verifizierung (OTP/Magic-Link)
- One-time + TTL + Rate-Limits + Anti-Enumeration
- Consent-Gate Pflicht (AGB + Datenschutz)
- Speicherung: Version + Timestamp (auditierbar)
- Tokens/Codes/Links: **niemals** im Klartext loggen

---

## 4) Lizenzkontrolle (NEU, FIX)

Status: **Lizenzkontrolle wurde ergänzt** (serverseitig).

Policy-Ziele:
- Lizenzprüfung ist **zusätzlich** zu Auth/RBAC (RBAC bleibt Pflicht).
- Default: **deny**, wenn Lizenz fehlt/ungültig/abgelaufen/gesperrt.
- Lizenzdaten/Keys: **niemals** in Logs/Audit im Klartext.
- Fehlerbild: klar & stabil (z. B. `403 forbidden` oder eigener Code/Reason), aber ohne Leak sensibler Infos.

Offen (damit „final“ wirklich final wird):
- Welche Features sind lizenzpflichtig? (Mapping Feature → Tier/Flag)
- Wie wird Lizenzzustand verwaltet? (DB/Config/External) + Testfälle
- Welche Rollen dürfen Lizenz setzen/ändern? (vermutlich: **SUPERADMIN**)

---

## 5) MVP-Scope (Produktkern)

### MVP-Kern
- Service Heft 4.0:
  - Profil (VIN/WID + QR/ID)
  - Timeline/Einträge
  - Dokumente/Uploads
  - Trust-Level je Eintrag/Quelle (T1/T2/T3)
- Public-QR Mini-Check: Ampel Rot/Orange/Gelb/Grün (ohne Metrics, mit Disclaimer)
- Frontpage/Hub + Login
- Blog/News (Admin erstellt; Moderator verwaltet strikt Blog/News)

### Admin-Minimum (Governance)
- Userliste **redacted**
- Rolle setzen
- Moderatoren akkreditieren
- VIP-Gewerbe-2-Staff-Freigabe (**SUPERADMIN**)
- Audit (ohne PII)

### Zusatzmodule (später, VIP/Dealer)
- Verkauf/Übergabe-QR, interner Verkauf
- Gewerbe: Direktannahme, MasterClipboard, OBD/GPS etc.

---

## 6) Trustscore / T-Level (Status)

Grundsatz:
- Ampel bewertet nur Dokumentation/Verifizierungsgrad, **nicht** Technik.

Kriterien high-level (ohne Metriken):
- Historie
- T-Level
- Aktualität/Regelmäßigkeit (ohne Zahlen/Zeiträume)
- Unfalltrust

Unfallregel:
- „Grün trotz Unfall“ nur bei **Abschluss + Belegen**

P0-Entscheidungen offen:
- Definition T1/T2/T3 (Belegarten/Prüfer/Regeln)
- Ampel-Mindestbedingungen je Stufe (deterministisch, ohne Metrics)
- Definition „Unfall abgeschlossen“ + Pflichtbelege

---

## 7) Repo/Setup (IST)

Repo: `...\LifeTimeCircle-ServiceHeft-4.0`  
Server: `...\LifeTimeCircle-ServiceHeft-4.0\server`

Top-Level: `docs/ server/ static/ storage/ tools/ scripts/`

ZIP-Regel:
- Rein: `docs/ server/ static/ tools/ scripts/ .env.example README* CHANGELOG*`
- Nicht rein: `server\data\app.db`, `.venv`, `__pycache__`, `.pytest_cache`, Logs, Build-Artefakte

---

## 8) Backend IST-Stand (FastAPI/Poetry/SQLite)

Auth:
- Challenge funktioniert (DEV OTP optional)
- Sessions/Token-Check ok

Security:
- Audit vorhanden (ohne Klartext-PII)
- RBAC-Guards integriert (401/403 sauber)
- UTC/tz-aware Timestamps gepatcht
- Pytest grün (zuletzt bestätigt; je nach letztem Commit erneut laufen lassen)

Smoke (zuletzt):
- `/auth/me` → 200 nach Login
- `/admin/users` → 403 als user (korrekt)
- `/auth/logout` → 200 + danach `/auth/me` → 401 (korrekt)

---

## 9) Exports (P0)

Policy-Ziel:
- Default **redacted**
- Full Export nur **SUPERADMIN** + one-time grant + TTL/Limit + Verschlüsselung + Audit
- Token nie im Log

Status:
- Vehicle Export ist als Referenz-Implementierung dokumentiert/geführt.
- Servicebook Export ist als Zielbild/Analog-Mechanik vorgesehen.

Smoke-Verhalten (Core-DB ohne Tabellen):
- `/export/vehicle/{id}` → **404 `vehicle_table_missing`** (korrekt: kein 500)
- `/export/servicebook/{id}` → **404 `servicebook_table_missing`** (korrekt: kein 500)

---

## 10) MasterClipboard / Gewerbe (IST)

- MasterClipboard-Endpunkte sind dealer/admin gated.
- Smoke als `user` liefert 401/403 (korrekt, solange Business-Gate so gewollt).

---

## 11) Offene Entscheidungen (MUSS vor „final“)

- T1/T2/T3 Belegarten/Prüfer/Regeln
- Ampel-Mindestbedingungen (deterministisch, ohne Metrics)
- Definition „Unfall abgeschlossen“ + Pflichtbelege
- Übergabe-/Verkaufsflow (inkl. Käufer ohne Account)
- Newsletter-Workflow (Send-only vs Reply/Feedback + Moderation)
- Lizenzmodell: Feature-Mapping + Admin/Provisioning + Tests

---

## 12) Backlog-Reihenfolge (Epics, „hart sinnvoll“)

1) EPIC-02 Auth/Consent  
2) EPIC-03 RBAC  
3) EPIC-04 Admin-Minimum  
4) EPIC-10 Betrieb/Qualität/Produktion  
5) EPIC-05 Service Heft Kern  
6) EPIC-06 Public-QR Mini-Check  
7) EPIC-08 Landingpage/Navigation  
8) EPIC-07 Blog/Newsletter  
9) EPIC-09 Verkauf/Übergabe  

---

## 13) Definition of Done — Gate vor Abgabe (MUSS)

- Navigation/Buttons/Empty States ok
- RBAC serverseitig, keine UI-only Security
- Public-QR: ohne Metrics + Disclaimer exakt
- Logs/Audit/Export konform (keine PII/Secrets, HMAC)
- Upload-Quarantine & Allowlist aktiv
- Keine Pfad-/Altversion-Konflikte (Docs SoT = `.\docs`)
- Lizenzkontrolle: serverseitig enforced + Tests + keine Leaks

---

## 14) Mini-Review (Ja/Nein, schnell)

- Export-Sektion ist aktuell: Vehicle Export korrekt beschrieben; Servicebook/weiteres als „analog geplant“ konsistent?
- Moderator-Regel: überall wirklich nur Blog/News (keine Leaks via Export/Audit/Read)?
- Public-QR Copy: Disclaimer exakt, keine Metrics – wirklich nirgends Zahlen/Zeiträume?
- Lizenzkontrolle: greift serverseitig + kein Logging von Keys/Secrets?

---

## 15) Nächste konkrete Aktion (P0) — Plan der Wahrheit

1) **Lizenzkontrolle sauber finalisieren**
   - Feature→Tier Mapping festziehen
   - Tests (allowed/denied) + Logging-Checks (keine Leaks)

2) **Exports erweitern (vehicle/servicebook/users)**
   - gleiche Mechanik: redacted default, full nur superadmin, grant + TTL + encrypted + audit

3) **SUPERADMIN Bootstrap/Provisioning**
   - out-of-band Script/Seed/Deployment definieren
   - normaler Admin darf superadmin nicht setzen

4) **Cleanup / Konsolidierung**
   - alte/unsichere Patches, init/bak, Doppelpfade entfernen
   - Docs-Index aktuell halten (dieser Checkpoint ist die Klammer)

---

ENDE 99_MASTER_CHECKPOINT
