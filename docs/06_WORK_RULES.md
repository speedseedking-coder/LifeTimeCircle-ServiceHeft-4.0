

---

### `docs/06_WORK_RULES.md`
```md
# LifeTimeCircle – Service Heft 4.0
**Arbeitsregeln (Chat/Umsetzung) – SoT**  
Stand: 2026-02-05

> Ziel: maximal konkret, produktionsreif, keine Demos, keine Lücken.

---

## Sprache / Output
- Deutsch
- maximal konkret
- keine Floskeln
- nicht nachfragen außer zwingend (sonst Defaultannahme)

---

## Code-Regeln
- **Keine ZIPs. Nur Code.**
- **Code immer:** Dateipfad + Dateiname + kompletter Dateiinhalt.
- Keine Platzhalter.
- Keine halben Snippets.
- Wenn zu lang: Block 1/n … bis fertig.

---

## Security / Policy
- Default: **deny-by-default + least privilege**
- RBAC serverseitig enforced
- Moderator strikt nur Blog/News (überall sonst 403)
- Keine PII/Secrets in Logs/Responses

---

## Git / Workflow
- Feature-Branch
- PR nach `main`
- CI muss grün sein (inkl. RBAC-Guard-Tests)
- Branch Protection: PR-only, strict up-to-date, required checks, linear history

---

## Lokal testen
```powershell
cd "C:\Users\stefa\Projekte\LifeTimeCircle-ServiceHeft-4.0\server"

# für Export/Redaction/Secret-Checks
$env:LTC_SECRET_KEY = "dev_test_secret_key_32_chars_minimum__OK"

poetry run pytest -q