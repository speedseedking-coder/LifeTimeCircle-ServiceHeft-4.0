// File: C:\\Users\\stefa\\Projekte\\LifeTimeCircle-ServiceHeft-4.0\\docs\\policies\\KI\_Agenten\_Only\_LTC\_2026-3



LTC – KI-Agenten Richtlinie (Only) – 2026-3

Stand: 2026-01-28 (Europe/Berlin)



1\) Zweck

Diese Richtlinie steuert die Nutzung von KI-Agenten im Projekt „LifeTimeCircle – Service Heft 4.0“.

Ziel: Produktivqualität, Datenschutz, keine Geheimnis-/PII-Leaks, keine Altpfade/Altversionen.



2\) Scope

Gilt für:

\- interne KI-gestützte Tools/Agenten

\- Prompting/Automatisierung im Projektkontext

\- Generierung von Code, Specs, Policies, Tests



3\) Hard Rules (MUST)

\- Source of Truth ausschließlich:

&nbsp; C:\\Users\\stefa\\Projekte\\LifeTimeCircle-ServiceHeft-4.0\\docs

&nbsp; (inkl. docs\\policies)

\- Keine Altpfade/Altversionen referenzieren oder erzeugen.

\- Keine Secrets in Prompts/Outputs:

&nbsp; - keine Tokens, API-Keys, KMS-Keys, OTPs, Magic Links

\- Keine Klartext-PII in Prompts/Outputs:

&nbsp; - keine E-Mail/Name/Adresse/Telefon in Logs/Exports/Beispielen

\- deny-by-default + least privilege als Defaultannahme.

\- RBAC immer serverseitig enforced (UI ist nur Darstellung).

\- Public-QR: keinerlei Metrics/Counts/Prozente/Zeiträume im Public Output; Disclaimer Pflicht.



4\) Erlaubte Inhalte (MAY)

\- Abstrakte Beispiele mit Dummy-Daten (nicht identifizierend)

\- Pseudonyme via HMAC (ohne Secret offenzulegen)

\- Policies/Tests/Specs/Architektur-Dokumente



5\) Verbotene Inhalte (MUST NOT)

\- Explizite Nutzer-/Kundendaten

\- Debug-Ausgaben mit Rohdaten

\- Exportformate mit PII by default

\- „Öffentliche Uploads“ oder öffentliche Buckets



6\) Review Gate

Jeder KI-generierte Output gilt erst als akzeptiert, wenn:

\- Pfade korrekt (docs/policies)

\- keine Secrets/PII enthalten

\- Public-QR Regeln eingehalten

\- DoD/Acceptance Tests nicht verletzt



7\) Abweichungen

Abweichungen sind nur zulässig, wenn:

\- admin/SUPERADMIN Entscheidung dokumentiert ist (Decision Log)

\- Auditability gewährleistet bleibt



