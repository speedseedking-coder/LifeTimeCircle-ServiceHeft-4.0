# LifeTimeCircle - Service Heft 4.0
**Entscheidungen / SoT (Decisions Log)**  
Stand: **2026-02-15**

> Ziel: Kurze, nachvollziehbare Entscheidungen (warum / was / Konsequenzen).  
> Regel: Wenn etwas nicht explizit erlaubt ist -> **deny-by-default**.

---

## D-001: RBAC serverseitig enforced (deny-by-default + least privilege)
**Status:** beschlossen  
**Warum:** Client kann manipuliert werden; Rechte muessen im Backend sicher sein.  
**Konsequenz:** Alle Router haben Dependencies/Gates; Tests pruefen Guard-Coverage.

---

## D-002: Moderator strikt nur Blog/News
**Status:** beschlossen  
**Warum:** Minimierung von Datenzugriff, keine PII, keine Exports.  
**Konsequenz:** Moderator bekommt ueberall sonst **403** via Router-Dependency `forbid_moderator`.

---

## D-003: Export redacted (PII minimieren, Dokumente nur approved)
**Status:** beschlossen  
**Warum:** Exports sind riskant (Datenabfluss).  
**Konsequenz:** Redaction-Store filtert Dokument-Refs nur auf `APPROVED`.

---

## D-004: Uploads Quarantaene-by-default
**Status:** beschlossen  
**Warum:** Uploads sind Angriffspfad (Malware, PII, ungewollte Inhalte).  
**Konsequenz:** Neu hochgeladene Dokumente sind `PENDING/QUARANTINED`; Auslieferung/Export nur bei `APPROVED`.

---

## D-005: Admin-Only Quarantaene Review (Approve/Reject/List)
**Status:** beschlossen  
**Warum:** Review ist sicherheitskritisch; least privilege.  
**Konsequenz:** Nur `admin/superadmin` duerfen Quarantaene-Liste sehen und Approve/Reject ausfuehren.

---

## D-006: Actor required liefert 401 (unauth) statt 403
**Status:** beschlossen  
**Warum:** Semantik sauber: unauth -> 401, auth-but-forbidden -> 403.  
**Konsequenz:** `require_actor` wirft 401, nicht 403.

---

## D-007: Upload-Scan Hook + Approve nur bei CLEAN
**Status:** beschlossen  
**Warum:** Quarantaene ohne Scan ist zu schwach; Freigabe nur nach Scan.  
**Konsequenz:** `scan_status` Feld + `approve` nur wenn `CLEAN`, sonst 409; Admin-Rescan Endpoint; `INFECTED` auto-reject.

---

## D-008: Sale/Transfer Status nur fuer Initiator oder Redeemer (object-level RBAC)
**Status:** beschlossen  
**Warum:** `tid` ist erratbar/teilbar; Status darf nicht fuer beliebige `vip|dealer` lesbar sein (ID-Leak via `initiator_user_id` / `redeemed_by_user_id`).  
**Konsequenz:** `GET /sale/transfer/status/{tid}` zusaetzlich zum Role-Gate (`vip|dealer`) nur wenn Actor **Initiator** oder **Redeemer** ist; sonst **403**. Tests muessen das explizit abdecken.

---

## D-009: Produkt ist "Unified" (kein Parallelzweig "2.0")
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
**Konsequenz:** Create/Activate eines 2. Fahrzeugs wird serverseitig gegen Plan/Entitlement geprueft (deny-by-default).

---

## D-012: Add-on Gate nur bei Erstaktivierung (Grandfathering)
**Status:** beschlossen  
**Warum:** Bestandskunden duerfen keine Funktionsverschlechterung bekommen.  
**Konsequenz:** Paywall greift nur wenn `addon_first_enabled_at == null`; nach erstem Enable bleibt Add-on fuer Bestandsfahrzeug nutzbar, auch bei Reaktivierung.

---

