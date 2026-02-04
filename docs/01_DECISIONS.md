
---

### `docs/01_DECISIONS.md`
```md
# LifeTimeCircle – Service Heft 4.0
**Entscheidungen / SoT (Decisions Log)**  
Stand: 2026-02-04

> Ziel: Kurze, nachvollziehbare Entscheidungen (warum / was / Konsequenzen).  
> Regel: Wenn etwas nicht explizit erlaubt ist → **deny-by-default**.

---

## D-001: RBAC serverseitig enforced (deny-by-default + least privilege)
**Status:** beschlossen  
**Warum:** Client kann manipuliert werden; Rechte müssen im Backend sicher sein.  
**Konsequenz:** Alle Router haben Dependencies/Gates; Tests prüfen Guard-Coverage.

---

## D-002: Moderator strikt nur Blog/News
**Status:** beschlossen  
**Warum:** Minimierung von Datenzugriff, keine PII, keine Exports.  
**Konsequenz:** `forbid_moderator` auf allen deny-Routen (nicht Blog/News).

---

## D-003: Public-QR zeigt nur Dokumentations-/Nachweisqualität (Trustscore)
**Status:** beschlossen  
**Warum:** Keine technische Zustandsbewertung, keine Haftungs-/Fehlinterpretationsrisiken.  
**Konsequenz:** Trustscore-Ampel bewertet nur Nachweise (keine „Vehicle health“).

---

## D-004: Export-Design mit Redaction-by-default
**Status:** beschlossen  
**Warum:** Privacy by design; Full Export ist High-Risk.  
**Konsequenz:** Redacted Export Standard; Full Export nur via One-Time-Token + TTL + Superadmin.

---

## D-005: Consent-Dokumente als Single Source of Truth
**Warum:** Rechts-/Policy-Änderungen müssen versioniert und nachvollziehbar sein.  
**Konsequenz:** `app/consent/policy.py` definiert required docs + Versions; Store/Router nutzen SoT.

---

## D-006 | Produktionsreife (keine Demo)
**Datum:** 2026-01-27  
**Entscheidung:** Oberste Prämisse: **benutzerfertig/produktionsreif** umsetzen, kein Demo-Charakter.

---

## D-007 | Verkauf/Übergabe-QR & interner Verkauf eingeschränkt
**Datum:** 2026-01-27  
**Entscheidung:** Fahrzeugverkauf (Übergabe-QR/Code) und interner Verkauf sind **nur** für **VIP-Nutzer** und **Händler (gewerblich / DEALER)** verfügbar.

---

## D-008 | Public-QR Mini-Check: Ampelsystem & Bedeutung
**Datum:** 2026-01-30  
**Entscheidung:** Public-QR Mini-Check nutzt 4-stufige Ampel **Rot/Orange/Gelb/Grün** und bewertet **nur** Dokumentations-/Nachweisqualität, **nicht** den technischen Zustand.  
**Zusatzregeln:** Public Response enthält **keine Metrics/Counts/Percentages/Zeiträume**; Disclaimer ist Pflicht (exakt, ohne Abwandlung):
> „Die Trust-Ampel bewertet ausschließlich die Dokumentations- und Nachweisqualität. Sie ist keine Aussage über den technischen Zustand des Fahrzeugs.“

---

## D-009 | Public-QR Mini-Check: Kriterien (high-level)
**Datum:** 2026-01-27  
**Entscheidung:** Kriterien für Trust-Level:
- Historie vorhanden
- Verifizierungsgrad (T3/T2/T1)
- Aktualität/Regelmäßigkeit (ohne Metriken)
- Unfalltrust: Für **Grün** bei Unfall nur bei **Abschluss + Belegen**

---

## D-010 | VIP-Gewerbe Mitarbeiterplätze (Staff-Limit + Freigabe-Gate)
**Datum:** 2026-01-30  
**Entscheidung:** VIP-Gewerbe: **max. 2 Staff**; Freigabe/Aktivierung nur durch **SUPERADMIN** (serverseitig enforced).  
**Hinweis:** Normale Admin-Endpunkte dürfen **kein** SUPERADMIN-Provisioning durchführen (out-of-band Bootstrap/Seed/Deployment).

---

## D-011 | Moderatoren: Akkreditierung & Zugriff (strikt)
**Datum:** 2026-01-30  
**Entscheidung:** Moderator: Zugriff **nur** auf Blog/News.  
**Explizit verboten:** Vehicles/Entries/Documents/Verification, **kein Export**, **kein Audit-Read**, **keine PII/Halterdaten**.

---

## D-012 | Landingpage Layout-Standard (Login-Panel)
**Datum:** 2026-01-30  
**Entscheidung:** Landingpage: Hauptseite mit Erklärtext, obere Headerbar mit Modulen/Tools, Login-Panel (E-Mail-Login + OTP/Magic-Link) links/rechts anordbar. Standard: **links**.

---

## D-013 | Blogbase + Newsletter
**Datum:** 2026-01-27  
**Entscheidung:** Frontpage hat aktivierbare **Blogbase** (Admin-News) und **Newsletter** zur wechselseitigen Kommunikation.

---

## D-014 | Projekt-Kontakt-E-Mail
**Datum:** 2026-01-27  
**Entscheidung:** Kontakt-E-Mail: **lifetimecircle@online.de**

---

## D-015 | Exports: Redacted Default + Full Export Gate
**Datum:** 2026-01-30  
**Entscheidung:** Exports sind standardmäßig **redacted** (keine Klartext-PII, keine Secrets; Pseudonyme via HMAC).  
**Full Export:** nur **SUPERADMIN** mit **one-time Grant-Token**, **TTL/Limit**, **Audit ohne PII/Secrets** und **verschlüsselter Response**; Tokens werden niemals im Klartext geloggt.

---

## D-016 | Uploads: Quarantine-by-default + Admin-Freigabe (P0 Security)
**Datum:** 2026-02-04  
**Entscheidung:** Dokument-Uploads sind **standardmäßig in Quarantäne** (`PENDING/QUARANTINED`) und werden erst nach Freigabe **APPROVED** für Nutzer abrufbar.  
**Regeln:**
- Keine öffentlichen Uploads (kein StaticFiles-Mount auf Storage).
- Download/Content für `user/vip/dealer` nur bei **APPROVED** und nur im erlaubten Scope.
- Quarantäne-Liste + Review + Approve/Reject nur **admin/superadmin**.
- Allowlist + Limits sind verpflichtend; alles andere wird abgelehnt (deny-by-default).
**Konsequenz:** RBAC-Guards + Tests müssen diese Gates serverseitig nachweisen (Moderator bleibt strikt nur Blog/News).
