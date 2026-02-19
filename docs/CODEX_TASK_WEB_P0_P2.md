\# CODEX\_TASK\_WEB\_P0\_P2 — Webdesign \& Frontend 100% Umsetzung (P0–P2)



\## Kontext

Projekt: \*\*LifeTimeCircle – Service Heft 4.0\*\*  

Ziel: Im Web-Frontend (`packages/web/`) eine robuste, konsistente UI-Basis + Seitenstruktur bauen, die die Produktlogik \*\*„Dokumentation \& Proof“\*\* sauber abbildet (Uploads, Historie, Trust-Ampel) und alle Rechte-/Consent-Regeln korrekt respektiert.



---



\## 0) Nicht verhandelbar (SoT + Hygiene + Security)

\### Source of Truth (immer in dieser Reihenfolge)

1\. `docs/99\_MASTER\_CHECKPOINT.md`

2\. `docs/02\_PRODUCT\_SPEC\_UNIFIED.md`

3\. `docs/03\_RIGHTS\_MATRIX.md`

4\. `docs/01\_DECISIONS.md`



\### Security / Rechte

\- \*\*deny-by-default + least privilege\*\*.

\- \*\*RBAC ist serverseitig\*\*, UI ist \*\*nicht\*\* die Security – aber UI darf \*\*keine falschen Erwartungen\*\* erzeugen.

\- \*\*Moderator ist strikt nur Blog/News\*\* → keine Menüs/Flows/Pages designen, die Moderator Zugriff auf Fahrzeuge/Dokumente/Trust nahelegen. In der UI: Moderator sieht keine App-Navigation; bei direktem Aufruf: 403.



\### Datenhygiene

\- \*\*Keine PII/Secrets\*\* in Mockdaten, Screenshots, Beispielen, Assets.

\- \*\*Keine echten VINs\*\* → VIN stets \*\*maskiert\*\*.

\- Public/QR: \*\*datenarm\*\*.



\### Public-QR Pflichttext (exakt, unverändert)

> „Die Trust-Ampel bewertet ausschließlich die Dokumentations- und Nachweisqualität. Sie ist keine Aussage über den technischen Zustand des Fahrzeugs.“



---



\## 1) Zielbild / Deliverables (am Ende MUSS vorhanden sein)

\### P0 — Fundament

1\. \*\*Design System / Tokens\*\* (Typo, Farben, Spacing, Radius, Shadow, Statusfarben inkl. Trust)

2\. \*\*UI-Kit Basiskomponenten\*\* (Button, Input, Select, Checkbox, Card, Badge, Alert, Tabs, Table, Modal/Drawer optional, Toast optional, Skeleton, EmptyState)

3\. \*\*2 Layout-Welten\*\*: Public vs App (Navigation, Header, Shell)

4\. \*\*System-Screens\*\*: 401 / 403 / Consent required (optional 404)

5\. \*\*Public-QR Page\*\*: datenarm, VIN maskiert, Disclaimer exakt, „print/share-ready“



\### P1 — MVP Flow (nutzbar)

6\. \*\*Landing → Eintritt → Rollenwahl → Signup/Login\*\* (gemäß `docs/01\_DECISIONS.md`)

7\. \*\*Consent Screens\*\* (blockierend, klar; Redirect zurück zur Zielseite)

8\. \*\*Vehicles\*\*: Liste + Detail als „Serviceheft/Dashboard“

9\. \*\*Documents\*\*: Upload UX + Statusanzeigen (keine Admin-Review UI für Nicht-Admins)



\### P2 — Vorbereitung

10\. \*\*Trust/To-Dos UI-Struktur\*\* als Widgets/Platzhalter (ohne falsche Aussagen über Fahrzeugzustand)



---



\## 2) Arbeitsmodus / Implementierungsregeln

\- \*\*Bestehende Repo-Patterns priorisieren\*\* (keine willkürlichen Framework-Wechsel).

\- Alle neuen/angepassten Dateien im Web-Paket: `packages/web/...`

\- Wenn du Rollen/Flows/Policies visuell oder technisch anfasst, \*\*Docs mitziehen\*\* (siehe Abschnitt 7).

\- Ergebnis immer so bauen, dass `npm run build` in `packages/web` grün bleibt.



---



\## 3) Schritt-für-Schritt Aufgaben (Codex: Abarbeiten in Reihenfolge)



