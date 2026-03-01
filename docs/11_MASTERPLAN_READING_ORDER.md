# READING ORDER & DOCUMENT MAP

Diese Datei beschreibt die sinnvolle Lesereihenfolge für den aktuellen Projektstand am **Sonntag, 2026-03-01**.

Wichtig:
- Das Projekt befindet sich bereits in aktiver Umsetzung.
- Alte Kickoff- oder Wochenplan-Texte sind nur noch historisch.
- Für reale Entscheidungen zählt der verifizierte Ist-Zustand.

---

## Empfohlene Reading Order

### Szenario 1: Developer

Wenn du direkt am Code arbeitest:

1. `docs/11_MASTERPLAN_CODEX_CHEATSHEET.md`
   - 5 Minuten Schnellreferenz
2. `docs/00_CODEX_CONTEXT.md`
   - Harte Invarianten, RBAC, SoT-Hierarchie
3. `docs/03_RIGHTS_MATRIX.md`
   - Route- und Rollenlogik
4. `docs/99_MASTER_CHECKPOINT.md`
   - aktueller, verifizierter Status
5. `docs/02_PRODUCT_SPEC_UNIFIED.md`
   - fachlich bindende Produktlogik
6. `docs/07_WEBSITE_COPY_MASTER_CONTEXT.md`
   - nur wenn UI-/Copy-Fragen relevant sind

Gesamt: ca. 60 bis 90 Minuten für belastbaren Projektkontext.

### Szenario 2: Project Manager / Tech Lead

Wenn du Status, Scope und Risiken bewerten willst:

1. `docs/99_MASTER_CHECKPOINT.md`
2. `docs/11_MASTERPLAN_INDEX.md`
3. `docs/11_MASTERPLAN_FINALISIERUNG.md`
4. `docs/11_MASTERPLAN_ROADMAP_VISUAL.md`
5. `docs/00_CODEX_CONTEXT.md` Abschnitt zu Invarianten und Rollen

Gesamt: ca. 45 bis 75 Minuten.

### Szenario 3: Code Review / QA

Vor Review oder QA-Lauf:

1. `docs/11_MASTERPLAN_CODEX_CHEATSHEET.md`
2. `docs/00_CODEX_CONTEXT.md`
3. `docs/03_RIGHTS_MATRIX.md`
4. `docs/99_MASTER_CHECKPOINT.md`

Gesamt: ca. 30 Minuten.

---

## Dokumentübersicht

### Technische SoT

| Dokument | Zweck |
|----------|------|
| `00_CODEX_CONTEXT.md` | Arbeitsbriefing, Invarianten, SoT-Hierarchie |
| `02_PRODUCT_SPEC_UNIFIED.md` | fachlich bindende Produktlogik |
| `03_RIGHTS_MATRIX.md` | Rollen- und Routing-Matrix |
| `01_DECISIONS.md` | Architektur- und Policy-Entscheidungen |
| `99_MASTER_CHECKPOINT.md` | aktueller verifizierter Ist-Zustand |

### Operative Masterplan-Dokumente

| Dokument | Zweck |
|----------|------|
| `11_MASTERPLAN_INDEX.md` | Einstieg und Einordnung |
| `11_MASTERPLAN_DAILY_CHECKLIST.md` | tägliche Arbeitscheckliste |
| `11_MASTERPLAN_FIX_CARD.md` | operative Task-/Fix-Sicht |
| `11_MASTERPLAN_FINALISIERUNG.md` | strategischer Plan |
| `11_MASTERPLAN_ROADMAP_VISUAL.md` | visuelle Phasen- und Zeitplanung |

### Copy-SoT

| Dokument | Zweck |
|----------|------|
| `07_WEBSITE_COPY_MASTER_CONTEXT.md` | zentrale Website-/Web-App-Texte |

---

## Schnelle Antworten

Wenn jemand fragt:

| Frage | Dokument |
|-------|----------|
| Welche Route oder Rolle ist erlaubt? | `03_RIGHTS_MATRIX.md` |
| Was ist aktuell wirklich fertig? | `99_MASTER_CHECKPOINT.md` |
| Welche Produktlogik ist bindend? | `02_PRODUCT_SPEC_UNIFIED.md` |
| Welche Copy gilt? | `07_WEBSITE_COPY_MASTER_CONTEXT.md` |
| Welche Regeln darf ich nie brechen? | `00_CODEX_CONTEXT.md` |

---

## Kritischer Pfad für aktive Arbeit

Vor produktiver Änderung:

1. `00_CODEX_CONTEXT.md` prüfen
2. `03_RIGHTS_MATRIX.md` prüfen
3. `99_MASTER_CHECKPOINT.md` prüfen
4. lokale Gates ernst nehmen:
   - `tools/test_all.ps1`
   - `tools/ist_check.ps1`

Während laufender Arbeit:

1. `11_MASTERPLAN_DAILY_CHECKLIST.md` als Arbeitsstütze verwenden
2. bei UI-Textfragen `07_WEBSITE_COPY_MASTER_CONTEXT.md` heranziehen
3. bei Konflikten immer SoT vor Planungsdokument stellen

---

## Wenn du nur 10 Minuten hast

Lies in dieser Reihenfolge:

1. `docs/11_MASTERPLAN_CODEX_CHEATSHEET.md`
2. `docs/99_MASTER_CHECKPOINT.md`
3. `docs/11_MASTERPLAN_INDEX.md`

---

## Wenn du verloren bist

1. Beginne mit `docs/99_MASTER_CHECKPOINT.md`
2. gehe dann zu `docs/00_CODEX_CONTEXT.md`
3. kläre Rollenfragen über `docs/03_RIGHTS_MATRIX.md`
4. kläre Produktfragen über `docs/02_PRODUCT_SPEC_UNIFIED.md`
5. nutze erst danach die restlichen Masterplan-Dokumente

---

## Merksatz

Dein schneller Kontext:
- Cheatsheet im Kopf
- Checkpoint als Realität
- CodeX als Regelwerk
- Masterplan als Planungshilfe, nicht als Beweis
