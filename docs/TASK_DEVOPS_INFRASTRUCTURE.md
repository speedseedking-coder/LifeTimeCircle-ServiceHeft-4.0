# DevOps: Infrastruktur-Architektur – Entscheidungsmatrix & Aktionsplan

Stand: **2026-03-01** (Europe/Berlin)

**Owner:** DevOps-Lead / Infrastructure-Lead  
**Deadline:** Bis **2026-03-03**  
**Docs zum Lesen:** `docs/00_OPERATIONS_OVERVIEW.md` + `docs/14_DEPLOYMENT_GUIDE.md`

---

## Phase 1: Architektur-Entscheidungen treffen (Tag 1–2)

### 1.1 Fragen zur Plattform-Wahl

Beantworte diese Fragen und dokumentiere die Gründe:

| Frage | Optionen | Gewählt | Grund | Kosten (geschätzt) |
|-------|----------|---------|-------|-------------------|
| **Cloud-Plattform?** | AWS / GCP / Azure / Heroku / On-Premise | ☐ TBD | | |
| **API-Hosting?** | Docker Compose / ECS / GKE / Direct Deploy / Heroku | ☐ TBD | | |
| **Frontend-Hosting?** | S3+CloudFront / GCS+CDN / Netlify / Vercel / Same-Host | ☐ TBD | | |
| **Datenbank?** | RDS PostgreSQL / Cloud SQL / Aurora / Self-hosted | ☐ TBD | | |
| **Monitoring-Tool?** | New Relic / DataDog / Prometheus / CloudWatch | ☐ TBD | | |
| **Log-Aggregation?** | ELK / Splunk / CloudLogging / None | ☐ TBD | | |

**Beispiel-Entscheidung (AWS):**
```
Cloud: AWS
  → API: Docker auf ECS Fargate
  → Frontend: S3 + CloudFront
  → Database: RDS PostgreSQL (multi-AZ)
  → Monitoring: CloudWatch + X-Ray
  → Logs: CloudWatch Logs
  Kosten: ~$500–1000/Monat
```

---

## Phase 2: Infrastruktur provisio**nieren (Tag 2–3)

### 2.1 Checkliste: Networking & Security Setup

- [ ] **VPC / Network**
  - [ ] VPC erstellen (z. B. 10.0.0.0/16)
  - [ ] Subnets: Public (für ALB), Private (für API), Private (für RDS)
  - [ ] Internet Gateway, NAT Gateway konfigurieren
  - [ ] Route Tables setzen up
  - Dokumentieren: VPC-ID, Subnet-IDs, CIDR-Ranges

- [ ] **Security Groups**
  - [ ] SG für ALB: Inbound 80, 443 (HTTP/HTTPS) von überall
  - [ ] SG für API: Inbound 8000 vom ALB only
  - [ ] SG für RDS: Inbound 5432 vom API-SG only
  - [ ] Egress: Default allow (oder restrictive nach Bedarf)

- [ ] **IAM Rollen & Policies**
  - [ ] ECS Task Execution Role (inkl. CloudWatch Logs, ECR access)
  - [ ] S3 access für Frontend Bucket
  - [ ] RDS access secrets (Secret Manager Integration)
  - [ ] CloudWatch Metrics & Logs permissions

**Output:** Dokumentation mit ARNs, IDs, Security Group Rules

---

### 2.2 Checkliste: RDS Setup (PostgreSQL)

- [ ] **Datenbank-Instance**
  - [ ] Engine: PostgreSQL 14+
  - [ ] Instance type: db.t3.small (oder größer für Prod)
  - [ ] Multi-AZ: JA (für High Availability)
  - [ ] Storage: 100 GB (gp3), Auto-scaling enabled
  - [ ] Deleted protection: JA
  - [ ] Backup retention: 30 Tage

- [ ] **Parameter Group & Options**
  - [ ] `max_connections` = 100 (ggf. mehr)
  - [ ] `shared_preload_libraries` = 'pg_stat_statements' (für Monitoring)
  - [ ] Enhanced monitoring enabled

