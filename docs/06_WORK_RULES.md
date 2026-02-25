# docs/06_WORK_RULES.md
# LifeTimeCircle – Service Heft 4.0
**Arbeitsregeln (Chat/Umsetzung) – SoT**  
Stand: **2026-02-06** (Europe/Berlin)

Ziel: maximal konkret, produktionsreif, keine Demos, keine Lücken.

## Sprache / Output
- Deutsch
- maximal konkret
- keine Floskeln
- nicht nachfragen außer zwingend (sonst Defaultannahme)

## Code-Regeln
- Keine ZIPs.
- Wenn Code/Dateien: immer **vollständiger Dateipfad + kompletter Dateiinhalt**.
- Keine Platzhalter.
- Keine halben Snippets.
- Wenn zu lang: **Block 1/n … n/n**.

## Source of Truth (SoT)
- **./docs** ist SoT (keine Altpfade, keine Parallel-Spezifikationen).
- Immer zuerst lesen/prüfen: `docs/99_MASTER_CHECKPOINT.md`
- Produkt-Spezifikation (bindend): `docs/02_PRODUCT_SPEC_UNIFIED.md`

## Konflikt-Priorität (wenn etwas widerspricht)
1) `docs/99_MASTER_CHECKPOINT.md`
2) `docs/02_PRODUCT_SPEC_UNIFIED.md`
3) `docs/03_RIGHTS_MATRIX.md`
4) `docs/01_DECISIONS.md`
5) `server/` (Implementierung)
6) Backlog/sonstiges

## Security / Policy (nicht verhandelbar)
- Default: **deny-by-default + least privilege**
- RBAC **serverseitig enforced** + **object-level checks**
- **Moderator strikt nur Blog/News** (sonst überall 403)
- **Keine PII/Secrets** in Logs/Responses/Exports

## Doku-Disziplin (damit nichts vergessen geht)
Jede Feature-/Policy-/Flow-Änderung erfordert Update in `./docs`:
- `docs/99_MASTER_CHECKPOINT.md` (Status + Referenzen/PRs/Scripts)
- `docs/01_DECISIONS.md` (wenn neue Entscheidung/Regel)
- `docs/03_RIGHTS_MATRIX.md` (wenn Rollen/Rechte/Flows betroffen)
- `docs/02_PRODUCT_SPEC_UNIFIED.md` (wenn Userflow/Produktlogik betroffen)

## Env-Hinweis
- Export/Redaction/HMAC braucht `LTC_SECRET_KEY` (>=16).
- Tests/DEV setzen ihn explizit.

## Arbeitsmodus
- Default: **Repo-Root**
- Nicht nachfragen außer zwingend; sonst Defaultannahmen treffen und direkt liefern:
  - Commands (rg/Select-String/PowerShell) so, dass sie im Repo-Root laufen

## Public-QR Pflichttext (exakt, unverändert)
„Die Trust-Ampel bewertet ausschließlich die Dokumentations- und Nachweisqualität. Sie ist keine Aussage über den technischen Zustand des Fahrzeugs.“

---

## 9. PowerShell Param-Gate

- In jeder `*.ps1` muss `param(...)` am Script-Anfang stehen.
- Erlaubt vor `param(...)`: Kommentare, `#requires`, `using`, Script-Attribute.
- Nicht erlaubt vor `param(...)`: Executable Code (führt zu Gate-Fail).
- Repo-weite Prüfung läuft über `tools/ps_param_gate.ps1` und ist in `tools/test_all.ps1` enthalten.
- Lokal schneller Check: `pwsh -NoProfile -ExecutionPolicy Bypass -File .\tools\ps_param_gate.ps1`
