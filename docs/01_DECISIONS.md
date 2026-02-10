# docs/01_DECISIONS.md
# LifeTimeCircle â€“ Service Heft 4.0
**Entscheidungen / SoT (Decisions Log)**  
Stand: **2026-02-06**

> Ziel: Kurze, nachvollziehbare Entscheidungen (warum / was / Konsequenzen).  
> Regel: Wenn etwas nicht explizit erlaubt ist ’ **deny-by-default**.

---

## D-001: RBAC serverseitig enforced (deny-by-default + least privilege)
**Status:** beschlossen  
**Warum:** Client kann manipuliert werden; Rechte müssen im Backend sicher sein.  
**Konsequenz:** Alle Router haben Dependencies/Gates; Tests prüfen Guard-Coverage.

---

## D-002: Moderator strikt nur Blog/News
**Status:** beschlossen  
**Warum:** Minimierung von Datenzugriff, keine PII, keine Exports.  
**Konsequenz:** Moderator bekommt überall sonst **403** via Router-Dependency `forbid_moderator`.

---

## D-003: Export redacted (PII minimieren, Dokumente nur approved)
**Status:** beschlossen  
**Warum:** Exports sind riskant (Datenabfluss).  
**Konsequenz:** Redaction-Store filtert Dokument-Refs nur auf `APPROVED`.

---

## D-004: Uploads Quarantäne-by-default
**Status:** beschlossen  
**Warum:** Uploads sind Angriffspfad (Malware, PII, ungewollte Inhalte).  
**Konsequenz:** Neu hochgeladene Dokumente sind `PENDING/QUARANTINED`; Auslieferung/Export nur bei `APPROVED`.

---

## D-005: Admin-Only Quarantäne Review (Approve/Reject/List)
**Status:** beschlossen  
**Warum:** Review ist sicherheitskritisch; least privilege.  
**Konsequenz:** Nur `admin/superadmin` dürfen Quarantäne-Liste sehen und Approve/Reject ausführen.

---

## D-006: Actor required liefert 401 (unauth) statt 403
**Status:** beschlossen  
**Warum:** Semantik sauber: unauth ’ 401, auth-but-forbidden ’ 403.  
**Konsequenz:** `require_actor` wirft 401, nicht 403.

---

## D-007: Upload-Scan Hook + Approve nur bei CLEAN
**Status:** beschlossen  
**Warum:** Quarantäne ohne Scan ist zu schwach; Freigabe nur nach Scan.  
**Konsequenz:** `scan_status` Feld + `approve` nur wenn `CLEAN`, sonst 409; Admin-Rescan Endpoint; INFECTED auto-reject.

---

## D-008: Sale/Transfer Status nur für Initiator oder Redeemer (object-level RBAC)
**Status:** beschlossen  
**Warum:** `tid` ist erratbar/teilbar; Status darf nicht für beliebige `vip|dealer` lesbar sein (ID-Leak via `initiator_user_id` / `redeemed_by_user_id`).  
**Konsequenz:** `GET /sale/transfer/status/{tid}` zusätzlich zum Role-Gate (`vip|dealer`) nur wenn Actor **Initiator** oder **Redeemer** ist; sonst **403**. Tests müssen das explizit abdecken.

---

## D-009: Produkt ist „Unified“ (kein Parallelzweig „2.0“)
**Status:** beschlossen  
**Warum:** Doppelspurigkeit erzeugt Drift; ein Produkt, eine Roadmap.  
**Konsequenz:** Spezifikation liegt zentral in `docs/02_PRODUCT_SPEC_UNIFIED.md` und ist bindend.

---

## D-010: Consent ist versioniert + zeitgestempelt, Re-Consent ist blockierend
**Status:** beschlossen  
**Warum:** Rechtssicherheit/DSGVO; nachvollziehbar, welche Version akzeptiert wurde.  
**Konsequenz:** AGB/Datenschutz speichern: `version` + `accepted_at`; bei neuer Version muss Re-Consent erfolgen, sonst Produkt-Flow gesperrt.

---