## D-013: PII-Workflow blockiert Trust T3 solange offen; bestaetigte PII wird automatisch geloescht
**Status:** beschlossen  
**Warum:** PII-Risiko minimieren; Trust darf nicht "gruen" werden, solange PII ungeklaert ist.  
**Konsequenz:** PII-Status `suspected|confirmed` verhindert T3; `confirmed` triggert Auto-Loeschung nach Default 30 Tagen (konfigurierbar).

---

## D-014: Trusted Upload speichert Hash/Checksum als Integritaetssignal
**Status:** beschlossen  
**Warum:** Nachweisqualitaet/Manipulationsresistenz; Basis fuer Trust.  
**Konsequenz:** Bei Upload wird Hash/Checksum gespeichert und in internen Nachweisen genutzt (public niemals roh dokumentlastig).

---

## D-015: Essentielle Systemlogs sind immutable (OBD/GPS)
**Status:** beschlossen  
**Warum:** Nachweiswert entsteht durch Unveraenderbarkeit.  
**Konsequenz:** OBD-Log/GPS-Probefahrt-Log sind nicht loesch-/editierbar; nur Ergaenzungen (Dokumentation) erlaubt.

---

## D-016: Zertifikate/Exports haben TTL; Historie bleibt
**Status:** beschlossen  
**Warum:** Minimierung von Datenabfluss; Reproduzierbarkeit per neuer Version.  
**Konsequenz:** Dateien laufen ab/werden geloescht; der Historie-Eintrag bleibt, neue Version ersetzt Datei, Historie bleibt.

---

## D-017: End-to-End Nutzerfluss ist bindend (Landing -> Eintritt -> Rollenwahl -> Signup -> Consent -> VIN -> Eintraege)
**Status:** beschlossen  
**Warum:** Ohne durchgaengigen Flow entsteht Fragmentierung; Onboarding muss sofort produktiven Wert liefern.  
**Konsequenz:** Web/Backend muessen den E2E-Flow unterstuetzen; Spezifikation liegt in `docs/02_PRODUCT_SPEC_UNIFIED.md`.

---

## D-018: Gewerbe-Typen sind Taxonomie fuer "durchgefuehrt von"
**Status:** beschlossen  
**Warum:** Vergleichbarkeit/Filterbarkeit der Historie; konsistente Darstellung (Werkstatt vs. Gesetzliches vs. Eigenleistung).  
**Konsequenz:** "durchgefuehrt von" nutzt feste Kategorien: Fachwerkstatt, Haendler, Autohaus, Reifenservice, Tuning-Fachbetrieb, Sonstiges, Gesetzliches (TUEV/Gutachten/Wertgutachten), Eigenleistung.

---

## D-019: Entry-Pflichtfelder + Optionalfelder + UX-Hinweis sind verbindlich
**Status:** beschlossen  
**Warum:** Minimaldaten sichern den roten Faden; optionale Pflege steigert Nachweisqualitaet.  
**Konsequenz:** Server erzwingt Pflichtfelder (Datum, Typ, durchgefuehrt von, Kilometerstand). UI zeigt bei Optionalfeldern stets: "Datenpflege = bessere Trust-Stufe & Verkaufswert".

---

## D-020: T1/T2/T3 Definition ist normiert (physisches Serviceheft beruecksichtigt)
**Status:** beschlossen  
**Warum:** Nachtraege muessen nachvollziehbar eingestuft werden.  
**Konsequenz:** T3 = Dokument vorhanden; T2 = physisches Serviceheft vorhanden; T1 = physisches Serviceheft nicht vorhanden.

---

## D-021: Unfallstatus "Unbekannt" deckelt Trust max. Orange; Gruen erfordert Abschluss bei Unfall
**Status:** beschlossen  
**Warum:** Unklarheit ist ein Risiko; Gruen darf nicht ohne belastbare Nachweise vergeben werden.  
**Konsequenz:** Public/Intern: "Unbekannt" begrenzt Trust auf Orange. Bei "Nicht unfallfrei" ist Gruen nur moeglich, wenn Unfalltrust abgeschlossen und belegt ist.

