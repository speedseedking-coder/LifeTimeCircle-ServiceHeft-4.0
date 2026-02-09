\# docs/00\_CODEX\_CONTEXT.md

\# LifeTimeCircle – Service Heft 4.0 (Codex-Context / Arbeitsbriefing)

Stand: 2026-02-08



Ziel dieses Dokuments: Codex/Agenten sollen ohne Rückfragen sofort „richtig“ im Repo arbeiten können.

Repo liegt lokal weiterhin unter:

<REPO-ROOT>



------------------------------------------------------------

0\) SOURCE OF TRUTH (SoT) + Konflikt-Priorität (bindend)

------------------------------------------------------------

SoT ist ausschließlich ./docs (keine Altpfade/Parallel-Spezifikationen).



Pflicht-Reihenfolge beim Nachschlagen / bei Konflikten:

1\) docs/99\_MASTER\_CHECKPOINT.md

2\) docs/02\_PRODUCT\_SPEC\_UNIFIED.md

3\) docs/03\_RIGHTS\_MATRIX.md

4\) docs/01\_DECISIONS.md

5\) server/ (Implementierung)

6\) Backlog/sonstiges



Wichtig: Einige SoT-Dateien wurden zeitweise mit „Block x/x … ```md“ Wrappern gespeichert.

Wenn das im Repo noch so ist: Inhalt innerhalb des ```md Codeblocks ist maßgeblich.



------------------------------------------------------------

1\) HARTE INVARIANTEN (Security/Policy) – niemals brechen

------------------------------------------------------------

\- deny-by-default + least privilege (jede Route explizit gated)

\- RBAC serverseitig enforced + object-level checks (Owner/Business/Scope)

\- Moderator strikt nur Blog/News; sonst überall 403

\- Actor required: ohne Actor -> 401 (unauth), nicht 403

\- Keine PII/Secrets in Logs/Responses/Exports (auch nicht in Debug-Ausgaben)

\- Uploads: Quarantäne-by-default, Approve nur nach Scan CLEAN

\- Exports: für Nicht-Admins nur redacted; Dokument-Refs nur APPROVED

\- Public QR Pflichttext exakt unverändert (siehe unten)



Env-Hinweis:

\- Export/Redaction/HMAC braucht LTC\_SECRET\_KEY (>=16) – Tests/DEV setzen ihn explizit.



------------------------------------------------------------

2\) PRODUKT (Unified) – was gebaut wird

------------------------------------------------------------

Bindende Produktspezifikation:

\- docs/02\_PRODUCT\_SPEC\_UNIFIED.md



Kernidee:

\- Digitales Serviceheft + Nachweis-/Dokumentationsqualität -> Trust-Ampel

\- Trust-Ampel ist KEINE technische Zustandsbewertung.



Pflicht-Disclaimer (Public-QR, exakt):

„Die Trust-Ampel bewertet ausschließlich die Dokumentations- und Nachweisqualität. Sie ist keine Aussage über den technischen Zustand des Fahrzeugs.“



------------------------------------------------------------

3\) ROUTING/RBAC (wer darf was) – Einstieg

------------------------------------------------------------

Bindend:

\- docs/03\_RIGHTS\_MATRIX.md



Globalregeln (Kurzform):

\- Moderator Allowlist (alles andere 403):

&nbsp; /auth/\*, /health, /public/\*, /blog/\*, /news/\*

\- Objektbezogene Routen: immer object-level checks zusätzlich zum Role-Gate



Wichtige Route-Gruppen (Details in Rights Matrix):

\- Public: /public/\*, /blog/\* read, /news/\* read

\- Auth/Consent: /auth/\*, /consent/\*

\- Vehicles: /vehicles/\*, /collections/\*

\- Entries/Gallery/Archive/Invoices: /vehicles/{id}/entries/\*, /vehicles/{id}/gallery/\*, /vehicles/{id}/archive/\*, /vehicles/{id}/invoices/\*

\- Documents: /documents/\*

\- Trust: /trust/\*, /trust/folders/\*

\- Transfer/Dealer: /transfer/\*, /dealer/\*

\- Sale transfer status: /sale/transfer/status/{tid}

\- PDFs/Exports: /pdf/\*, /export/\*

\- Notifications: /notifications/\*

\- CMS: /cms/blog/\*, /cms/news/\*, /cms/publish/\*

\- Import: /import/\*



------------------------------------------------------------

4\) STATUS (main) – was ist bereits DONE (Referenzen/Dateien)

------------------------------------------------------------

Bindend:

\- docs/99\_MASTER\_CHECKPOINT.md



Wichtige bereits gemergte Themen (Auszug, Details im Master Checkpoint):

