\# docs/06\_WORK\_RULES.md

\# LifeTimeCircle – Service Heft 4.0

\*\*Arbeitsregeln / SoT-Spielregeln (für PRs, Reviews, Chat-Output)\*\*  

Stand: 2026-02-04



> Ziel: Produktionsreifer MVP (keine Demo). Security FIX: deny-by-default + least privilege. RBAC serverseitig enforced.

> Source of Truth: ./docs (keine Altpfade/Altversionen).



---



\## Priorität bei Konflikten (verbindlich)

1\) docs/99\_MASTER\_CHECKPOINT.md  

2\) docs/03\_RIGHTS\_MATRIX.md  

3\) Repo-Code (server/)  

4\) Backlog/sonstiges



---



\## Output-Regeln (verbindlich)

\- Deutsch, maximal konkret, keine Floskeln.

\- Nicht nachfragen außer zwingend; sonst Defaultannahme + direkte Commands (rg/Select-String) liefern.

\- Keine ZIPs. Nur Code.

\- Code immer: vollständiger Dateipfad + kompletter Dateiinhalt in Codeblock.

\- Wenn zu lang: Block 1/n … n/n, keine Platzhalter.



---



\## Public-QR (Fix)

\- Bewertet ausschließlich Nachweis-/Dokumentationsqualität, nie technischen Zustand.

\- Keine Metrics/Counts/Percentages/Zeiträume.

\- Disclaimer Pflicht (exakt, nicht abwandeln):



„Die Trust-Ampel bewertet ausschließlich die Dokumentations- und Nachweisqualität. Sie ist keine Aussage über den technischen Zustand des Fahrzeugs.“



---



\## RBAC (Fix)

\- Verkauf/Übergabe + interner Verkauf: nur VIP/DEALER.

\- VIP-Gewerbe: max 2 Staff, Freigabe nur SUPERADMIN.

\- MODERATOR: nur Blog/News; kein Export; kein Audit; keine PII.



---



\## Auth/Consent (Fix)

\- E-Mail Login + OTP/Magic-Link (one-time + TTL + rate-limit + anti-enum).

\- Consent (AGB+Datenschutz) Pflicht, Version+Timestamp auditierbar.



---



\## Security (Fix)

\- Keine Secrets/Tokens/PII im Klartext in Logs/Audit/Exports.

\- Pseudonymisierung: HMAC (kein unsalted SHA).

\- Uploads: Allowlist + Limits + Quarantine default; Freigabe nach Scan/Admin; keine öffentlichen Uploads.

\- Exports: redacted default; Full nur SUPERADMIN + Audit + TTL/Limit + Verschlüsselung.

\- Hinweis: Export/Redaction/HMAC benötigt LTC\_SECRET\_KEY (>=16); Tests/DEV setzen ihn explizit.



