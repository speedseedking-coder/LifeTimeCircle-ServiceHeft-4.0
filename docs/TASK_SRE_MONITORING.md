# SRE: Monitoring & On-Call-Rota Setup

Stand: **2026-03-01** (Europe/Berlin)

**Owner:** SRE-Lead / Ops-Lead  
**Deadline:** Bis **2026-03-05** (nach DevOps Infra-Setup)  
**Docs zum Lesen:** `docs/15_MONITORING_INCIDENT_RESPONSE.md`

---

## Phase 1: Monitoring-Tool Selection & Setup (Day 1–2)

### 1.1 Tool-Entscheidung

| Tool | Setup | Cost/Mo | Features | Best For |
|------|-------|---------|----------|----------|
| **New Relic** | 1h | $100–500 | Browser + Server + Logs | Full-Stack Monitoring |
| **DataDog** | 1h | $150–600 | Advanced APM + Logs + Custom Metrics | Enterprise |
| **Prometheus + Grafana** | 8h | $0 (self) | Metrics-focused, Open-Source | Cloud-Native |
| **CloudWatch** (AWS only) | 30min | ~$5 | Integrated with AWS | AWS-only stacks |
| **Grafana Cloud** | 1h | $50–200 | Hosted Prometheus + Loki | Modern Cloud |

**Vergleich für LifeTimeCircle:**

```
Wir wollen:
✅ Fast Setup (Prod bald ready)
✅ Error & APM Tracking (API Latency, Exceptions)
✅ Log Aggregation (zentral, ohne PII)
✅ Alerting (Slack, Email, SMS)
✅ Budget-friendly

EMPFEHLUNG: New Relic Starter oder Grafana Cloud
  Alternative (AWS): CloudWatch (schnellste Integration)
```

**Gewählt:** `___________________________` (ausfüllen)

---

### 1.2 Metriken definieren (z. B. für New Relic)

Welche Metriken müssen wir tracken?

| Metriken | Alert-Schwelle | Notification |
|----------|-----------------|--------------|
| **API Response Time (p99)** | > 2s für 5min | Slack #alerts |
| **API Error Rate (5xx)** | > 0.5% für 5min | Slack + PagerDuty |
| **Frontend Page Load** | > 3s | Slack #alerts |
| **Database Connections** | > 80 von 100 pool | Slack #alerts |
| **Disk Space (RDS)** | < 10% free | Slack #alerts |
| **Memory Usage (API)** | > 85% | Slack #alerts |
| **Request Rate** | > 1000 req/sec | Log only (tracking) |
| **4xx Errors (Auth/404)** | > 5% | Slack #warnings |

**Output:** Alert-Liste für Tool eintragen

---

### 1.3 Instrumentation (Logging, Tracing)

#### API-Side (Python/FastAPI):

```python
# server/main.py - Add New Relic (oder equivalentes)
import logging
import newrelic.agent

# Initialize New Relic
newrelic.agent.initialize('/path/to/newrelic.ini')

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Middleware für Request-Logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    
    # Log (OHNE sensitive data)
    logger.info(f"{request.method} {request.url.path} {response.status_code} {duration:.3f}s")
    
    # New Relic automatic (via middleware)
    return response

# Error Handling
@app.exception_handler(Exception)
async def exception_handler(request: Request, exc: Exception):
    logger.error(f"Exception: {exc}", exc_info=True)
    # New Relic automatically captures
    raise
```

#### Frontend-Side (React):

```typescript
// packages/web/src/monitoring.ts
import * as Sentry from "@sentry/react";

// Initialize Sentry (oder equivalent)
Sentry.init({
  dsn: process.env.REACT_APP_SENTRY_DSN,
  environment: "production",
  tracesSampleRate: 0.1,
  maxBreadcrumbs: 50,
});

// Error Boundary
export const ErrorBoundary = ({ children }) => (
  <Sentry.ErrorBoundary fallback={<ErrorPage />}>
    {children}
  </Sentry.ErrorBoundary>
);

// Performance Monitoring
Sentry.startBrowserTracingWithReact({
  routingInstrumentation: new Sentry.ReactRouterInstrumentation()
});
```

---

### 1.4 Setup im Monitoring-Tool

**Example: New Relic Setup**

```bash
# 1. Create Free Tier Account
# → https://newrelic.com/signup

# 2. Install Agent (Python)
pip install newrelic

# 3. Create newrelic.ini
newrelic-admin generate-config YOUR_LICENSE_KEY newrelic.ini

# 4. Wrap Application
newrelic-admin run-program uvicorn server.main:app --host 0.0.0.0 --port 8000

# 5. Dashboard: Check if data comes in
# → https://one.newrelic.com/nr1-core?state=6db0a5cf-eebf-4ce5-94a5-0708155ca8fe
```

---

## Phase 2: Alerting Setup (Day 2)

### 2.1 Alert Policies formulieren

Beispiel New Relic Alert Policy:

