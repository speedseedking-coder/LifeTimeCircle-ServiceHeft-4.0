# docs/01_DECISIONS.md
# LifeTimeCircle â€“ Service Heft 4.0
**Entscheidungen / SoT (Decisions Log)**  
Stand: **2026-02-06**

> Ziel: Kurze, nachvollziehbare Entscheidungen (warum / was / Konsequenzen).  
> Regel: Wenn etwas nicht explizit erlaubt ist â†’ **deny-by-default**.

---

## D-001: RBAC serverseitig enforced (deny-by-default + least privilege)
**Status:** beschlossen  
**Warum:** Client kann manipuliert werden; Rechte mÃ¼ssen im Backend sicher sein.  
**Konsequenz:** Alle Router haben Dependencies/Gates; Tests prÃ¼fen Guard-Coverage.

---

## D-002: Moderator strikt nur Blog/News
**Status:** beschlossen  
**Warum:** Minimierung von Datenzugriff, keine PII, keine Exports.  
**Konsequenz:** Moderator bekommt Ã¼berall sonst **403** via Router-Dependency `forbid_moderator`.

---

## D-003: Export redacted (PII minimieren, Dokumente nur approved)
**Status:** beschlossen  
**Warum:** Exports sind riskant (Datenabfluss).  
**Konsequenz:** Redaction-Store filtert Dokument-Refs nur auf `APPROVED`.

---

## D-004: Uploads QuarantÃ¤ne-by-default
**Status:** beschlossen  
**Warum:** Uploads sind Angriffspfad (Malware, PII, ungewollte Inhalte).  
**Konsequenz:** Neu hochgeladene Dokumente sind `PENDING/QUARANTINED`; Auslieferung/Export nur bei `APPROVED`.

---

## D-005: Admin-Only QuarantÃ¤ne Review (Approve/Reject/List)
**Status:** beschlossen  
**Warum:** Review ist sicherheitskritisch; least privilege.  
**Konsequenz:** Nur `admin/superadmin` dÃ¼rfen QuarantÃ¤ne-Liste sehen und Approve/Reject ausfÃ¼hren.

---

## D-006: Actor required liefert 401 (unauth) statt 403
**Status:** beschlossen  
**Warum:** Semantik sauber: unauth â†’ 401, auth-but-forbidden â†’ 403.  
**Konsequenz:** `require_actor` wirft 401, nicht 403.

---

## D-007: Upload-Scan Hook + Approve nur bei CLEAN
**Status:** beschlossen  
**Warum:** QuarantÃ¤ne ohne Scan ist zu schwach; Freigabe nur nach Scan.  
**Konsequenz:** `scan_status` Feld + `approve` nur wenn `CLEAN`, sonst 409; Admin-Rescan Endpoint; INFECTED auto-reject.

---

## D-008: Sale/Transfer Status nur fÃ¼r Initiator oder Redeemer (object-level RBAC)
**Status:** beschlossen  
**Warum:** `tid` ist erratbar/teilbar; Status darf nicht fÃ¼r beliebige `vip|dealer` lesbar sein (ID-Leak via `initiator_user_id` / `redeemed_by_user_id`).  
**Konsequenz:** `GET /sale/transfer/status/{tid}` zusÃ¤tzlich zum Role-Gate (`vip|dealer`) nur wenn Actor **Initiator** oder **Redeemer** ist; sonst **403**. Tests mÃ¼ssen das explizit abdecken.

---

## D-009: Produkt ist â€žUnifiedâ€œ (kein Parallelzweig â€ž2.0â€œ)
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
**Konsequenz:** Create/Activate eines 2. Fahrzeugs wird serverseitig gegen Plan/Entitlement geprÃ¼ft (deny-by-default).

---

## D-012: Add-on Gate nur bei Erstaktivierung (Grandfathering)
**Status:** beschlossen  
**Warum:** Bestandskunden dÃ¼rfen keine Funktionsverschlechterung bekommen.  
**Konsequenz:** Paywall greift nur wenn `addon_first_enabled_at == null`; nach erstem Enable bleibt Add-on fÃ¼r Bestandsfahrzeug nutzbar, auch bei Reaktivierung.

---

## D-013: PII-Workflow blockiert Trust T3 solange offen; bestÃ¤tigte PII wird automatisch gelÃ¶scht
**Status:** beschlossen  
**Warum:** PII-Risiko minimieren; Trust darf nicht â€žgrÃ¼nâ€œ werden, solange PII ungeklÃ¤rt ist.  
**Konsequenz:** PII-Status `suspected|confirmed` verhindert T3; `confirmed` triggert Auto-LÃ¶schung nach Default 30 Tagen (konfigurierbar).

