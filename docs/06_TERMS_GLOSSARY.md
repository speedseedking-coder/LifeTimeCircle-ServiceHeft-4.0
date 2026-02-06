C:\\Users\\stefa\\Projekte\\LifeTimeCircle-ServiceHeft-4.0\\docs\\06\_TERMS\_GLOSSARY.md

\# LifeTimeCircle – ServiceHeft 4.0

\## Terms / Glossar (kanonisch)



Stand: 2026-01-29



\- \*\*Core / ServiceHeft-Core\*\*: Zentrale Anwendung, einzige Quelle für Vehicle/Timeline/Docs/Verification/Public-QR.

\- \*\*Source of Truth (SoT)\*\*: `C:\\Users\\stefa\\Projekte\\LifeTimeCircle-ServiceHeft-4.0\\docs` inkl. `docs/policies/`.

\- \*\*Policy\*\*: Verbindliche Regel (Security/Privacy/RBAC/Trustscore). Modul-Repos dürfen Policies nicht überschreiben.

\- \*\*Module (Repo)\*\*: Separates Repo für Workflows/Tools; liefert Events/Artefakte; Core entscheidet Timeline/Trustscore.

\- \*\*Tier\*\*: Paketzuordnung (Free / VIP / Dealer/VIP-Gewerbe).

\- \*\*Rolle\*\*: public/user/vip/dealer/moderator/admin/superadmin (siehe `docs/policies/ROLES\_AND\_PERMISSIONS.md`).

\- \*\*Scope\*\*: own/org/shared/public – zusätzlicher Filter zu Rollenrechten.

\- \*\*Vehicle / Fahrzeug\*\*: Fahrzeugprofil im Core.

\- \*\*QR-Fahrzeug-ID\*\*: Primäre, nicht-VIN Identität für Workflows/Verknüpfungen; Public zeigt nur `vehicle\_public\_id`.

\- \*\*VIN/WID\*\*: Sekundäre Identifikatoren; restriktiv; niemals public; nicht in Logs.

\- \*\*TimelineEntry\*\*: Eintrag im Serviceheft-Lebenslauf (Events/Services/Wartung/Unfall/Diagnose).

\- \*\*Evidence / Nachweis\*\*: Dokument/Foto/PDF/Beleg zu einem TimelineEntry.

\- \*\*Quarantäne (Upload)\*\*: Default-Zustand nach Upload; Inhalt erst nach Scan/Approval sichtbar (Policy).

\- \*\*Verification T1/T2/T3\*\*: Verifizierungsstufen (T1 Selbstauskunft, T2 Beleg vorhanden, T3 akkreditiert verifiziert).

\- \*\*Public-QR Mini-Check\*\*: Öffentliche Ansicht; bewertet nur Dokumentationsqualität; keine Zahlen/Zeiträume; Disclaimer Pflicht.

\- \*\*Trustscore / Ampel\*\*: Rot/Orange/Gelb/Grün nach Dokumentations-/Nachweisqualität (nicht technischer Zustand).

\- \*\*Unfalltrust\*\*: Bei Unfall nur Grün, wenn Abschluss + Belege dokumentiert sind.

\- \*\*Transfer / Übergabe-QR\*\*: Besitz-/Übergabe-Flow; nur vip/dealer; Auditpflicht.

\- \*\*AuditEvent\*\*: Sicherheits-/Governance-Event (redacted, keine PII/Secrets).

\- \*\*Step-up\*\*: Zusätzliche Bestätigung für sensitive Admin-Aktionen (z.B. Full Export, Role Grant).

\- \*\*Redacted Export\*\*: Export ohne PII/Secrets; Default.

\- \*\*Full Export\*\*: Nur admin; verschlüsselt; TTL/Limit; Auditpflicht.