---

## D-022: To-dos starten ab Gelb; VIP priorisiert Top 3, Non-VIP sieht komplette Liste
**Status:** beschlossen  
**Warum:** Gelb ist "solide, aber optimierbar"; VIP erhaelt fokussierte Priorisierung.  
**Konsequenz:** To-dos aktiv ab Gelb. VIP: Top-3 Priorisierung. Non-VIP: vollstaendige Liste. To-do enthaelt Systemgrund + optional Owner-Notiz.

---

## D-023: PII-Workflow ist blockierend fuer T3, Admin-Override auditpflichtig, Auto-Loeschung Default 30 Tage
**Status:** beschlossen  
**Warum:** DSGVO/PII Risiko minimieren; Trust darf nicht T3 erreichen, solange PII ungeklaert ist.  
**Konsequenz:** PII `suspected|confirmed` -> nur Owner/Admin sichtbar, T3 blockiert. Admin-Override nur mit Audit. PII confirmed ohne Bereinigung -> Auto-Loeschung nach Default 30 Tagen.

---

## D-024: PDFs/Zertifikate haben TTL; Datei wird geloescht, Historie bleibt; Erneuerung erfordert User-Bestaetigung
**Status:** beschlossen  
**Warum:** Datenabfluss reduzieren; Nachweise bleiben als Historie erhalten; Re-Issuance bewusst.  
**Konsequenz:** Trust-Zertifikat 90 Tage, Wartungsstand 30 Tage, Inserat-Export 30 Tage (VIP-only), QR-PDF unbegrenzt. Nach Ablauf Datei weg, Historie-Eintrag bleibt. Erneuerung nur nach Bestaetigung.

---

## D-025: Benachrichtigungen: Daily Digest + kritisch sofort; VIP Ruhezeiten nur fuer E-Mail
**Status:** beschlossen  
**Warum:** Relevanz ohne Spam; VIP erhaelt Steuerbarkeit.  
**Konsequenz:** Digest taeglich; kritische Events sofort (u.a. Approvals, essentielle Loeschungen/Plausi-Checks, Ablaeufe, Unfalltrust noetig, To-dos ab Gelb). VIP kann Ruhezeiten fuer E-Mail setzen; Free nicht.

---

## D-026: Blog/News Content-Workflow: Entwurf -> Review -> Publish (Publish final durch Superadmin)
**Status:** beschlossen  
**Warum:** Qualitaetssicherung + klare Verantwortlichkeit.  
**Konsequenz:** Moderator erstellt/editiert Entwuerfe, Admin reviewed, Superadmin veroeffentlicht final. Moderator bleibt strikt auf Blog/News begrenzt.

---

## D-027: Import ist 2-stufig (Validate -> Run) mit Report; Dubletten werden uebersprungen
**Status:** beschlossen  
**Warum:** Fehler muessen vor dem Schreiben sichtbar sein; Transparenz fuer Datenqualitaet.  
**Konsequenz:** Pflicht: Validate-Preview, danach Run. Report ist verpflichtend. Dubletten werden skippt und im Report ausgewiesen.

---

## D-028: Add-on Gate mit Grandfathering ist verbindlich (Neu = addon_first_enabled_at == NULL)
**Status:** beschlossen  
**Warum:** Keine Funktionsverschlechterung fuer Bestandsfahrzeuge; Gate nur fuer Neu-Aktivierungen.  
**Konsequenz:** Gate/Paywall greift nur, wenn `addon_first_enabled_at` NULL ist. Sonst bleibt volle Nutzbarkeit erhalten, auch bei Re-Aktivierung. Admin-Schalter: neu erlauben, neu kostenpflichtig, optional admin-only.

---

