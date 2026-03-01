# Operations & Infrastructure – Overview

Stand: **2026-03-01** (Europe/Berlin)

Für alle, die die LifeTimeCircle Service Heft 4.0 in Production bringen, betreiben und am Laufen halten.

---

## 📚 Dokumentation Übersicht

| Dokument | Zweck | Leser |
|----------|-------|-------|
| **14_DEPLOYMENT_GUIDE.md** | Wie Release Candidate deployen | DevOps, Release Engineer |
| **15_MONITORING_INCIDENT_RESPONSE.md** | Überwachung, Alerts, Was tun bei Fehlern | SRE, On-Call, Manager |
| **16_SECRETS_MANAGEMENT.md** | Geheimnisse speichern, rotieren, sichern | Security, DevOps, Backend-Lead |
| **05_MAINTENANCE_RUNBOOK.md** | Lokale Dev-Routinen, Verifikation | Alle Developer |
| **13_GO_LIVE_CHECKLIST.md** | Punkte vor echtem Live-Rollout | Project Manager, QA |
| **12_RELEASE_CANDIDATE_2026-03-01.md** | Was im RC enthalten ist | QA, Product |
| **99_MASTER_CHECKPOINT.md** | Aktueller Projekt-Stand (SoT) | Alle |

---

## 🚀 Der Weg zu Production (Checkliste)

### Phase 1: Vorbereitung (Woche vor Deployment)

- [ ] **Architektur-Entscheidungen** treffen
  - Hosting-Plattform? (AWS, GCP, Heroku, On-Prem?)
  - API-Deployment? (Docker, Direct, Managed Service?)
  - Datenbank? (RDS, Cloud SQL, Managed PostgreSQL?)
  - Frontend? (CDN, Vercel, same-host static?)

- [ ] **Secrets generieren & speichern**
  - LTC_SECRET_KEY (32+ Bytes)
  - Database-Passwort
  - ggf. weitere Keys
  - → In Secret Manager (AWS/Azure/Vault) speichern

- [ ] **Infrastruktur provisio**lesen**
  - Prod-Server/Instances hochfahren
  - Networking & Firewall konfigurieren
  - Datenbank-Instance erstellen
  - TLS-Zertifikate besorgen/per _Let's Encrypt_)

- [ ] **CI/CD Pipeline** vorbereiten
  - GitHub Actions Workflows prüfen
  - Deploy-Secrets in GitHub rein
  - Deployment-Skript/Stage fertig

### Phase 2: Test-Deployment (3–5 Tage vor Live)

- [ ] **Staging-Deployment** durchführen
  - Repo clonen, rc-2026-03-01 auschecken
  - Secrets ins Staging-Env laden
  - Build & Deploy durchführen
  - Smoke Tests durchlaufen
  - Logs prüfen (keine Errors)

- [ ] **Last-Minute-Bugs** fixen
  - Wenn Fehler in Staging: Fix im Code, PR, New RC-Tag
  - Erneut stagieren & testen
  - Wenn OK: Go für Prod

### Phase 3: Live-Deployment (Go-Live-Tag)

- [ ] **Finales Gate** passieren
  - `git diff --check` ✅
  - `npm run build` ✅
  - `npm run e2e` ✅
  - `tools/test_all.ps1` ✅
  - `tools/ist_check.ps1` ✅

- [ ] **Prod-Secrets** laden
  - LTC_SECRET_KEY in Prod-Env einrichten
  - Database Password konfigurieren
  - TLS Cert aktivieren

- [ ] **Deployment** durchfahren
  - API deployen (Uvicorn starten oder Docker)
  - Frontend static files deployen
  - DNS updaten (oder Load Balancer switchern)

- [ ] **Health Checks**
  - API: `curl https://app.lifetimecircle.de/api/health` → 200 OK
  - Frontend: `curl https://app.lifetimecircle.de/` → 200 OK
  - Logs: `tail -f /var/log/lifetimecircle/api.log` → keine 5xx

- [ ] **Smoke Tests** manuell
  - Public-Seite laden ✅
  - Auth-Flow starten ✅
  - Admin-Login starten ✅

### Phase 4: Nach Deploy (Erste Woche)