- [ ] **Zugriff & Secrets**
  - [ ] Admin-Password generiert (32 Bytes, sicher)
  - [ ] In AWS Secrets Manager gespeichert (Secret-Name: `prod/db/password`)
  - [ ] Endpoint dokumentiert (z. B. `prod-db.cxxxxxx.eu-central-1.rds.amazonaws.com`)

- [ ] **Backup & Restore Test**
  - [ ] Automated backups enabled
  - [ ] Manual snapshot erstellt & dokumentiert
  - [ ] Restore-Test durchgeführt (Snapshot → neue DB → verify connectivity)

**Output:** RDS Endpoint, Security Group ID, Secret ARN

---

### 2.3 Checkliste: Docker Registry Setup

Wenn Docker verwendet wird:

- [ ] **Repo für container images**
  - [ ] ECR (AWS), GCR (GCP), ACR (Azure) oder Docker Hub
  - [ ] Repository erstellt: `lifetimecircle-api`, `lifetimecircle-web`
  - [ ] Image tagging strategy: `rc-2026-03-01`, `latest`, `staging`
  - [ ] Lifecycle policy: alte Images nach 30 Tagen löschen

- [ ] **IAM access für Builds**
  - [ ] CI/CD-User hat `push` Permissions
  - [ ] Prod-Server hat `pull` Permissions

**Output:** Registry URLs, Access Credentials dokumentiert

---

### 2.4 Checkliste: TLS & Domain

- [ ] **Domain kaufen / aktivieren**
  - [ ] Domain registriert: z. B. `lifetimecircle.de`
  - [ ] Registrar zugänglich (z. B. Namecheap, Route53)
  - [ ] Nameserver aktualisiert (falls nötig)

- [ ] **SSL/TLS-Zertifikat**
  - [ ] Let's Encrypt Certificate erstellt (ACM wenn AWS)
  - [ ] For domains: `app.lifetimecircle.de` + `www.`, ggf. `api.`
  - [ ] Auto-renewal konfiguriert (ACM macht das auto)
  - [ ] Zertifikat in ALB / CDN konfiguriert

- [ ] **DNS Records**
  - [ ] A Record: `app.lifetimecircle.de` → ALB IP / CloudFront
  - [ ] CNAME: `www.lifetimecircle.de` → ALB (optional)
  - [ ] Ggf. `api.lifetimecircle.de` → API Endpoint
  - [ ] SPF, DKIM für Email (wenn Mail-Versand)

- [ ] **Redirect-Regeln**
  - [ ] HTTP → HTTPS (ALB Target Group Rule)
  - [ ] HTTP Status Code: 301 Permanent Redirect
  - [ ] Test: `curl -L http://app.lifetimecircle.de` → redirects zu HTTPS

**Output:** Domain, TLS Cert ARN, DNS Records dokumentiert

---

## Phase 3: Deployment-Pipeline vorbereiten (Tag 3)

### 3.1 Build & Push Pipeline

Erstelle Deployment-Skript (Pseudo-Code):

```bash
#!/bin/bash
# deploy.sh – Build, Push, Deploy

set -e

# 1. Code auschecken
git checkout rc-2026-03-01

# 2. Secrets laden
export LTC_SECRET_KEY=$(aws secretsmanager get-secret-value --secret-id prod/LTC_SECRET_KEY --query SecretString --output text)
export DATABASE_URL=$(aws secretsmanager get-secret-value --secret-id prod/DATABASE_URL --query SecretString --output text)

# 3. Build Backend
cd server
poetry install --no-dev
poetry build  # oder Docker build

# 4. Build Frontend
cd ../packages/web
npm ci
npm run build

# 5. Push zu Registry
aws ecr get-login-password --region eu-central-1 | docker login --username AWS --password-stdin 123456789.dkr.ecr.eu-central-1.amazonaws.com
docker build -t lifetimecircle-api:rc-2026-03-01 -f server/Dockerfile .
docker tag lifetimecircle-api:rc-2026-03-01 123456789.dkr.ecr.eu-central-1.amazonaws.com/lifetimecircle-api:rc-2026-03-01
docker push 123456789.dkr.ecr.eu-central-1.amazonaws.com/lifetimecircle-api:rc-2026-03-01

# 6. Deploy zu Staging
aws ecs update-service --cluster staging --service api --force-new-deployment

# 7. Verify
sleep 30
curl -X GET https://staging.lifetimecircle.de/api/health

echo "✅ Deployed!"
```

