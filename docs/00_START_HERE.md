./docs/00_START_HERE.md

\# 00\_START\_HERE — LifeTimeCircle / Service Heft 4.0



Stand: 2026-01-30 (Europe/Berlin)  

Kontakt: lifetimecircle@online.de  

Docs-SoT: `./docs/` (keine Altpfade/Altversionen)



\## 1) Worum geht’s (in 5 Sätzen)

\- \*\*LifeTimeCircle\*\* ist die Plattform; \*\*Service Heft 4.0\*\* ist das Kernprodukt: digitales, verifizierbares Lebenslauf-/Serviceheft für Fahrzeuge.

\- Fokus: \*\*Dokumentation + Nachweise + Verifizierungsstufen\*\*; optional \*\*Public-QR Mini-Check\*\*.

\- \*\*Kein Demo-Modus\*\*: Security/Privacy/RBAC werden produktionsreif gedacht und umgesetzt.

\- Public-QR ist \*\*niemals\*\* eine Aussage zum technischen Zustand, \*\*nur\*\* zur Doku-/Nachweisqualität.

\- Verkauf/Übergabe und interner Verkauf sind \*\*nur\*\* für \*\*VIP/Dealer\*\*.



\## 2) Die 4 Basis-Dokumente (damit nichts mehr „verloren“ geht)

1\. `./99\_MASTER\_CHECKPOINT.md` — Gesamtüberblick + aktuelle nächste Aktionen (die „Wahrheit“)  

2\. `./01\_DECISIONS.md` — nur verbindlich entschiedene Regeln (nichts Offenes)  

3\. `./02\_BACKLOG.md` — Epics/Stories/Tasks + Prioritäten  

4\. `./03\_RIGHTS\_MATRIX.md` — implementierbare RBAC-Matrix (API/Scope)



> Regel: Änderungen \*\*immer\*\* zuerst hier dokumentieren, dann implementieren. UI ist nie Sicherheitsinstanz.



\## 3) Fixe Leitplanken (nicht verhandelbar)

\### 3.1 Security/Privacy

\- \*\*deny-by-default\*\* + \*\*least privilege\*\*

\- \*\*RBAC serverseitig enforced\*\*

\- \*\*keine Secrets\*\* in Logs; \*\*keine Klartext-PII\*\* in Logs/Audit/Exports

\- Pseudonymisierung: \*\*HMAC\*\* (kein unsalted SHA)

\- Uploads: \*\*Allowlist + Limits + Quarantine by default\*\*, Freigabe nach Scan oder Admin-Approval, \*\*keine öffentlichen Uploads\*\*

\- Exports: \*\*redacted default\*\*; \*\*Full Export nur SUPERADMIN\*\* + Audit + TTL/Limit + Verschlüsselung



\### 3.2 Public-QR (öffentlich)

\- Bewertet ausschließlich \*\*Dokumentations-/Nachweisqualität\*\*, nie Technikzustand

\- Public Response: \*\*keine Metrics/Counts/Percentages/Zeiträume\*\*

\- Disclaimer (exakt, nicht abwandeln):

&nbsp; > „Die Trust-Ampel bewertet ausschließlich die Dokumentations- und Nachweisqualität. Sie ist keine Aussage über den technischen Zustand des Fahrzeugs.“



\### 3.3 Business-Gating

\- Verkauf/Übergabe-QR \& interner Verkauf: \*\*nur VIP \& DEALER\*\*

\- VIP-Gewerbe: \*\*max. 2 Staff\*\*, Freigabe nur \*\*SUPERADMIN\*\*

\- MODERATOR: nur Blog/News; keine PII; kein Export; kein Audit-Read



\## 4) Heute weitermachen (schnellster Einstieg)

\### 4.1 Backend lokal starten (DEV)

```powershell

cd ".\server"

$env:LTC\_SECRET\_KEY="dev-only-change-me-please-change-me-32chars-XXXX"

$env:LTC\_DB\_PATH=".\\data\\app.db"

$env:LTC\_DEV\_EXPOSE\_OTP="false"

.\\uvicorn\_run.ps1



