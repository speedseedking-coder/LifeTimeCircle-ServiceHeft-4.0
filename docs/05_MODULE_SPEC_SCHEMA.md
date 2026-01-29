C:\\Users\\stefa\\Projekte\\LifeTimeCircle-ServiceHeft-4.0\\docs\\05\_MODULE\_SPEC\_SCHEMA.md

\# LifeTimeCircle – ServiceHeft 4.0

\## Modul-Spec-Schema (verbindlich)



Stand: 2026-01-29  

Zweck: Einheitlicher Mindeststandard für Modul-Repos (Docs + API Contract + Events), damit Core-Integration deterministisch bleibt.



---



\## 1) Pflichtdateien pro Modul-Repo

Jedes Modul-Repo MUSS enthalten:

\- `CONTEXT\_PACK.md` (1:1 Copy aus Core: `docs/07\_CONTEXT\_PACK.md`, unverändert)

\- `MODULE\_SPEC.md` (Spezifikation nach diesem Schema)

\- `API\_CONTRACT.md` (API + Auth + Events)



Module dürfen keine eigenen abweichenden Policies definieren.



---



\## 2) MODULE\_SPEC.md – Mindestfelder (MUSS)

`MODULE\_SPEC.md` muss folgende Kapitel enthalten (mindestens):



1\. \*\*Name\*\* (`module\_id`)

2\. \*\*Tier\*\* (free / vip / dealer bzw. interne Tier-Bezeichnung aus `docs/04\_MODULE\_CATALOG.md`)

3\. \*\*Zweck\*\*

4\. \*\*In Scope / Out of Scope\*\*

5\. \*\*Rollen \& RBAC\*\*

&nbsp;  - erlaubte Rollen (aus Core: public/user/vip/dealer/moderator/admin)

&nbsp;  - Scope-Regel (own/org/shared)

&nbsp;  - deny-by-default + server enforced (Pflichtsatz)

6\. \*\*Datenkategorien\*\* (gemäß `docs/policies/DATA\_CLASSIFICATION.md`)

7\. \*\*Public Surface\*\* (none / public\_qr\_only / other)  

&nbsp;  - Default: none

8\. \*\*Kern-Workflows\*\*

9\. \*\*Uploads\*\* (ja/nein + Policy-Hinweis)

10\. \*\*Exports\*\* (ja/nein + Policy-Hinweis)

11\. \*\*Audit-Events (Minimum)\*\* (Enum-Namen + redacted Regeln)

12\. \*\*Security/Privacy Anforderungen\*\*

13\. \*\*DoD (Abnahme)\*\* (mindestens RBAC Negativtests + keine PII/Secrets im Log)



Empfehlung: „Stand“-Datum im Header.



---



\## 3) API\_CONTRACT.md – Mindestfelder (MUSS)

\- Base Path / Endpoint-Liste

\- Auth-Modus (public ausgeschlossen, außer explizit erlaubt)

\- Request/Response (Minimalpayloads)

\- Rate-Limits (mindestens: Session/Create, Upload, Export/Share)

\- Event-Emission:

&nbsp; - `module\_id`

&nbsp; - `event\_name`

&nbsp; - `schema\_version`

&nbsp; - `correlation\_id`

&nbsp; - `idempotency\_key`

&nbsp; - `emitted\_at` (server)

&nbsp; - `actor` (role + subject\_id + scope\_ref)

&nbsp; - Payload: redacted-by-default, keine PII



---



\## 4) Event-Integration (Core Contract)

\- Core akzeptiert nur \*\*whitelisted\*\* Module-Events (Project Map: `docs/policies/PROJECT\_MAP.md`).

\- Core mappt Events in TimelineEntries (deterministisch).

\- Public-QR darf niemals direkt Modul-Storages lesen.



---



\## 5) Beispiel – Minimaler Header (optional)

Beispiel (als Orientierung; Format frei, Inhalte Pflicht):



\- module\_id: masterclipboard

\- tier: dealer

\- public\_surface: none

\- roles\_allowed: \[dealer, admin]

\- scope: org

\- deny\_by\_default: true

\- server\_enforced: true

\- events: \[MASTERCLIPBOARD\_SESSION\_STARTED, ...]