## D-011: Paywall-Regel Fahrzeuge (1 gratis, ab 2 kostenpflichtig) ist serverseitig enforced
**Status:** beschlossen  
**Warum:** UI-only Sperren sind trivial zu umgehen.  
**Konsequenz:** Create/Activate eines 2. Fahrzeugs wird serverseitig gegen Plan/Entitlement geprüft (deny-by-default).

---

## D-012: Add-on Gate nur bei Erstaktivierung (Grandfathering)
**Status:** beschlossen  
**Warum:** Bestandskunden dürfen keine Funktionsverschlechterung bekommen.  
**Konsequenz:** Paywall greift nur wenn `addon_first_enabled_at == null`; nach erstem Enable bleibt Add-on für Bestandsfahrzeug nutzbar, auch bei Reaktivierung.

---

## D-013: PII-Workflow blockiert Trust T3 solange offen; bestätigte PII wird automatisch gelöscht
**Status:** beschlossen  
**Warum:** PII-Risiko minimieren; Trust darf nicht „grün“ werden, solange PII ungeklärt ist.  
**Konsequenz:** PII-Status `suspected|confirmed` verhindert T3; `confirmed` triggert Auto-Löschung nach Default 30 Tagen (konfigurierbar).

---

## D-014: Trusted Upload speichert Hash/Checksum als Integritätssignal
**Status:** beschlossen  
**Warum:** Nachweisqualität/Manipulationsresistenz; Basis für Trust.  
**Konsequenz:** Bei Upload wird Hash/Checksum gespeichert und in internen Nachweisen genutzt (public niemals roh dokumentlastig).

---

## D-015: Essentielle Systemlogs sind immutable (OBD/GPS)
**Status:** beschlossen  
**Warum:** Nachweiswert entsteht durch Unveränderbarkeit.  
**Konsequenz:** OBD-Log/GPS-Probefahrt-Log sind nicht lösch-/editierbar; nur Ergänzungen (Dokumentation) erlaubt.

---

## D-016: Zertifikate/Exports haben TTL; Historie bleibt
**Status:** beschlossen  
**Warum:** Minimierung von Datenabfluss; Reproduzierbarkeit per neuer Version.  
**Konsequenz:** Dateien laufen ab/werden gelöscht; der Historie-Eintrag bleibt, neue Version ersetzt Datei, Historie bleibt.

---

## D-017: End-to-End Nutzerfluss ist bindend (Landing ’ Eintritt ’ Rollenwahl ’ Signup ’ Consent ’ VIN ’ Einträge)
**Status:** beschlossen  
**Warum:** Ohne durchgängigen Flow entsteht Fragmentierung; Onboarding muss sofort produktiven Wert liefern.  
**Konsequenz:** Web/Backend müssen den E2E-Flow unterstützen; Spezifikation liegt in `docs/02_PRODUCT_SPEC_UNIFIED.md`.

---

## D-018: Gewerbe-Typen sind Taxonomie für „durchgeführt von“
**Status:** beschlossen  
**Warum:** Vergleichbarkeit/Filterbarkeit der Historie; konsistente Darstellung (Werkstatt vs. Gesetzliches vs. Eigenleistung).  
**Konsequenz:** „durchgeführt von“ nutzt feste Kategorien: Fachwerkstatt, Händler, Autohaus, Reifenservice, Tuning-Fachbetrieb, Sonstiges, Gesetzliches (TÃœV/Gutachten/Wertgutachten), Eigenleistung.

---

## D-019: Entry-Pflichtfelder + Optionalfelder + UX-Hinweis sind verbindlich
**Status:** beschlossen  
**Warum:** Minimaldaten sichern den roten Faden; optionale Pflege steigert Nachweisqualität.  
**Konsequenz:** Server erzwingt Pflichtfelder (Datum, Typ, durchgeführt von, Kilometerstand). UI zeigt bei Optionalfeldern stets: „Datenpflege = bessere Trust-Stufe & Verkaufswert“.

---

## D-020: T1/T2/T3 Definition ist normiert (physisches Serviceheft berücksichtigt)
**Status:** beschlossen  
**Warum:** Nachträge müssen nachvollziehbar eingestuft werden.  
**Konsequenz:** T3 = Dokument vorhanden; T2 = physisches Serviceheft vorhanden; T1 = physisches Serviceheft nicht vorhanden.