- [ ] **Hour 1–3:** Intensives Monitoring
  - API-Error-Rate < 0.1%?
  - Response Times normal?
  - Kurz-Checkouts, ob Nutzer berichten von Fehlern

- [ ] **Hour 6–24:** Beobachtend
  - Tägliche Logs durchsehen
  - Performance-Trends
  - Datenbank-Connections/Queries OK?

- [ ] **Tag 2–7:** Regelmäßige Checks
  - Backups OK?
  - Keine Sicherheits-Incidents?
  - Monitoring-Alerting funktioniert?

- [ ] **Woche 2+:** Leichte Monitoring
  - Weiterhin watchful, aber nicht intensiv
  - Alerting bleibt aktiv
  - Post-Incident Reviews, falls nötig

---

## 🔧 Wichtigste Entscheidungen pro Team

### 🏛️ **Infrastructure / DevOps**

**Was muss ich tun?**
1. Hosting-Plattform wählen (Kosten, Compliance, Scaling)
2. API + Frontend + DB proviszonieren
3. Networking, Firewall, TLS aufsetzen
4. CI/CD Deploy-Stage schreiben
5. Monitoring & Logging einrichten

**Dokumente lesen:** `docs/14_DEPLOYMENT_GUIDE.md`

**Template-Fragen:**
- Welche Cloud? AWS, GCP, Azure, On-Premise?
- Containerisierung (Docker) oder direkter Deploy?
- Load-Balancer / Auto-Scaling nötig?
- Backup-Strategie? (RTO/RPO)

---

### 🔐 **Security / Secrets Manager**

**Was muss ich tun?**
1. Secret-Manager-Lösung auswählen (AWS Secrets, Azure Key Vault, Vault)
2. IAM Policies einrichten (nur Prod-Server darf Secrets lesen)
3. Rotation-Prozess automatisieren (wenn möglich)
4. Audit-Logging aktivieren (wer liest wann welche Secrets?)

**Dokumente lesen:** `docs/16_SECRETS_MANAGEMENT.md`

**Template-Fragen:**
- Wo leben Production-Secrets? (AWS/Azure/On-Prem?)
- Rotation automatisch oder manuell?
- Wer darf Secrets rotieren? (nur Admin?)

---

### 📊 **SRE / On-Call**

**Was muss ich tun?**
1. Monitoring Setup (New Relic, DataDog, Prometheus, etc.)
2. Alert-Schwellen definieren (Error Rate, Latency, Availability)
3. On-Call-Rota aufstellen
4. Incident-Response-Runbook testen
5. Post-Mortem-Prozess etablieren

**Dokumente lesen:** `docs/15_MONITORING_INCIDENT_RESPONSE.md`

**Template-Fragen:**
- SLA: 99%, 99.5%, 99.9%?
- Alert-Kanäle: Slack, PagerDuty, SMS?
- RTO / RPO angestrebt?
- Rollback-Zeit < 5 Min möglich?

---

### 🚀 **Release / Project Manager**

**Was muss ich tun?**
1. Vor Live: Go-Live-Checklist durchgehen
2. Stakeholder-Freigaben einholen (Geschäftsführung, Legal, Product)
3. Communication-Plan: Status-Page, Customer-Notify
4. Post-Deployment-Handoff an Support/SRE

**Dokumente lesen:** `docs/13_GO_LIVE_CHECKLIST.md`, `docs/12_RELEASE_CANDIDATE_2026-03-01.md`

**Template-Fragen:**
- Wann ist Kundenankündigung geplant?
- Support-Team bereit?
- Rollback-Plan kommuniziert?

---

## 📋 Kritische Pfade & Abhängigkeiten

```
┌────────────────────────────────────┐
│ Code Release (rc-2026-03-01)       │
│ - Alle Gates grün ✅               │
│ - Tagged & gepusht                │
└─────────────────┬──────────────────┘
                  │
    ┌─────────────┼─────────────┐
    │             │             │
    V             V             V
┌─────────────┘ ┌──────────┐ ┌──────────┐
│ Secrets      │ Infra    │ │ Monitoring
│ Manager      │ Setup    │ │ & Logging
│ eingerichtet │ ready    │ │ bereit
└─────────────┘ └──────────┘ └──────────┘
    │             │             │
    └─────────────┼─────────────┘
                  │
                  V
         ┌────────────────┐
         │ Deploy starten │
         └────────────────┘
                  │
                  V
         ┌────────────────┐
         │ Health-Checks  │
         └────────────────┘
                  │
         ┌────────┴────────┐
         │                 │
       ✅ OK            ❌ Fehler
         │                 │
         V                 V
    Live! 🎉           Rollback
```

