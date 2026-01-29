# TRUSTSCORE SPEC – Public-QR Mini-Check (Ampelsystem)

Version: 1.2  
Stand: 2026-01-27

---

## 0) Ziel & Grenzen (nicht verhandelbar)
Public-QR zeigt eine Trust-Ampel, die ausschließlich Dokumentations-/Nachweisqualität bewertet.
Keine Aussage über technischen Zustand. Kein OBD/Defekt/TÜV/Diagnose-Wording.

---

## 1) Ampelstufen
- Grün: hohe Nachweisqualität (mit Unfall-/Unknown-Bremse)
- Gelb: mittlere Nachweisqualität
- Orange: geringe Nachweisqualität
- Rot: sehr geringe/unklare Nachweisqualität

---

## 2) Eingangsgrößen (intern)
Intern darf berechnet werden aus:
- entries_total, history_span_months, critical_gaps_months
- t1_share, t2_share, t3_share, t3_recent
- last_entry_age_days, entries_last_12_months
- accident_flag(true/false/unknown), accident_closed, accident_evidence_count

Konstanten:
- T3_RECENT_MONTHS = 12
- ACCIDENT_EVIDENCE_MIN = 2

---

## 3) Entscheidungslogik (rule-based, deterministisch)

### 3.1 Basis-Checks (K.O.)
- entries_total == 0 → Rot
- t3_share == 0 UND t2_share == 0 → Rot
- history_span_months < 3 UND entries_total < 3 → mindestens Orange

### 3.2 Punkteschema (0..100)
A) Historie (max 35)
- +10 entries_total >= 5
- +10 entries_total >= 12
- +10 history_span_months >= 24
- +5  critical_gaps_months <= 12

B) Verifizierung (max 40)
- +10 (t2_share + t3_share) >= 0.50
- +10 t3_share >= 0.25
- +10 t3_share >= 0.50
- +10 t3_recent == true (T3 in den letzten 12 Monaten)

C) Aktualität (max 25)
- +10 last_entry_age_days <= 180
- +5  last_entry_age_days <= 90
- +10 entries_last_12_months >= 2

Mapping:
- 0–24 Rot
- 25–49 Orange
- 50–74 Gelb
- 75–100 Grün (mit Sonderregeln)

### 3.3 Unfall-/Unknown-Sonderregeln (Grün-Bremse)
- accident_flag == true:
  Grün nur wenn accident_closed == true UND accident_evidence_count >= 2, sonst max Gelb.
- accident_flag == unknown:
  Ampel max Gelb (nie Grün), außer Status wird durch Nachweise eindeutig geklärt.

---

## 4) Ausgabeformat (Public Contract) – VERBINDLICH
Public-QR darf keine Rohmetriken ausgeben (keine counts, keine months, keine shares, kein `metrics`).

### 4.1 Public Response Schema (Minimal)
~~~json
{
  "level": "GREEN",
  "label": "Hohe Nachweisqualität",
  "reasons": [
    "Verifizierte Einträge vorhanden",
    "Regelmäßige Dokumentation",
    "Aktuelle Nachweise"
  ],
  "disclaimer": "Bewertet nur Nachweisqualität der Dokumentation, nicht den technischen Zustand."
}
~~~

Regeln:
- max 3 Gründe
- keine Zahlenwerte
- bei Unfall/unknown: zusätzlicher Hinweistext ohne Details

### 4.2 Internal Debug Schema (Nur ADMIN/SUPERADMIN)
Intern darf enthalten:
- score
- metrics
- decision trace
Diese Ausgabe muss RBAC-geschützt sein (nie öffentlich).

---

## 5) Testfälle (Acceptance)
- accident_flag=unknown & score hoch → max Gelb
- accident_flag=true, closed=false → max Gelb
- entries_total=0 → Rot
- Public response enthält niemals metrics/Counts/Percentages/Zeiträume

---