A) Web Skeleton + Proxy + Root Redirect

\- packages/web (Vite + React + TS)

\- Vite Proxy: /api/\* -> http://127.0.0.1:8000/\*

\- API Root Redirect: GET / -> 307 -> /public/site

\- GET /favicon.ico -> 204



B) Public QR Disclaimer (Pflichttext)

\- packages/web/src/pages/PublicQrPage.tsx

\- Patch-Script: server/scripts/patch\_public\_qr\_disclaimer.ps1



C) Web Smoke Toolkit

\- server/scripts/ltc\_web\_toolkit.ps1

\- (Optional) Patch-Scripts im Master Checkpoint referenziert



D) Docs Encoding Fix (UTF-8)

\- server/scripts/fix\_docs\_encoding\_utf8.ps1

\- Branch Protection: Required Checks auf Job-Name „pytest“



E) P0 Uploads Quarantäne (Documents)

\- Workflow: QUARANTINED/PENDING -> Admin scan -> CLEAN/INFECTED -> approve/reject

\- Download-Regeln: user/vip/dealer nur APPROVED + scope + object-level

\- Admin/Superadmin: Review auch QUARANTINED möglich



F) P0 Actor Source of Truth

\- server/app/auth/actor.py (zentrale Actor-Ermittlung)

\- DEV/Test Header-Override nur gated (nicht Produktion)



G) Moderator hard-block runtime coverage

\- server/tests/test\_moderator\_block\_coverage\_runtime.py (Runtime-Scan über registrierte Routes)



H) Sale/Transfer Status Leak Fix (Security)

\- GET /sale/transfer/status/{transfer\_id}

\- Zugriff nur Initiator ODER Redeemer (object-level), sonst 403

\- Test-Coverage in server/tests/test\_sale\_transfer\_api.py



I) VIP Business Staff-Limit + Superadmin Gate

\- VIP-Gewerbe max. 2 Staff-Accounts

\- Superadmin-only Freigabe/Erhöhung

\- Referenzen: server/app/admin/routes.py, server/tests/test\_vip\_business\_staff\_limit.py



J) OpenAPI Duplicate Operation IDs Fix (Documents router)

\- server/app/main.py: documents router nur einmal include\_router(...)



K) Public Blog/News endpoints

\- Public Router: GET /blog(/), GET /blog/{slug}, GET /news(/), GET /news/{slug}

\- Router wired in server/app/main.py



------------------------------------------------------------

5\) PRODUKTLOGIK (E2E) – „was muss funktionieren“

------------------------------------------------------------

Bindend:

\- docs/02\_PRODUCT\_SPEC\_UNIFIED.md



Schnellindex der wichtigsten Spec-Abschnitte:

\- §2 End-to-End Flow (Landing -> Eintritt -> Rollenwahl -> Signup -> Consent -> VIN -> Onboarding)

\- §3 Fahrzeuge/Collections + Paywall (1 gratis, ab 2 serverseitig)

\- §5 Entries Pflichtfelder (Datum, Typ, durchgeführt von, Kilometerstand)

\- §6 Upload (Bilder/PDF), Trusted Upload Hash/Checksum, PII-Workflow

\- §7 T1/T2/T3 (Nachträge)

\- §8 Public Mini-Check (datenarm, VIN maskiert)

\- §9 Trust-Ampel + To-dos (VIP Top3 vs Non-VIP volle Liste)

\- §10 Unfalltrust (Unbekannt deckelt max Orange; Unfall -> Grün nur abgeschlossen + belegt)

\- §11 Oldtimer-/Restauration-Trust (Trust-Ordner)

\- §12 Modul-Eingang (Übernehmen/Ablehnen/Später), Spam-Schutz

\- §13 Immutable Systemlogs (OBD/GPS)

\- §14 Transfer/Dealer (klar getrennt)

\- §15 PDFs/TTL (Trust 90d, Wartung 30d, Inserat 30d; Historie bleibt)

\- §16 Notifications (Digest + kritisch sofort; VIP Ruhezeiten E-Mail)

\- §18 Import (Validate -> Run + Report; Dubletten skip)

\- §20 Add-ons Gate/Grandfathering: addon\_first\_enabled\_at == NULL -> „neu“ (Paywall erlaubt)



------------------------------------------------------------

6\) ENGINEERING-GUIDE (wie Codex arbeiten soll)

------------------------------------------------------------

A) Vor jeder Änderung:

\- docs/99\_MASTER\_CHECKPOINT.md lesen (aktueller Stand, PRs, Scripts)

\- docs/03\_RIGHTS\_MATRIX.md prüfen (RBAC/Allowlist/403/401/Objektchecks)

