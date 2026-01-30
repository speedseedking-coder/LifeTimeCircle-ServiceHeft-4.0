\# LifeTimeCircle – ServiceHeft 4.0 — MASTER CHECKPOINT



Stand: 2026-01-30



\## Projekt-Setup (lokal)

\- Repo: C:\\Users\\stefa\\Projekte\\LifeTimeCircle-ServiceHeft-4.0

\- Server: C:\\Users\\stefa\\Projekte\\LifeTimeCircle-ServiceHeft-4.0\\server

\- Node/Packages: C:\\Users\\stefa\\Projekte\\LifeTimeCircle-ServiceHeft-4.0\\packages\\lifetimecircle-core

\- Policy: deny-by-default, least privilege, RBAC serverseitig, keine PII im Log, HMAC-Pseudonymisierung, Public-QR ohne Metriken + Disclaimer.



\## Aktueller IST-Zustand (funktional)

\- Auth per E-Mail Challenge (DEV OTP optional) läuft.

\- Sessions/Token-Check funktioniert.

\- Audit Tail Script zeigt Events ohne PII.

\- RBAC-Guard ist integriert und Unit-Tests sind grün.

\- Deprecation-Fixes (FastAPI lifespan, utcnow->timezone aware) sind gepatcht.

\- Gesamtstatus zuletzt: pytest war grün (10 passed), danach Admin-Routes ergänzt.



\## Wichtige Dateien / Module (Server)

\- app/auth/\*

&nbsp; - settings.py: env/secret validation

&nbsp; - crypto.py: token\_hash / HMAC

&nbsp; - storage.py: sqlite auth storage

&nbsp; - rbac.py: get\_current\_user + require\_roles (401/403 sauber)

&nbsp; - deps.py: compatibility layer (falls Router noch alte deps nutzen)

\- app/routers/masterclipboard (bestehende Module-Routes)

\- scripts/

&nbsp; - uvicorn\_run.ps1 (Serverstart; verlangt LTC\_SECRET\_KEY >= 32)

&nbsp; - patch\_\* (verschiedene Patch-Skripte)

&nbsp; - audit\_tail.py (letzte Events, ohne PII)



\## Admin-Rollenverwaltung (NEU)

Ziel:

\- Endpoint: POST /admin/users/{user\_id}/role (nur admin)

\- Endpoint: GET /admin/users (nur admin, keine PII)

\- Audit: minimal, ohne Klartext-PII



Symptom wenn falsch eingebunden:

\- Tests geben 404 Not Found auf /admin/... -> Router nicht gemountet (main.py include fehlt)



\## Test-Kommandos

Server-Tests:

\- cd server

\- poetry run pytest



Route-Check Admin:

\- poetry run python -c "from app.main import create\_app; app=create\_app(); print(\[r.path for r in app.routes if getattr(r,'path',None) and r.path.startswith('/admin')])"



Serverstart (DEV):

\- $env:LTC\_SECRET\_KEY="dev-only-change-me-please-change-me-32chars-XXXX"

\- $env:LTC\_DB\_PATH=".\\data\\app.db"

\- $env:LTC\_DEV\_EXPOSE\_OTP="false"

\- .\\uvicorn\_run.ps1



\## Offene Baustellen / Nächster Schritt

P0:

1\) Sicherstellen, dass admin\_router in create\_app() eingebunden ist (404 Fix).

2\) pytest grün bekommen (Admin-Tests müssen 200/403 liefern, nicht 404).

3\) Danach: git add + commit + (optional) tag checkpoint.



\## Letzte beobachtete Fehler

\- Admin-Tests: 404 Not Found (Router nicht eingebunden)

\- Lösung: main.py Import + app.include\_router(admin\_router) innerhalb create\_app().



