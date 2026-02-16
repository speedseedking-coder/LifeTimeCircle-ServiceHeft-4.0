# server/scripts/README.md
# LifeTimeCircle – Service Heft 4.0 — Scripts

Ziel: Skripte sind wartbar, sicher (deny-by-default) und reproduzierbar.

## 1) Script-Typen

### A) Reusable Tooling (bleibt dauerhaft)
- Präfix häufig: `ltc_*`
- Beispiel:
  - `ltc_web_toolkit.ps1` (Web Smoke Build / optional Clean)

Diese Skripte sind Werkzeuge und dürfen regelmäßig laufen.

### B) Patch-Skripte (meist PR-spezifisch)
- Präfix: `patch_*`
- Zweck: eine klar definierte Änderung idempotent auf Dateien anwenden.

Regel: Patch-Skripte nach Merge nur behalten, wenn sie realistisch wiederverwendet werden.
Reine Unfall-/Reparatur-Patches werden nach Merge entfernt (Repo sauber halten).

## 2) Ausführen (Windows / Repo-Root)

Wichtig: Scripts als Datei ausführen – nicht Zeile-für-Zeile in die Konsole kopieren.

```powershell
pwsh -NoProfile -ExecutionPolicy Bypass -File .\server\scripts\{script}.ps1 {args}