\- docs/01\_DECISIONS.md prüfen (Entscheidungen/Regeln)



B) Jede Feature-/Policy-/Flow-Änderung MUSS docs updaten:

\- docs/99\_MASTER\_CHECKPOINT.md (Status + PR/Scripts)

\- docs/01\_DECISIONS.md (wenn neue Regel)

\- docs/03\_RIGHTS\_MATRIX.md (wenn Rechte/Flows betroffen)

\- docs/02\_PRODUCT\_SPEC\_UNIFIED.md (wenn Produktlogik/Flow betroffen)



C) Logging/Responses:

\- keine PII/Secrets

\- keine ungefilterten Dokument-IDs oder User-IDs in Public-Kontexten

\- Exports redacted für Nicht-Admins



D) RBAC-Enforcement:

\- jede Route hat Gate (deny-by-default)

\- Moderator: hard block via Dependency (forbid\_moderator) + Runtime-Scan Test muss weiter grün bleiben

\- object-level checks nicht vergessen (Owner/Business/Scopes)



------------------------------------------------------------

7\) LOKALES STARTEN / TESTEN (Windows, Repo-Root)

------------------------------------------------------------

API (Tab A):

\- cd <REPO-ROOT>\\server

\- $env:LTC\_SECRET\_KEY="dev\_test\_secret\_key\_32\_chars\_minimum\_\_OK"

\- poetry run uvicorn app.main:app --reload



WEB (Tab B):

\- cd <REPO-ROOT>\\packages\\web

\- npm install

\- npm run dev

\- http://127.0.0.1:5173/



Tests:

\- cd <REPO-ROOT>\\server

\- $env:LTC\_SECRET\_KEY="dev\_test\_secret\_key\_32\_chars\_minimum\_\_OK"

\- poetry run pytest -q



Web Build Smoke:

\- cd <REPO-ROOT>

\- pwsh -NoProfile -ExecutionPolicy Bypass -File .\\server\\scripts\\ltc\_web\_toolkit.ps1 -Smoke -Clean



------------------------------------------------------------

8\) „WO FINDE ICH WAS“ – Pfad-Mapping (für Codex)

------------------------------------------------------------

SoT/Docs:

\- docs/99\_MASTER\_CHECKPOINT.md        -> Projektstatus, PR/Scripts, Done-Liste

\- docs/02\_PRODUCT\_SPEC\_UNIFIED.md     -> bindende Produktlogik (E2E)

\- docs/03\_RIGHTS\_MATRIX.md            -> RBAC-Matrix + Routen + Regeln

\- docs/01\_DECISIONS.md                -> Entscheidungen (warum/konsequenz)

\- docs/06\_WORK\_RULES.md               -> Output-/Arbeitsregeln

\- docs/04\_REPO\_STRUCTURE.md           -> Soll-Struktur + Quick Commands



Backend (FastAPI):

\- server/app/main.py                  -> Router wiring (inkl. Blog/News, Documents include)

\- server/app/auth/actor.py            -> Actor Source of Truth (Auth/401)

\- server/app/admin/routes.py          -> Admin-Routen (u.a. VIP staff-limit gate)

\- server/app/routers/\*                -> Feature-Router (documents, trust, transfer, dealer, etc.)

\- server/app/services/\*               -> Business-Logik (object-level checks zentralisieren)

\- server/app/models/\*                 -> DB-Modelle (inkl. Dokumentstatus/Scan/PII Felder)



Scripts:

\- server/scripts/ltc\_web\_toolkit.ps1

\- server/scripts/fix\_docs\_encoding\_utf8.ps1

\- server/scripts/patch\_\* (siehe Master Checkpoint für genaue Namen/Zwecke)



Tests (Security-relevant zuerst):

\- server/tests/test\_moderator\_block\_coverage\_runtime.py

\- server/tests/test\_sale\_transfer\_api.py

\- server/tests/test\_vip\_business\_staff\_limit.py

\- (weitere RBAC/Guard-Tests je nach Repo)



Frontend:

\- packages/web/src/pages/PublicQrPage.tsx  -> Public QR Disclaimer (Pflichttext)



------------------------------------------------------------

9\) CHECKLISTE für jede Änderung (kurz, strikt)

------------------------------------------------------------

\- Security: deny-by-default, Moderator überall 403 außer Allowlist

\- Actor missing -> 401

\- Object-level checks vorhanden

\- Documents: Quarantäne/Scan/Approve/Download-Regeln unverändert korrekt

\- Exports redacted + nur APPROVED-Dokumentrefs

\- Tests grün: pytest

\- Docs aktualisiert (Master Checkpoint + ggf. Rights/Decisions/Spec)

