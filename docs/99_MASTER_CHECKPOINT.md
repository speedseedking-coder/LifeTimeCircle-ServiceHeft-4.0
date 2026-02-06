# docs/99_MASTER_CHECKPOINT.md
# LifeTimeCircle – Service Heft 4.0
**MASTER CHECKPOINT (SoT)**  
Stand: **2026-02-06**

Projekt:
- Brand: **LifeTimeCircle**
- Modul: **Service Heft 4.0**
- Ziel: **produktionsreif (keine Demo)**
- Security: **deny-by-default + least privilege**, RBAC **serverseitig enforced**
- Source of Truth: **./docs** (keine Altpfade/Altversionen)

Konflikt-Priorität:
1) `docs/99_MASTER_CHECKPOINT.md`
2) `docs/03_RIGHTS_MATRIX.md`
3) `server/`
4) Backlog/sonstiges

Env-Hinweis:
- Export/Redaction/HMAC braucht `LTC_SECRET_KEY` (>=16); Tests/DEV setzen ihn explizit.

---

## Aktueller Stand (main)
✅ PR #24: `Test: moderator blocked on all non-public routes (runtime scan)`  
✅ PR #27: `Fix: sale-transfer status endpoint participant-only (prevent ID leak)`  
✅ PR #33: `Public: blog/news endpoints`  
✅ PR #36: `Fix: OpenAPI duplicate operation ids (documents router double include)`  
✅ PR #37: `Feat: public landing page (/public/site) + Docs: MVP gates + scripts`  
- `GET /public/site` liefert eine minimale Landingpage (Backend-Status + Links)  
- `docs/07_MVP_DONE.md` ergänzt Release-Gates + Website-Plan  
- `server/scripts/check_openapi_duplicates.py` prüft Duplicate Routes + Duplicate operationId  
✅ Lokal: `DUP_ROUTES_COUNT = 0` und `DUP_OPERATION_ID_COUNT = 0`  
✅ CI: `CI/pytest` grün

---

## Public Endpoints (Auszug)
- `GET /public/site` (Landingpage)
- `GET /docs` (Swagger UI)
- `GET /redoc` (ReDoc)
- `GET /openapi.json`
- `GET /blog/`, `GET /blog/{slug}`
- `GET /news/`, `GET /news/{slug}`

---

## Security / RBAC (SoT)
- Default: **deny-by-default**
- **Actor required** auf nicht-public: ohne Actor → **401**
- **Moderator** strikt nur Blog/News (+ health/public/auth); alles andere → **403**
- Documents: **Quarantine-by-default**; Approve nur nach Scan=`CLEAN`; Download für non-admin nur `APPROVED` + Scope/Owner

---

## Public-QR Trust-Ampel (Pflichttext)
„Die Trust-Ampel bewertet ausschließlich die Dokumentations- und Nachweisqualität. Sie ist keine Aussage über den technischen Zustand des Fahrzeugs.“