**Zu delegieren:** 
- [ ] Deployment-Skript ins Repo (`tools/deploy_prod.sh`)
- [ ] In CI/CD Pipeline (GitHub Actions) integrieren

---

### 3.2 CI/CD Integration (GitHub Actions)

Erstelle `.github/workflows/deploy-prod.yml`:

```yaml
name: Deploy Production

on:
  workflow_dispatch:
  push:
    tags:
      - 'prod-*'

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Deploy to Production
        env:
          AWS_ACCESS_KEY_ID: ${{ secrets.AWS_ACCESS_KEY_ID }}
          AWS_SECRET_ACCESS_KEY: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          AWS_REGION: eu-central-1
        run: |
          bash ./tools/deploy_prod.sh
      
      - name: Smoke Test
        run: |
          curl -X GET https://app.lifetimecircle.de/api/health
```

---

## Phase 4: Dokumentation & Handoff (Tag 4)

### 4.1 Infrastructure-As-Code (IaC) – Option

Falls Zeit: Terraform/CloudFormation Templates:

```hcl
# main.tf (Terraform)
resource "aws_rds_instance" "prod" {
  identifier = "lifetimecircle-prod"
  engine     = "postgres"
  instance_class = "db.t3.small"
  allocated_storage = 100
  # ...
}

resource "aws_ecs_cluster" "prod" {
  name = "lifetimecircle-prod"
}

resource "aws_ecs_service" "api" {
  name = "api"
  cluster = aws_ecs_cluster.prod.name
  # ...
}
```

---

### 4.2 Dokumentation für SRE/Ops

Erstelle `docs/INFRASTRUCTURE_PROD.md` mit:

- [ ] **Architektur-Diagram** (VPC, VPC-Layout, Security Groups)
- [ ] **Wichtige IDs & Endpoints**
  ```
  VPC: vpc-xxxxx
  ALB: arn:aws:elasticloadbalancing:...
  RDS Endpoint: prod-db.cxxxxxx.eu-central-1.rds.amazonaws.com
  API Container: 123456789.dkr.ecr.eu-central-1.amazonaws.com/lifetimecircle-api:rc-2026-03-01
  Frontend Bucket: s3://lifetimecircle-frontend-prod
  Frontend CDN: d123abc.cloudfront.net
  ```

- [ ] **Scaling Policy** (wenn ECS/K8s)
  - Min replicas: 2
  - Max replicas: 10
  - Scale-up trigger: CPU > 70%
  - Scale-down trigger: CPU < 30%

- [ ] **Disaster Recovery Plan**
  - RTO: Recovery Time Objective (target: < 1h)
  - RPO: Recovery Point Objective (target: < 15 min)
  - Backup location: S3 cross-region

---

## Checklist: Was muss SRE-Lead / Security-Lead wissen?

Nach DevOps-Provisioning informieren:

- [ ] **SRE-Lead:**
  - RDS Endpoint & Connection String
  - API Container Endpoint
  - Frontend CDN URL
  - Monitoring-Hook Informationen (CloudWatch, Logs)

- [ ] **Security-Lead:**
  - RDS Admin Password (in Secrets Manager)
  - `LTC_SECRET_KEY` generierter Wert (in Secrets Manager)
  - Security Group IDs (für Audit)
  - IAM Role ARNs (für KMS Access, falls needed)

---

## Deadline & Output

**Deadline:** **2026-03-03 EOD**

**Deliverables:**
- [ ] Entscheidungsmatrix ausgefüllt
- [ ] VPC, Subnets, Security Groups → dokumentiert
- [ ] RDS PostgreSQL → online & getestet
- [ ] Docker Registry → ready
- [ ] Domain & TLS → konfiguriert
- [ ] Deploy-Skript → in Repo
- [ ] `docs/INFRASTRUCTURE_PROD.md` → erstellt
- [ ] Handoff-Mail an SRE/Security mit allen IDs

---

**Wenn fertig → Inform SRE-Lead, Security-Lead können starten!** ✅
