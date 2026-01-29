\# Dateiname: docs/AI\_HINTS.md

Version: 2026-03 | Last-Update: YYYY-MM-DD



Projekt:

\- LifeTimeCircle – Service Heft 4.0 (Brand: „LifeTimeCircle“, Modul: „Service Heft 4.0“, Kontakt: lifetimecircle@online.de)

\- Produktion statt Demo. Default: deny-by-default + least privilege. RBAC serverseitig enforced.

\- Source of Truth: C:\\Users\\stefa\\Projekte\\LifeTimeCircle-ServiceHeft-4.0\\docs (keine Altpfade/Altversionen).



Sprache/Output:

\- Deutsch, maximal konkret. Keine Floskeln. Nicht nachfragen außer zwingend (sonst Defaultannahme).

\- Keine ZIPs. Nur Code.

\- Code: Dateipfad+Dateiname + kompletter Dateiinhalt. Wenn zu lang: Block 1/n … bis fertig. Keine Platzhalter/halben Snippets.



Public-QR Trustscore:

\- Bewertet ausschließlich Nachweis-/Dokumentationsqualität (nie technischen Zustand).

\- Ampel Rot/Orange/Gelb/Grün nach: Historie, T-Level (T1/T2/T3), Aktualität/Regelmäßigkeit, Unfalltrust (Grün bei Unfall nur Abschluss+Belege).

\- Public Response: keine Metrics/Counts/Percentages/Zeiträume. Disclaimer Pflicht.



Rollen:

\- Verkauf/Übergabe-QR \& interner Verkauf nur VIP/DEALER.

\- VIP-Gewerbe: max 2 Staff, Freigabe nur SUPERADMIN.

\- MODERATOR nur Blog/News; keine PII; kein Export; kein Audit.



Auth \& Consent:

\- E-Mail Login + Verifizierung (One-time + TTL + Rate-Limits + Anti-Enumeration).

\- AGB+Datenschutz Pflicht; Version + Timestamp speichern/protokollieren.



Security/Privacy:

\- Keine Secrets in Logs. Keine Klartext-PII in Logs/Exports. Pseudonymisierung via HMAC (kein unsalted SHA).

\- Exports: standardmäßig redacted; Full Export nur SUPERADMIN + Audit + TTL/Limit + Verschlüsselung.

\- Uploads: Allowlist + Limits + Quarantine by default; Freigabe nach Scan oder Admin-Approval; keine öffentlichen Uploads.



DoD vor Abgabe:

\- Navigation/Buttons ok, Empty States ok, RBAC serverseitig, Public-QR ohne Metrics + Disclaimer, Logs/Audit/Export konform, keine Pfadfehler.

\- Bei Konflikt: Policy hat Vorrang; Abweichung kurz nennen.



