C:\\Users\\stefa\\Projekte\\LifeTimeCircle-ServiceHeft-4.0\\docs\\07\_CONTEXT\_PACK.md

\# LifeTimeCircle – ServiceHeft 4.0

\## Context Pack (Copy-Pflicht in Modul-Repos)



Stand: 2026-01-29  

Kontakt: lifetimecircle@online.de



\### Ziel

Produktionsreife Umsetzung (keine Demo). Default: deny-by-default + least privilege. RBAC serverseitig enforced.



\### Source of Truth

`C:\\Users\\stefa\\Projekte\\LifeTimeCircle-ServiceHeft-4.0\\docs`  

Policies: `C:\\Users\\stefa\\Projekte\\LifeTimeCircle-ServiceHeft-4.0\\docs\\policies`



\### Hard Constraints (nicht verhandelbar)

\- RBAC serverseitig enforced (UI ist nie Sicherheitsgrenze).

\- Deny-by-default + least privilege.

\- Keine Secrets in Logs (keine OTPs/Tokens/Magic Links).

\- Keine Klartext-PII in Logs/Exports.

\- Pseudonymisierung via HMAC (kein unsalted SHA).

\- Uploads: Allowlist + Limits + Quarantine by default; Freigabe nach Scan oder Admin-Approval; keine öffentlichen Uploads.

\- Exports: standardmäßig redacted; Full Export nur admin + Audit + TTL/Limit + Verschlüsselung.

\- Moderator: nur Blog/News; keine PII; kein Export; kein Audit; kein Zugriff auf Vehicles/Entries/Documents/Verification.

\- Verkauf/Übergabe-QR \& interner Verkauf: nur vip/dealer/admin.

\- VIP-Gewerbe: max 2 Staff; Freigabe nur admin.



\### Public-QR Trustscore (Public Output Regeln)

\- Bewertet ausschließlich Nachweis-/Dokumentationsqualität (nie technischen Zustand).

\- Public Response enthält keine Metrics/Counts/Percentages/Zeiträume.

\- Disclaimer ist Pflicht und immer sichtbar.

\- Public enthält keine PII, keine Dokument-URLs, keine VIN/WID.



\### DoD vor Abgabe (Pflicht)

\- Navigation/Buttons ok, Empty States ok.

\- RBAC serverseitig + Tests (inkl. Negativfälle).

\- Public-QR ohne Metrics + Disclaimer.

\- Logs/Audit/Export konform (keine Secrets, keine Klartext-PII).

\- Uploads/Exports policy-konform.

\- Keine Pfadfehler / keine Altpfade/Altversionen, die Policy-Drift erzeugen.