---

## 🎓 Für verschiedene Rollen

### Developer
- Liest: `docs/05_MAINTENANCE_RUNBOOK.md`
- Muss wissen: Lokale Dev-Setup, wie man Gates grün macht
- Handelt: Bugfixes, Features bis zur Prod-Reife testen

### DevOps / Infra-Lead
- Liest: `docs/14_DEPLOYMENT_GUIDE.md`, `docs/16_SECRETS_MANAGEMENT.md`
- Muss wissen: Architektur-Entscheidung, IaC, Secrets, Monitoring
- Handelt: Provisioning, Deployment-Automation, Incident-Koordination

### SRE / On-Call
- Liest: `docs/15_MONITORING_INCIDENT_RESPONSE.md`
- Muss wissen: Alerts, Runbooks, RTO/RPO, wie man rollback macht
- Handelt: Monitoring überwachen, Incidents managen, Post-Mortems

### QA / Release Manager
- Liest: `docs/13_GO_LIVE_CHECKLIST.md`, `docs/12_RELEASE_CANDIDATE_2026-03-01.md`
- Muss wissen: Was ist in Release, was ist überprüft, Go-Live-Kriterien
- Handelt: Final sign-off, Kommunikation, Stakeholder-Checkboxes

### Security / Compliance
- Liest: `docs/16_SECRETS_MANAGEMENT.md`, `docs/15_MONITORING_INCIDENT_RESPONSE.md`
- Muss wissen: Secrets Management, Audit Logging, Incident-Response
- Handelt: Secrets-Setup validieren, Audit-Trails prüfen

---

## ⚠️ Häufige Fehler durchführ (vermeidet diese!)

| Fehler | Warum schlecht | Fix |
|--------|--- |-----|
| **Secrets in Git committed** | Exposure beim Leak | `.gitignore` + pre-commit hook + Secret-Scan |
| **Keine Monitoring vor Live** | Fehler nicht erkannt | Monitoring vor Deploy fertig |
| **Falscher Secret bei Deploy** | Auth-Fehler, API down | Secret-Manager frühzeitig testen |
| **Kein Rollback-Plan** | Fehler = Downtime | RTO/RPO definieren, Rollback-Prozess testen |
| **Nicht alle Gates überprüft** | Überraschungs-Bugs | `npm run build` + `npm run e2e` + `tools/test_all.ps1` |
| **Deployment ohne Kommunikation** | Nutzer überrascht | Status-Page + Ankündigung vorher |

---

## 🆘 Kontakte & Eskalations-Wege (TBD)

Fülle diese aus, bevor Live geht:

```
Backend-Lead:        [Name] [Phone] [Slack]
Frontend-Lead:       [Name] [Phone] [Slack]
DevOps-Lead:         [Name] [Phone] [Slack]
Security-Lead:       [Name] [Phone] [Slack]
Project-Manager:     [Name] [Phone] [Slack]
Executive Escalation: [Name] [Phone] [Slack]

Critical Incident Paging:
- Tool: [PagerDuty / Opsgenie / Custom]
- Alerting: [Slack / SMS / Call]

Status Communication:
- Public Status: https://status.lifetimecircle.de (TBD)
- Internal Incident Channel: #incidents auf Slack
- Customer Notify: [Email Template / Tool TBD]
```

---

## 📞 Support & Questions

Fragen zu Deployment, Operations, Secrets? → Siehe relevante Docs oben.

Fragen zu Code-Quality, Testing? → `docs/05_MAINTENANCE_RUNBOOK.md`

Fragen zu Feature-Spezifikation? → `docs/02_PRODUCT_SPEC_UNIFIED.md`

Fragen zu architektonischen Entscheidungen? → `docs/01_DECISIONS.md`