---

## D-014: Trusted Upload speichert Hash/Checksum als IntegritÃ¤tssignal
**Status:** beschlossen  
**Warum:** NachweisqualitÃ¤t/Manipulationsresistenz; Basis fÃ¼r Trust.  
**Konsequenz:** Bei Upload wird Hash/Checksum gespeichert und in internen Nachweisen genutzt (public niemals roh dokumentlastig).

---

## D-015: Essentielle Systemlogs sind immutable (OBD/GPS)
**Status:** beschlossen  
**Warum:** Nachweiswert entsteht durch UnverÃ¤nderbarkeit.  
**Konsequenz:** OBD-Log/GPS-Probefahrt-Log sind nicht lÃ¶sch-/editierbar; nur ErgÃ¤nzungen (Dokumentation) erlaubt.

---

## D-016: Zertifikate/Exports haben TTL; Historie bleibt
**Status:** beschlossen  
**Warum:** Minimierung von Datenabfluss; Reproduzierbarkeit per neuer Version.  
**Konsequenz:** Dateien laufen ab/werden gelÃ¶scht; der Historie-Eintrag bleibt, neue Version ersetzt Datei, Historie bleibt.

---

## D-017: End-to-End Nutzerfluss ist bindend (Landing â†’ Eintritt â†’ Rollenwahl â†’ Signup â†’ Consent â†’ VIN â†’ EintrÃ¤ge)
**Status:** beschlossen  
**Warum:** Ohne durchgÃ¤ngigen Flow entsteht Fragmentierung; Onboarding muss sofort produktiven Wert liefern.  
**Konsequenz:** Web/Backend mÃ¼ssen den E2E-Flow unterstÃ¼tzen; Spezifikation liegt in `docs/02_PRODUCT_SPEC_UNIFIED.md`.

---

## D-018: Gewerbe-Typen sind Taxonomie fÃ¼r â€ždurchgefÃ¼hrt vonâ€œ
**Status:** beschlossen  
**Warum:** Vergleichbarkeit/Filterbarkeit der Historie; konsistente Darstellung (Werkstatt vs. Gesetzliches vs. Eigenleistung).  
**Konsequenz:** â€ždurchgefÃ¼hrt vonâ€œ nutzt feste Kategorien: Fachwerkstatt, HÃ¤ndler, Autohaus, Reifenservice, Tuning-Fachbetrieb, Sonstiges, Gesetzliches (TÃœV/Gutachten/Wertgutachten), Eigenleistung.

---

## D-019: Entry-Pflichtfelder + Optionalfelder + UX-Hinweis sind verbindlich
**Status:** beschlossen  
**Warum:** Minimaldaten sichern den roten Faden; optionale Pflege steigert NachweisqualitÃ¤t.  
**Konsequenz:** Server erzwingt Pflichtfelder (Datum, Typ, durchgefÃ¼hrt von, Kilometerstand). UI zeigt bei Optionalfeldern stets: â€žDatenpflege = bessere Trust-Stufe & Verkaufswertâ€œ.

---

## D-020: T1/T2/T3 Definition ist normiert (physisches Serviceheft berÃ¼cksichtigt)
**Status:** beschlossen  
**Warum:** NachtrÃ¤ge mÃ¼ssen nachvollziehbar eingestuft werden.  
**Konsequenz:** T3 = Dokument vorhanden; T2 = physisches Serviceheft vorhanden; T1 = physisches Serviceheft nicht vorhanden.

---

## D-021: Unfallstatus â€žUnbekanntâ€œ deckelt Trust max. Orange; GrÃ¼n erfordert Abschluss bei Unfall
**Status:** beschlossen  
**Warum:** Unklarheit ist ein Risiko; GrÃ¼n darf nicht ohne belastbare Nachweise vergeben werden.  
**Konsequenz:** Public/Intern: â€žUnbekanntâ€œ begrenzt Trust auf Orange. Bei â€žNicht unfallfreiâ€œ ist GrÃ¼n nur mÃ¶glich, wenn Unfalltrust abgeschlossen und belegt ist.

---