---

## D-021: Unfallstatus „Unbekannt“ deckelt Trust max. Orange; Grün erfordert Abschluss bei Unfall
**Status:** beschlossen  
**Warum:** Unklarheit ist ein Risiko; Grün darf nicht ohne belastbare Nachweise vergeben werden.  
**Konsequenz:** Public/Intern: „Unbekannt“ begrenzt Trust auf Orange. Bei „Nicht unfallfrei“ ist Grün nur möglich, wenn Unfalltrust abgeschlossen und belegt ist.

---

## D-022: To-dos starten ab Gelb; VIP priorisiert Top 3, Non-VIP sieht komplette Liste
**Status:** beschlossen  
**Warum:** Gelb ist „solide, aber optimierbar“; VIP erhält fokussierte Priorisierung.  
**Konsequenz:** To-dos aktiv ab Gelb. VIP: Top-3 Priorisierung. Non-VIP: vollständige Liste. To-do enthält Systemgrund + optional Owner-Notiz.

---

## D-023: PII-Workflow ist blockierend für T3, Admin-Override auditpflichtig, Auto-Löschung Default 30 Tage
**Status:** beschlossen  
**Warum:** DSGVO/PII Risiko minimieren; Trust darf nicht T3 erreichen, solange PII ungeklärt ist.  
**Konsequenz:** PII suspected/confirmed ’ nur Owner/Admin sichtbar, T3 blockiert. Admin-Override nur mit Audit. PII confirmed ohne Bereinigung ’ Auto-Löschung nach Default 30 Tagen.

---

## D-024: PDFs/Zertifikate haben TTL; Datei wird gelöscht, Historie bleibt; Erneuerung erfordert User-Bestätigung
**Status:** beschlossen  
**Warum:** Datenabfluss reduzieren; Nachweise bleiben als Historie erhalten; Re-Issuance bewusst.  
**Konsequenz:** Trust-Zertifikat 90 Tage, Wartungsstand 30 Tage, Inserat-Export 30 Tage (VIP-only), QR-PDF unbegrenzt. Nach Ablauf Datei weg, Historie-Eintrag bleibt. Erneuerung nur nach Bestätigung.

---

## D-025: Benachrichtigungen: Daily Digest + kritisch sofort; VIP Ruhezeiten nur für E-Mail
**Status:** beschlossen  
**Warum:** Relevanz ohne Spam; VIP erhält Steuerbarkeit.  
**Konsequenz:** Digest täglich; kritische Events sofort (u.a. Approvals, essenzielle Löschungen/Plausi-Checks, Abläufe, Unfalltrust nötig, To-dos ab Gelb). VIP kann Ruhezeiten für E-Mail setzen; Free nicht.

---

## D-026: Blog/News Content-Workflow: Entwurf ’ Review ’ Publish (Publish final durch Superadmin)
**Status:** beschlossen  
**Warum:** Qualitätssicherung + klare Verantwortlichkeit.  
**Konsequenz:** Moderator erstellt/editiert Entwürfe, Admin reviewed, Superadmin veröffentlicht final. Moderator bleibt strikt auf Blog/News begrenzt.

---

## D-027: Import ist 2-stufig (Validate ’ Run) mit Report; Dubletten werden übersprungen
**Status:** beschlossen  
**Warum:** Fehler müssen vor dem Schreiben sichtbar sein; Transparenz für Datenqualität.  
**Konsequenz:** Pflicht: Validate-Preview, danach Run. Report ist verpflichtend. Dubletten werden skippt und im Report ausgewiesen.

---

## D-028: Add-on Gate mit Grandfathering ist verbindlich (Neu = addon_first_enabled_at == NULL)
**Status:** beschlossen  
**Warum:** Keine Funktionsverschlechterung für Bestandsfahrzeuge; Gate nur für Neu-Aktivierungen.  
**Konsequenz:** Gate/Paywall greift nur, wenn `addon_first_enabled_at` NULL ist. Sonst bleibt volle Nutzbarkeit erhalten, auch bei Re-Aktivierung. Admin-Schalter: neu erlauben, neu kostenpflichtig, optional admin-only.

