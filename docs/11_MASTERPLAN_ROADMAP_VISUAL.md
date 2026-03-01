# LifeTimeCircle – Finalisierungs-Roadmap (Visual)
**Stand: 2026-03-01**

Diese Datei ist eine kompakte Visualisierung des aktuellen Zielkorridors.
Sie beschreibt keinen historischen Kickoff-Plan mehr, sondern den laufenden Restpfad ab dem verifizierten Stand vom **Sonntag, 2026-03-01**.

---

## Überblick

```text
Bereits verifiziert
    |
    +-- Backend stabil
    +-- Web-Core-Flows angebunden
    +-- A11y / Mobile / Desktop-Hardening auf Kernseiten
    +-- Repo-Gates grün
    |
    v
Rest-Finalisierung
    |
    +-- SoT-Dokumente konsolidieren
    +-- Rest-Polish auf Kernflows
    +-- Release-/Betriebsfragen klären
    |
    v
Release-nahe Entscheidung
```

---

## Roadmap in Phasen

```text
PHASE A: Stabiler Kern
-----------------------------------------
[done] Backend, Auth, Consent
[done] Vehicles / Vehicle Detail
[done] Documents
[done] Public-QR
[done] Admin
[done] Web-Build + E2E + Test-All

PHASE B: Qualitäts-Härtung
-----------------------------------------
[done] Basis-A11y
[done] Mobile 375px
[done] Desktop 1920px
[open] Rest-Randfälle / Spezialkomponenten

PHASE C: SoT-Konsolidierung
-----------------------------------------
[done] 99_MASTER_CHECKPOINT
[done] 07_WEBSITE_COPY_MASTER_CONTEXT
[done] MASTERPLAN_INDEX
[done] READING_ORDER
[in progress] FINALISIERUNG / ROADMAP / DAILY_CHECKLIST

PHASE D: Release-Nähe
-----------------------------------------
[open] restliche Betriebs-/Deployment-Doku
[open] finale Risiko- und Go/No-Go-Sicht
[open] letzter Produkt-Polish auf Kernpfaden
```

---

## Abhängigkeiten

```text
SoT-Konsistenz
    |
    +--> saubere Planung
    |
    +--> weniger Fehlinterpretation im Team

Verifizierter Workspace
    |
    +--> sichere Produktarbeit
    |
    +--> belastbare Release-Entscheidung

Kernflows stabil
    |
    +--> Rest-Polish sinnvoll
    |
    +--> Release-Diskussion überhaupt möglich
```

---

## Kritischer Pfad

```text
1. SoT aktuell halten
2. Workspace clean + grün halten
3. Kernflows weiter härten
4. offene Release-Fragen dokumentieren
5. Go/No-Go erst auf verifiziertem Stand
```

---

## Risiko-Matrix

| Risiko | Wahrscheinlichkeit | Impact | Gegenmaßnahme |
|--------|--------------------|--------|---------------|
| Doku driftet wieder vom Workspace weg | hoch | hoch | SoT kurz halten, alte Chroniken nicht zurückholen |
| Späte UI-Randfälle verursachen Regressionen | mittel | mittel | nur gezielte Pakete, danach Build + E2E |
| Release-Diskussion basiert auf alten Planständen | mittel | hoch | immer erst `99_MASTER_CHECKPOINT.md` lesen |
| Scope driftet in neue Features statt Finalisierung | mittel | hoch | Kernflows und Gates priorisieren |

---

## Erfolgskriterien

```text
Release-nah ist erreicht, wenn:

- der Workspace dauerhaft grün bleibt
- die Kernflows belastbar sind
- die SoT-Dokumente nicht widersprüchlich sind
- offene Themen als echte Restliste sichtbar sind
```

---

## Merksatz

Die Roadmap ist ab jetzt kein Kalenderdrama mehr.
Sie ist ein Restpfad von einem funktionierenden Kern hin zu einem ehrlich dokumentierten, release-nahen Zustand.