## D-029: Required Check ist Check-Run/Job-Name `pytest` (drift-proof)
**Status:** beschlossen  
**Warum:** Branch Protection haengt am stabilen Check-Run/Job-Namen. Falsche/alte Status-Contexts fuehren zu "Expected/Waiting" und blockieren PRs.  
**Konsequenz:**  
- Branch Protection Required Check: **`pytest`** (Check-Run/Job-Name).  
- Verifikation erfolgt ueber **check-runs** (nicht ueber alte "contexts"), z.B. via `gh pr checks` oder `gh api .../check-runs`.  
- Bei Workflow-Aenderungen muss sichergestellt sein, dass der Job/Check weiterhin **`pytest`** heisst.

---

## D-030: CI Guard verhindert Drift/Rename des Required Checks `pytest`
**Status:** beschlossen  
**Warum:** Wenn der `pytest`-Job umbenannt/entfernt wird, blockt Branch Protection ("Expected/Waiting") oder driftet still.  
**Konsequenz:**  
- CI fuehrt vor Tests einen Guard aus: `server/scripts/ci_guard_required_job_pytest.ps1`  
- Guard bricht CI ab, wenn `jobs: -> pytest:` im Workflow fehlt (Fail-fast statt "haengen")  
- Required Check bleibt stabil: Branch Protection strict=true + required `pytest`

---

## DEC-2026-02-09 - Web Pages Scaffold ist MVP-Standard + IST-ZUSTAND Voll-Check als Merge-Gate
**Status:** angenommen  
**Datum:** 2026-02-09  
**Kontext / Anlass:** Web Pages Scaffold ist als MVP-Standard gesetzt; Merge-Qualitaet wird durch CI + lokalen Voll-Check abgesichert.

### Entscheidung
1) **Web-Pages-Scaffold (App + Pages) ist ab jetzt Mindeststandard** fuer das Web-Paket:
   - `packages/web/src/pages/*` enthaelt: Auth, Consent, Vehicles, VehicleDetail, Documents, PublicQr.
2) **Merge-Gate besteht aus GitHub Required Check + lokalem IST-ZUSTAND Voll-Check**:
   - GitHub Required Check: **`pytest`** (Check-Run/Job-Name, drift-proof).
   - Lokal (Windows): `pwsh -NoProfile -ExecutionPolicy Bypass -File .\server\scripts\ltc_verify_ist_zustand.ps1`
     (falls zusaetzlich eine Python-Variante existiert, ist sie gleichwertig).
   - Erwartung: CI insgesamt gruen (inkl. Web Build Jobs, falls vorhanden).
3) **Public-QR Pflichttext wird SoT-konform verifiziert** und muss weiterhin exakt vorhanden sein:
   - verifiziert in `packages/web/src/components/TrustAmpelDisclaimer.tsx`
   - verifiziert in `packages/web/src/pages/PublicQrPage.tsx`
4) **API-Client-Policy wird aktiv geprueft**:
   - Bearer/401/POST Muster vorhanden (api.ts),
   - keine dev/actor header im Web-Client.

### Konsequenzen
- PRs gelten erst als "fertig", wenn **Required Check `pytest` gruen** UND **lokaler IST-ZUSTAND Voll-Check gruen**.
- Public-QR bleibt datenarm; Pflicht-Disclaimer darf nicht veraendert werden.
---

## D-031: Preflight Remote-Gate verlangt echten `origin` + `git ls-remote --heads origin`
**Status:** beschlossen  
**Warum:** Ein lokaler Pfad als `origin` (z.B. `.`) kann Fetch kuenstlich "gruen" machen, prueft aber keinen realen PR-Flow gegen ein Remote-Repository.  
**Konsequenz:**  
- Gate ist nur gruen, wenn `git remote -v` einen echten Remote-URL zeigt (kein lokaler Pfad wie `.` oder Dateisystempfad).  
- Zusaetzlich muss `git ls-remote --heads origin` erfolgreich laufen (Erreichbarkeit + Auth pruefbar).  
- Bei Fail: **STOP**, keine weiteren Commits/PR-Aktionen bis Remote korrekt konfiguriert ist.