## D-003: CI Required Status Check Context muss exakt dem GitHub-Context entsprechen
**Status:** beschlossen  
**Warum:** Branch Protection blockiert PRs mit "Expected", wenn der Required Context nicht exakt dem gemeldeten Status-Context entspricht (z.B. Workflow-Job heißt `CI/pytest`, nicht `pytest`).  
**Konsequenz:** Required status checks auf `CI/pytest` setzen; bei Änderungen am Workflow immer Context-Namen verifizieren (`gh api .../required_status_checks/contexts`).  
**Hinweis (PowerShell):** Kein Bash Here-Doc; JSON an `gh api` via `--input -` per Pipe übergeben.
---

## D-030: CI Guard verhindert Drift/Rename des Required Checks pytest
**Status:** beschlossen  
**Warum:** Branch Protection required checks hängen am stabilen **Check-Run/Job-Namen** (pytest). Wenn der Job-Key/Name driftet/umbenannt wird, zeigt GitHub oft „Expected/Waiting“ und blockt Merges.  
**Konsequenz:**  
- CI führt vor Tests einen Guard aus: server/scripts/ci_guard_required_job_pytest.ps1  
- Guard bricht CI ab, wenn jobs: -> pytest: im Workflow fehlt (Fail-fast statt „hängen“)  
- Required Check bleibt stabil: Branch Protection strict=true + required pytest


<<<<<<< HEAD
## DEC-2026-02-09 – Web Pages Scaffold ist MVP-Standard + IST-ZUSTAND Voll-Check als Merge-Gate

**Status:** angenommen  
**Datum:** 2026-02-09  
**Kontext / Anlass:** PR #103 („feat/web pages scaffold“) wurde erfolgreich gemerged. CI war vollständig grün und der lokale Voll-Check bestätigt den erwarteten Projektzustand.

### Entscheidung
1) **Web-Pages-Scaffold (App + Pages) ist ab jetzt Mindeststandard** für das Web-Paket:
   - `packages/web/src/pages/*` enthält: Auth, Consent, Vehicles, VehicleDetail, Documents, PublicQr.
2) **Merge-Gate besteht aus CI + lokalem IST-ZUSTAND Voll-Check**:
   - CI muss grün sein (mindestens): `CI/pytest`, `CI/web_build`, `CI/web/web_build`.
   - Lokal muss nach dem Merge laufen: `pwsh -NoProfile -ExecutionPolicy Bypass -File .\server\scripts\ltc_verify_ist_zustand.ps1`
3) **Public-QR Pflichttext wird als SoT-konform verifiziert** und muss weiterhin exakt vorhanden sein:
   - verifiziert in `packages/web/src/components/TrustAmpelDisclaimer.tsx`
   - verifiziert in `packages/web/src/pages/PublicQrPage.tsx`
4) **API-Client-Policy wird aktiv geprüft**:
   - Bearer/401/POST Muster vorhanden (api.ts),
   - keine dev/actor header im Web-Client.

### Evidenz (nachweisbar)
- PR #103: CI Checks grün (3/3): `CI/pytest`, `CI/web_build`, `CI/web/web_build`.
- Lokaler IST-ZUSTAND Voll-Check (`ltc_verify_ist_zustand.ps1`) grün inkl.:
  - Repo clean + sync (main, HEAD fb44fc5)
  - SoT-Pflichtdateien vorhanden
  - Web Pages vorhanden (inkl. PublicQrPage)
  - Pflicht-Disclaimer exakt gefunden (2 Stellen)
  - pytest grün (mit `LTC_SECRET_KEY`)
  - `npm ci` + `npm run build` grün

### Konsequenzen
- PRs gelten erst als „fertig“, wenn **CI grün** UND **lokaler IST-ZUSTAND Voll-Check grün**.
- Public-QR bleibt datenarm; Pflicht-Disclaimer darf nicht verändert werden.
=======
>>>>>>> 018a2ca (docs: fix title dash encoding in decisions log)