\### Schritt 1 — Ist-Analyse (kurz, aber konkret)

1\. Prüfe vorhandene Struktur:

&nbsp;  - Routing (wie werden Routes gemanaged?)

&nbsp;  - Bestehende Layouts/Pages

&nbsp;  - Style-System (CSS/Tailwind/Modules?)

&nbsp;  - API-Helper/Fetch-Wrapper + Error-Handling

2\. Schreibe in PR-Description (kurz):

&nbsp;  - Router/Navigation-Ansatz

&nbsp;  - Wo Tokens/Styles liegen

&nbsp;  - Welche Guards existieren oder neu eingeführt wurden



> Keine Spekulationen. Nur Fakten aus dem Code.



---



\### Schritt 2 — Design Tokens \& Base Styles (P0)

Ziel: Konsistente Basis, die überall genutzt wird.



\- Lege Tokens an oder erweitere bestehende Global Styles:

&nbsp; - Typo: Font-Sizes/Line-heights, Headings, Body

&nbsp; - Spacing Scale

&nbsp; - Radius + Shadow

&nbsp; - Farbpalette inkl. Statusfarben: neutral/info/success/warn/error

&nbsp; - Trust-Statusfarben: grün/gelb/rot/grau (und passende Kontrastfarben)



\*\*Wichtig:\*\* Pages sollen keine „Magic Numbers“ enthalten – Spacing/Radius/Farbwerte primär über Tokens.



---



\### Schritt 3 — UI-Kit Komponenten (P0)

Implementiere/vereinheitliche wiederverwendbare Komponenten:

\- `Button`, `Input`, `Select`, `Checkbox`

\- `Card`, `Badge`, `Alert`

\- `Tabs`, `Table`

\- `EmptyState`, `Skeleton`

\- Optional (wenn gebraucht): `Modal/Dialog`, `Drawer`, `Toast`



Qualität:

\- A11y: Fokuszustände, Tastaturbedienung, sinnvolle ARIA-Labels

\- Klare Zustände: loading/disabled/error/success

\- Visuell ruhig, „Serviceheft/Dashboard“ Look



---



\### Schritt 4 — Layout-Trennung Public vs App (P0)

Ziel: Strikte Trennung + korrektes Verhalten bei Actor/Role/Consent.



\- Erstelle/verwende:

&nbsp; - `PublicLayout` (Public, Blog/News, Auth/Entry)

&nbsp; - `AppLayout` (App: Vehicles/Documents/etc.)



Navigation:

\- Public-Nav ist minimal (z. B. Blog/News, Einstieg/Login)

\- App-Nav zeigt nur App-relevante Einträge (Vehicles, Documents, …)

\- Moderator: App-Nav \*\*nie anzeigen\*\*



---



\### Schritt 5 — Route Guards / Zugriff (P0)

Implementiere Guards (oder an bestehendes Pattern anpassen):

\- `RequireActor`: wenn Actor fehlt → 401 Screen (oder Redirect auf Login + klare Message)

\- `RequireConsent`: wenn Consent fehlt/abgelaufen → ConsentRequired Screen (blockierend)

\- `RequireRole`: Moderator nur Blog/News; sonst 403



\*\*Regel:\*\* Wenn unklar → blockieren (deny-by-default).



---



\### Schritt 6 — System Screens (P0)

Erstelle Seiten:

\- `Unauthorized401`

\- `Forbidden403`

\- `ConsentRequired`

\- Optional: `NotFound404`



Design:

\- Gleicher Stil (Card + klare Headline + CTA)

\- Keine PII, keine internen IDs

\- ConsentRequired: klare Begründung + CTA „Akzeptieren“ + danach Rücksprung zur Zielroute



---



\### Schritt 7 — Public-QR Page (P0)

Ziel: „print/share-ready“, datenarm, korrekt.



Seite muss enthalten:

\- VIN \*\*maskiert\*\*

\- Trust-Ampel Darstellung (nur Dokumentations-/Nachweisqualität)

\- Unfallstatus-Badge (wenn Daten vorhanden, sonst neutral)

\- Pflichttext exakt (siehe oben, unverändert)



Verboten:

\- Interne IDs

\- Personenbezüge

\- Links auf private Dokumente ohne Auth



---



\### Schritt 8 — Eintritt/Auth Flow + Consent (P1)

Gemäß `docs/01\_DECISIONS.md`:

\- Landing/Frontpage: Einstieg (keine „App“-Links ohne Login/Consent)

