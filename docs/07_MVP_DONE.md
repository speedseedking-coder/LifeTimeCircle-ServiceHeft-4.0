\# docs/07\_MVP\_DONE.md

\# LifeTimeCircle – Service Heft 4.0

\*\*MVP „durch“ / Release-Gates + Website-Plan (SoT)\*\*  

Stand: 2026-02-06



\## 1) Wann sind wir „durch“?

Wir sind „durch“ (= MVP releasefähig), wenn ALLE Punkte erfüllt sind:



\### Release-Gates (hart)

\- CI/Tests grün (`poetry run pytest -q`)

\- RBAC: deny-by-default + least privilege ist serverseitig enforced

\- Moderator: außerhalb Allowlist immer 403 (`/auth/\*`, `/health`, `/public/\*`, `/blog/\*`, `/news/\*`)

\- Documents: Quarantine-by-default; Approve nur nach Scan=CLEAN; Downloads für non-admin nur APPROVED+scope

\- OpenAPI: keine Duplicate operationId / keine Duplicate routes

\- Keine PII/Secrets in Logs/Responses



\### MVP UX (sichtbar, minimal)

\- Eine öffentliche Landingpage ist erreichbar (mindestens `/public/site`)

\- Links zu /docs, /redoc, /blog, /news funktionieren

\- Pflichttext Trust-Ampel ist sichtbar (Public-QR Hinweis)



\## 2) Wann „kommt die Webseite“?

Sofort sichtbar, sobald `GET /public/site` existiert (statische Landingpage über FastAPI, kein Frontend-Build nötig).



„Richtige App-Webseite“ (Login/Dashboard/Servicebook UI) ist ein eigenes Modul:

\- separates Frontend (z.B. Vite/React oder Next.js)

\- API-Integration + Auth-Flow + RBAC-aware Navigation

\- Deployment (static hosting) + API Base-URL + CORS/CSRF sauber



Kurz: Landingpage = jetzt über Backend möglich. App-UI = nächster großer Block (Frontend).