```
Alert Policy: "LifeTimeCircle Production"

Notification Channel:
- Slack: #incidents (critical)
- Slack: #alerts (warning)
- Email: sre-team@company.com (critical)
- PagerDuty: SRE On-Call (critical)

Conditions:

1. API Error Rate High
   Metric: Transaction Error Rate
   Threshold: > 0.5% for 5 min
   Severity: CRITICAL
   Notify: Slack #incidents + PagerDuty

2. API Response Time High
   Metric: Apdex (Application Performance Index)
   Threshold: < 0.95 (meaning 95%+ satisfied)
   Duration: 5 minutes
   Severity: WARNING
   Notify: Slack #alerts

3. Database Connections High
   Metric: db.pool.connections
   Threshold: > 80 of 100
   Duration: 2 minutes
   Severity: WARNING
   Notify: Slack #alerts

4. Frontend API Errors
   Metric: (via Sentry) Errors in React
   Threshold: > 10 unique errors / 5 min
   Severity: WARNING
   Notify: Slack #alerts
```

### 2.2 Incident Notification Channels

Setting up Notifications:

- [ ] **Slack Integration**
  ```
  New Relic → Settings → Notification channels → Add "Slack"
  → Connect to workspace
  → Select channels: #incidents, #alerts
  ```

- [ ] **PagerDuty (optional, für On-Call Paging)**
  ```bash
  # Create PagerDuty Service:
  # → https://app.pagerduty.com/services
  
  # Integrate with New Relic:
  # Settings → Notification channels → Add "PagerDuty"
  # → Generate Integration Key in PagerDuty
  # → Enter in New Relic
  ```

- [ ] **Email**
  ```
  Settings → Users & Roles → Set email notification preferences
  ```

---

## Phase 3: On-Call-Rota aufstellen (Day 2–3)

### 3.1 On-Call Schedule

Definiere die Rota (Beispiel):

```
=== LifeTimeCircle On-Call Rota ===

Effective: 2026-03-06 (nach Go-Live)

Week 1 (Mon-Sun):
  Primary (Mon-Fri): Alice (alice@company.com, +49 123 456789, @alice_slack)
  Backup (Mon-Fri):  Bob (bob@company.com, +49 987 654321, @bob_slack)
  Weekend (Sat-Sun): Carol (carol@company.com, +49 555 666777, @carol_slack)

Week 2:
  Primary: Bob
  Backup: Carol
  Weekend: Alice

[... continues ...]

Rotations:
- Primary rotation: Weekly (Monday)
- Escalation: Primary unreachable after 15 min → Backup
- Management escalation: Unresolved after 1h → Engineering Manager
```

**Tool Options:**
- [ ] PagerDuty (commercial, recommended)
- [ ] Opsgenie (AWS managed)
- [ ] Simple Spreadsheet (manual, aber billig)
- [ ] Custom Slack Workflow (DIY)

**Setup in PagerDuty:**

```bash
# 1. Create Escalation Policy
PagerDuty → Escalation Policies → Create
  Level 1: Alice (15 min)
  Level 2: Bob (30 min)
  Level 3: Manager (email)

# 2. Create On-Call Schedule
PagerDuty → On-Call Schedules
  Weekly rotation, Alice starts
  Includes weekends

# 3. Link to Services
PagerDuty → Services → LifeTimeCircle API
  → Add Escalation Policy
  → Save
```

---

### 3.2 On-Call Responsibilities

Document was On-Call Person must do:

```markdown
# On-Call Responsibilities

## Availability
- Available within 15 min (respond to alert)
- Have laptop + internet during duty
- Forward phone to mobile if away

## During Incident
1. **Receive Alert** (PagerDuty → Phone/Slack)
2. **Assess** (Check dashboards, logs, status)
   - Is it a real problem or false positive?
   - What's affected? (API? DB? Frontend?)
3. **Communicate**
   - Slack #incidents channel
   - Customer? (if needed)
4. **Mitigate** (Quick fix or escalate?)
   - Simple fix: roll out fix
   - Complex: escalate to Principal Engineer
5. **Resolve** (Verify healthy, document)
   - Confirm metrics back to normal
   - Quick summary to #incidents

## After Incident
- Within 24h: Post-Mortem (if incident > 15 min)
- Document what happened, why, how to prevent next time

## Compensation
- Per company policy: X hours of comp time if paged outside normal hours
```

---

### 3.3 Runbooks für häufige Probleme

Erstelle schnelle Action-Guides:

```markdown
## Runbook: High API Error Rate (>1%)

**Detection:** Alert "API Error Rate High"
**Suspected Causes:** 
  - Database connection pool exhausted
  - Deployment broke something
  - External service down (email, payment)

**Steps:**
1. SSH to Prod API server:
   ssh -i prod-key.pem ec2-user@api-prod.company.com

2. Check API logs:
   tail -f /var/log/lifetimecircle/api.log | grep ERROR

3. Check database:
   psql -h prod-db.company.com -U postgres
   SELECT count(*) FROM pg_stat_activity;  — show connections

4. Check metrics:
   https://one.newrelic.com → API dashboard
   Look for specific endpoint errors

5. If recent deploy:
   git log --oneline -1
   # If suspicious commit - trigger rollback:
   bash ./tools/rollback.sh

6. Escalate if unsure:
   Post in #incidents: @engineering-lead can you take a look?
```