## D-022: To-dos starten ab Gelb; VIP priorisiert Top 3, Non-VIP sieht komplette Liste
**Status:** beschlossen  
**Warum:** Gelb ist â€žsolide, aber optimierbarâ€œ; VIP erhÃ¤lt fokussierte Priorisierung.  
**Konsequenz:** To-dos aktiv ab Gelb. VIP: Top-3 Priorisierung. Non-VIP: vollstÃ¤ndige Liste. To-do enthÃ¤lt Systemgrund + optional Owner-Notiz.

---

## D-023: PII-Workflow ist blockierend fÃ¼r T3, Admin-Override auditpflichtig, Auto-LÃ¶schung Default 30 Tage
**Status:** beschlossen  
**Warum:** DSGVO/PII Risiko minimieren; Trust darf nicht T3 erreichen, solange PII ungeklÃ¤rt ist.  
**Konsequenz:** PII suspected/confirmed â†’ nur Owner/Admin sichtbar, T3 blockiert. Admin-Override nur mit Audit. PII confirmed ohne Bereinigung â†’ Auto-LÃ¶schung nach Default 30 Tagen.

---

## D-024: PDFs/Zertifikate haben TTL; Datei wird gelÃ¶scht, Historie bleibt; Erneuerung erfordert User-BestÃ¤tigung
**Status:** beschlossen  
**Warum:** Datenabfluss reduzieren; Nachweise bleiben als Historie erhalten; Re-Issuance bewusst.  
**Konsequenz:** Trust-Zertifikat 90 Tage, Wartungsstand 30 Tage, Inserat-Export 30 Tage (VIP-only), QR-PDF unbegrenzt. Nach Ablauf Datei weg, Historie-Eintrag bleibt. Erneuerung nur nach BestÃ¤tigung.

---

## D-025: Benachrichtigungen: Daily Digest + kritisch sofort; VIP Ruhezeiten nur fÃ¼r E-Mail
**Status:** beschlossen  
**Warum:** Relevanz ohne Spam; VIP erhÃ¤lt Steuerbarkeit.  
**Konsequenz:** Digest tÃ¤glich; kritische Events sofort (u.a. Approvals, essenzielle LÃ¶schungen/Plausi-Checks, AblÃ¤ufe, Unfalltrust nÃ¶tig, To-dos ab Gelb). VIP kann Ruhezeiten fÃ¼r E-Mail setzen; Free nicht.

---

## D-026: Blog/News Content-Workflow: Entwurf â†’ Review â†’ Publish (Publish final durch Superadmin)
**Status:** beschlossen  
**Warum:** QualitÃ¤tssicherung + klare Verantwortlichkeit.  
**Konsequenz:** Moderator erstellt/editiert EntwÃ¼rfe, Admin reviewed, Superadmin verÃ¶ffentlicht final. Moderator bleibt strikt auf Blog/News begrenzt.

---

## D-027: Import ist 2-stufig (Validate â†’ Run) mit Report; Dubletten werden Ã¼bersprungen
**Status:** beschlossen  
**Warum:** Fehler mÃ¼ssen vor dem Schreiben sichtbar sein; Transparenz fÃ¼r DatenqualitÃ¤t.  
**Konsequenz:** Pflicht: Validate-Preview, danach Run. Report ist verpflichtend. Dubletten werden skippt und im Report ausgewiesen.

---

## D-028: Add-on Gate mit Grandfathering ist verbindlich (Neu = addon_first_enabled_at == NULL)
**Status:** beschlossen  
**Warum:** Keine Funktionsverschlechterung fÃ¼r Bestandsfahrzeuge; Gate nur fÃ¼r Neu-Aktivierungen.  
**Konsequenz:** Gate/Paywall greift nur, wenn `addon_first_enabled_at` NULL ist. Sonst bleibt volle Nutzbarkeit erhalten, auch bei Re-Aktivierung. Admin-Schalter: neu erlauben, neu kostenpflichtig, optional admin-only.

## D-003: CI Required Status Check Context muss exakt dem GitHub-Context entsprechen
**Status:** beschlossen  
**Warum:** Branch Protection blockiert PRs mit "Expected", wenn der Required Context nicht exakt dem gemeldeten Status-Context entspricht (z.B. Workflow-Job heißt `CI/pytest`, nicht `pytest`).  
**Konsequenz:** Required status checks auf `CI/pytest` setzen; bei Änderungen am Workflow immer Context-Namen verifizieren (`gh api .../required_status_checks/contexts`).  
**Hinweis (PowerShell):** Kein Bash Here-Doc; JSON an `gh api` via `--input -` per Pipe übergeben.