\- Eintritt → Rollenwahl → Signup/Login

\- Consent Screen blockiert App-Routen, bis akzeptiert



Nach Consent:

\- Redirect zurück zur ursprünglich gewünschten Route (sofern vorhanden)



---



\### Schritt 9 — Vehicles Pages (P1)

\*\*Vehicles List\*\*

\- Liste + EmptyState + Loading + Error

\- Anzeige: Fahrzeugname/Modell (neutral), VIN maskiert, Trust Kurzstatus



\*\*Vehicle Detail (Dashboard)\*\*

\- Header: Fahrzeug + VIN maskiert + Trust-Ampel

\- Sektionen:

&nbsp; 1) Historie/Timeline (Service-Einträge)

&nbsp; 2) Dokumente/Uploads Übersicht (Counts + Status)

&nbsp; 3) Proof-Widgets (z. B. offene Nachweise/letzte Updates)



\*\*Einträge-Form\*\*

\- Pflichtfelder gemäß Spec: Datum, Typ, durchgeführt von, Kilometerstand

\- Validierung + klare Fehlertexte

\- Submit disabled bis valid



---



\### Schritt 10 — Documents Pages / Upload UX (P1)

Upload-Komponente:

\- Drag\&Drop + Filepicker

\- Fortschritt + Retry

\- Statusanzeige: QUARANTINED/PENDING/CLEAN/INFECTED/APPROVED (oder Repo-Statusmapping)



Rechte:

\- \*\*Keine Admin-Review UI\*\* für Nicht-Admins.

\- Moderator: kein Zugriff → 403.



States:

\- Empty/Loading/Error sauber (keine blank screens)



---



\### Schritt 11 — Trust/To-Dos Widgets (P2 Vorbereitung)

\- Baue UI-Struktur so, dass Trust/To-Dos später „einstecken“ können:

&nbsp; - Widget-Komponenten + Platzhalter

&nbsp; - Keine Aussagen zum technischen Zustand

&nbsp; - Wenn VIP/Non-VIP Logik existiert: UI kann Top-3 vs volle Liste anzeigen, sonst neutraler Platzhalter



---



\## 4) Definition of Done (Abnahme-Kriterien)

\### Build/Checks

\- `npm run build` in `packages/web` ✅

\- `server/scripts/ltc\_web\_toolkit.ps1` ✅

\- `server/scripts/ltc\_verify\_ist\_zustand.ps1` ✅

\- Required Check `pytest` ✅



\### Funktional

\- Public vs App Layout sauber getrennt

\- 401/403/Consent Screens greifen zuverlässig

\- Moderator: nur Blog/News sichtbar/erreichbar; alles andere 403

\- Public-QR: VIN maskiert + datenarm + Pflichttext exakt

\- Vehicles List/Detail \& Documents Upload: konsistente UI + vollständige States

\- Keine PII/Secrets in Repo-Änderungen



---



\## 5) Output-Regeln für Codex (wie du liefern musst)

In der finalen Antwort:

1\. Liste alle \*\*geänderten/neu erstellten Dateien\*\* mit \*\*vollem Pfad\*\*

2\. Gib für \*\*jede Datei\*\* den \*\*vollständigen Inhalt\*\* aus (kein Diff-only)

3\. Keine ZIPs

4\. Nenne kurz die ausgeführten Commands + Ergebnis

5\. Erstelle Commit + PR (falls Tooling vorhanden) inkl. kurzer PR-Beschreibung



---



\## 6) Doku-Disziplin (nur wenn du Flows/Rollen/Policies änderst)

Wenn du Rollen/Access/UI-Policies/Flows änderst oder präzisierst, update parallel:

\- `docs/99\_MASTER\_CHECKPOINT.md` (Status/Referenzen)

\- `docs/01\_DECISIONS.md` (neue Regel/Entscheidung)

\- `docs/03\_RIGHTS\_MATRIX.md` (Rollen/Rechte/Flows)

\- `docs/02\_PRODUCT\_SPEC\_UNIFIED.md` (Userflow/Produktlogik)



---



\## 7) Hinweis zur Priorität

\- \*\*P0 komplett zuerst\*\*, dann P1, dann P2.

\- Wenn du bei einer Stelle unsicher bist: \*\*deny-by-default\*\* + kurze Notiz in PR-Description, welche Doc-Stelle das begründet.