Mehr Runbooks:
- [ ] "Database Hard Down" (how to failover)
- [ ] "Frontend 404 Storm" (cache purge?)
- [ ] "Memory Leak" (restart services)
- [ ] "DDoS Attack" (enable WAF)

---

## Phase 4: Testing & Drills (Day 3)

### 4.1 Fake Incident Drill

Test your monitoring + On-Call response:

```bash
# 1. Simulate an error on staging
# (Intentionally break something to trigger alert)

# 2. Primary on-call should receive alert
# (Check PagerDuty, Slack, Phone)

# 3. Primary responds:
# - Ack in PagerDuty
# - Post to #incidents
# - Start investigating

# 4. After 5 min:
# - Fix the issue
# - Resolve incident

# 5. Debrief:
# - Did alert trigger correctly?
# - Was response time < 15 min?
# - Any process issues?
```

**Schedule:** Run drill once/month before going live, then quarterly

---

### 4.2 Runbook Testing

Walk through each runbook with team:

- [ ] "High Error Rate" runbook
  - [ ] Read steps out loud
  - [ ] Check if cmd names are correct
  - [ ] Verify ssh access works
  - [ ] Update with actual server names / URLs

- [ ] "Database Down" runbook
  - [ ] Can we actually SSH to DB server?
  - [ ] Do we have access to failover?
  - [ ] Is restore procedure tested?

---

## Phase 5: Documentation & Training (Day 3)

### 5.1 Create Operations Handbook

Erstelle `docs/SRE_OPERATIONS_HANDBOOK.md`:

```markdown
# SRE Operations Handbook – LifeTimeCircle Prod

## Monitoring
- Tool: [New Relic / DataDog / etc]
- Dashboard: https://one.newrelic.com/...
- Alert channels: Slack #incidents, PagerDuty, Email

## On-Call
- Schedule: https://pagerduty.com/schedules/...
- Weekly rotation every Monday
- Backup escalation after 15 min unresponded

## Key Contacts
- SRE Lead: Alice (@alice_slack)
- Engineering Manager: Dave (dave@company.com)
- Security: [Contact]

## Incident Response
See runbooks below.

## Runbooks
- API Error Rate High
- Database Down
- Memory Leak
- Frontend Issues
...
```

### 5.2 Team Training Session

Schedule 1h meeting:

```
Agenda:
1. Demo Monitoring Dashboard (10 min)
   - Show where to see metrics
   - Show how to drill down on errors

2. Demo Alert Channels (5 min)
   - Show Slack alerts
   - Show PagerDuty paging

3. Walk Through Runbooks (30 min)
   - "High Error Rate" step-by-step
   - "Database Down" step-by-step
   - Q&A

4. Practice Incident Drill (10 min)
   - Simulate alert
   - Primary on-call responds
   - Walk through resolution

5. Q&A (5 min)
```

---

## Phase 6: Handoff Checklist

### 6.1 What DevOps-Lead Needs to Provide

Ask DevOps for:

- [ ] API Prod Server IPs / SSH access
- [ ] Database Prod Server IP / Connection String
- [ ] Frontend CDN / Web Server Logs
- [ ] Application Performance Metrics hookup info
- [ ] CloudWatch / native platform monitoring URLs

### 6.2 What Security-Lead Needs to Know

Share with Security:

- [ ] Monitoring tool usage (data retention, encryption)
- [ ] PII protections in logs (implement scrubbers)
- [ ] Access controls to dashboards (who can see what?)
- [ ] Audit trails for dashboard access

---

## Checklist: Complete

- [ ] Monitoring tool chosen & account created
- [ ] Metrics defined (API error, latency, DB, etc.)
- [ ] Agents installed (Python + React)
- [ ] Alert policies configured
- [ ] Notification channels setup (Slack, Email, PagerDuty)
- [ ] On-Call rota defined (who, when, escalation)
- [ ] Runbooks created & reviewed (5+ scenarios)
- [ ] Drill/Testing completed
- [ ] Team trained
- [ ] Documentation created (`SRE_OPERATIONS_HANDBOOK.md`)
- [ ] Handoff to DevOps/Security completed

---

## Deadline & Output

**Deadline:** **2026-03-05 EOD**

**Deliverables:**
- [ ] Monitoring tool account + API key
- [ ] Dashboard URL(s) to watch
- [ ] Alert policies active (5+)
- [ ] Slack/PagerDuty channels linked
- [ ] `docs/SRE_OPERATIONS_HANDBOOK.md` created
- [ ] On-Call rota documented (PagerDuty or spreadsheet)
- [ ] Runbook doc for common scenarios (5+)
- [ ] Team drill completed
- [ ] Access info shared with all SRE/Ops

---

**Wenn fertig → Ready für Staging-Deploy & Load-Test!** ✅
