# Patent Platform Phase 0 MVP - Development & Deployment Guide

## Overview

This guide covers setting up, developing, testing, and deploying the Patent Lifecycle Platform Phase 0 MVP.

**Target**: US and Indian mechanical patent markets, 100 early-access users within 6 months, 10+ patents filed.

---

## Local Development Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL 15 (or use Docker)
- Git

### Quick Start with Docker Compose

```bash
# Clone repository
git clone <repo>
cd project

# Start all services (PostgreSQL, Redis, Backend, Frontend)
docker-compose up --build

# Backend API: http://localhost:8000
# Frontend: http://localhost:3000
# Docs: http://localhost:8000/docs
```

### Manual Local Setup

#### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql+asyncpg://user:password@localhost/patent_db"
export REDIS_URL="redis://localhost:6379/0"
export ENVIRONMENT="development"

# Run migrations
alembic upgrade head

# Seed materials database (5,000 materials)
python -m backend.app.database.patent_seed

# Start server
uvicorn backend.app.main:app --reload --port 8000
```

#### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Set environment variables
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# Start dev server
npm run dev

# Open http://localhost:3000
```

---

## Architecture Overview

### Backend Stack
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Cache**: Redis for sessions and rate limiting
- **Async**: asyncpg, aiosqlite for database operations
- **Task Queue**: Kafka (deferred to Phase 1B)

### Frontend Stack
- **Framework**: Next.js with React 18
- **Styling**: Tailwind CSS
- **State**: React hooks with fetch API
- **Testing**: Jest + React Testing Library

### Database Schema

**Patents Table**
```sql
- id (UUID, PK)
- title, abstract, technical_field
- status (DRAFT, READY_FOR_FILING, FILED, REJECTED, ABANDONED)
- patent_type (UTILITY, PROVISIONAL, DESIGN)
- embodiments (JSON array)
- claims_summary, detailed_description
- jurisdictions (JSON: [USPTO, INDIAN_IPO])
- fea_file_id, fea_file_name (optional for Phase 1B)
- uspto_application_number, indian_ipo_application_number
- created_at, updated_at, filed_at
- tenant_id (for multi-tenancy stub)
```

**Materials Table**
```sql
- id (UUID, PK)
- name (unique), material_type
- density, youngs_modulus, tensile_strength
- yield_strength, elongation_at_break
- corrosion_resistance, temperature_range_min/max
- corrosion_potential, corrosion_current_density
- source, source_url, datasheet_url
```

**Patent Audit Logs Table**
```sql
- id (UUID, PK)
- patent_id (FK)
- action (CREATED, UPDATED, FILED, etc.)
- actor (user email)
- details (JSON)
- timestamp
- tenant_id (for multi-tenancy stub)
```

---

## API Endpoints

### Patent Creation & Management

```bash
# Create draft patent
POST /patents/create
{
  "title": "Novel Method...",
  "abstract": "A method...",
  "technical_field": "Materials Science"
}

# Get patent details
GET /patents/{patent_id}

# Add embodiments
POST /patents/{patent_id}/embodiments
{ "embodiments": ["Embodiment 1", "Embodiment 2"] }

# Set claims summary
POST /patents/{patent_id}/claims
{ "claims_summary": "A method comprising..." }

# List patents
GET /patents?status=DRAFT&limit=50&offset=0
```

### Patent Filing

```bash
# Generate filing preview
POST /patents/{patent_id}/filing-preview?jurisdiction=USPTO&applicant_name="John Doe"

# Submit for filing (generates XML)
POST /patents/{patent_id}/submit-for-filing
{
  "jurisdiction": "USPTO",
  "applicant_name": "John Doe",
  "applicant_address": "123 Main St",
  "applicant_city": "San Francisco",
  "applicant_state": "CA",
  "applicant_zip": "94105"
}

# Mark as filed (after USPTO/IPO submission)
POST /patents/{patent_id}/mark-as-filed
{
  "jurisdiction": "USPTO",
  "application_number": "US2026123456"
}

# Get patent status
GET /patents/{patent_id}/status

# Get audit trail
GET /patents/{patent_id}/audit-trail
```

### Materials Database

```bash
# Look up material by name
GET /patents/materials/lookup?name="Steel 304"

# List materials by type
GET /patents/materials/by-type/metal?limit=50
```

---

## Testing

### Unit Tests

```bash
# Run USPTO XML generation tests
pytest backend/tests/unit/test_patent_filing.py -v

# Test with coverage
pytest backend/tests/unit/ --cov=backend.app.services
```

### Integration Tests

```bash
# Run patent workflow tests
pytest backend/tests/integration/test_patent_workflow.py -v

# All integration tests
pytest backend/tests/integration/ -v
```

### Manual Testing (Postman/cURL)

```bash
# Create patent
curl -X POST http://localhost:8000/patents/create \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Novel Coating Method",
    "abstract": "A method for applying protective coatings",
    "technical_field": "Materials Science"
  }'

# Response: { "id": "...", "status": "DRAFT", ...}

# Get patent
curl http://localhost:8000/patents/{patent_id}

# Submit for filing
curl -X POST http://localhost:8000/patents/{patent_id}/submit-for-filing \
  -H "Content-Type: application/json" \
  -d '{
    "jurisdiction": "USPTO",
    "applicant_name": "John Doe",
    "applicant_address": "123 Main St",
    "applicant_city": "San Francisco",
    "applicant_state": "CA",
    "applicant_zip": "94105"
  }'
```

---

## USPTO XML Generation

The platform generates USPTO EFS-Web XML for mechanical patents. Key features:

- **Form**: SN2019-01 (Utility Patent Application)
- **Filing Fee**: $330 USD (subject to change)
- **Claims**: Automatic generation of 1 independent claim + dependent claims per embodiment
- **Scope**: Mechanical patents only (Phase 0)

### Example XML Structure

```xml
<patent-application-publication>
  <filings>
    <filing>
      <filing-type>UTILITY</filing-type>
      <form-type>SN2019-01</form-type>
      <filing-fee-paid>330.0</filing-fee-paid>
    </filing>
  </filings>
  <bibliographic-data>
    <invention-title>Novel Method...</invention-title>
    <abstract>A method...</abstract>
    <claims>
      <claim id="CLM-0001" num="1" claim-type="independent">
        <claim-text>1. A method for... comprising...</claim-text>
      </claim>
      <claim id="CLM-0002" num="2" claim-type="dependent" depends-on="1">
        <claim-text>2. The method of claim 1, wherein...</claim-text>
      </claim>
    </claims>
  </bibliographic-data>
</patent-application-publication>
```

---

## Production Deployment

### AWS Infrastructure (Single Region - us-east-1)

#### 1. Database (RDS)
```bash
# RDS PostgreSQL 15
- Instance: db.t3.medium (2 vCPU, 4 GB RAM)
- Multi-AZ: Enabled
- Backup: 30-day retention, daily snapshots
- Encryption: AES-256 at rest
- Cost: ~$150/month
```

#### 2. Application Server (ECS/Fargate)
```bash
# Fargate container service
- Image: Patent API Docker image
- CPU: 0.5 vCPU
- Memory: 1 GB
- Replicas: 2 (auto-scaling 1-5 based on load)
- Cost: ~$100/month
```

#### 3. Cache (ElastiCache)
```bash
# Redis cluster
- Node type: cache.t3.micro
- Multi-AZ: Enabled
- Cost: ~$30/month
```

#### 4. Load Balancer (ALB)
```bash
# Application Load Balancer
- Health check: /health every 30s
- TLS termination: 1.3
- Cost: ~$20/month
```

#### 5. Storage (S3)
```bash
# For FEA file uploads (Phase 1B)
- Server-side encryption: AES-256
- Versioning: Enabled
- Cost: ~$1/month (for MVP scale)
```

#### 6. Monitoring (CloudWatch + Prometheus)
```bash
- Logs: All API requests, errors, audit trail
- Metrics: P99 latency, error rate, database connections
- Alerts: >3% error rate, latency >500ms, disk >80%
```

### Terraform Infrastructure as Code

See `terraform/` directory for IaC templates:
- `main.tf` - VPC, subnets, security groups
- `rds.tf` - PostgreSQL database
- `ecs.tf` - Fargate container service
- `alb.tf` - Load balancer
- `variables.tf` - Environment configuration

Deploy with:
```bash
cd terraform
terraform init
terraform plan -var-file=prod.tfvars
terraform apply -var-file=prod.tfvars
```

### Deployment Pipeline (GitHub Actions)

See `.github/workflows/deploy.yml`:

```yaml
# Trigger on push to main
- Build Docker image
- Run tests
- Push to ECR
- Update ECS task definition
- Deploy to Fargate
- Run smoke tests
- Notify team on Slack
```

### Manual Deployment

```bash
# 1. Build Docker image
docker build -t patent-api:latest -f Dockerfile.backend .

# 2. Push to ECR
aws ecr get-login-password | docker login --username AWS --password-stdin $ECR_URI
docker tag patent-api:latest $ECR_URI/patent-api:latest
docker push $ECR_URI/patent-api:latest

# 3. Update ECS task definition
aws ecs update-service \
  --cluster patent-cluster \
  --service patent-api \
  --force-new-deployment

# 4. Monitor deployment
aws ecs describe-services --cluster patent-cluster --services patent-api
```

---

## Security & Compliance (MVP Phase 0)

### Data Protection
- ✅ Encryption at rest: AES-256 (PostgreSQL, S3)
- ✅ Encryption in transit: TLS 1.3
- ✅ Audit logging: All patent actions logged immutably
- ✅ Access control: JWT tokens, role-based access (future)

### SOC 2 Type I Readiness Checklist
- ✅ Documented security policies
- ✅ Audit trail for all data modifications
- ✅ Encryption at rest and in transit
- ✅ Access control mechanisms
- ✅ Change management procedures
- ✅ Incident response plan (documented)
- ⏳ External audit (not required for MVP)

### Compliance (Phase 0 → Phase 1)
- **Phase 0**: Basic security, audit logging, SOC 2 readiness
- **Phase 1A**: GDPR compliance, data residency rules
- **Phase 2**: SOC 2 Type II audit (18-month observation period)
- **Phase 3**: ISO 27001 certification

---

## Performance Targets

### MVP Phase 0 Targets
- **P95 Latency**: <500ms (local region)
- **P99 Latency**: <1000ms
- **Error Rate**: <1% (>99% uptime)
- **Throughput**: 100 requests/second
- **Database**: Single RDS instance (sufficient for MVP)
- **Availability**: 99% (48 minutes downtime/month acceptable)

### Monitoring & Alerting
```bash
# Use CloudWatch dashboards to track:
- API latency (p50, p95, p99)
- Error rate by endpoint
- Database connection pool usage
- Cache hit rate
- Patent creation rate
- Filing success rate
```

---

## Next Steps (Phase 0 → Phase 1A)

### Immediate (Months 1-3)
1. Deploy MVP to AWS with multi-AZ RDS
2. Onboard 20-30 beta users
3. Collect feedback on filing workflow
4. Begin patent attorney partnerships
5. Start provisional patent filing (2-3 internal patents)

### Short Term (Months 3-6)
1. Scale to 100 users
2. File 10 mechanical patents (5 US, 5 India)
3. Iterate based on user feedback
4. Prepare Series A fundraising materials
5. Validate market demand & unit economics

### Medium Term (Months 6-12, Phase 1A)
1. Add European Patent Office support
2. Live simulation integration planning
3. Multi-jurisdiction claim generation
4. Enterprise feature planning (API access, team management)

---

## Troubleshooting

### Database Connection Issues
```bash
# Check PostgreSQL
psql postgresql://user:password@localhost/patent_db -c "SELECT 1"

# Check in Docker
docker-compose logs postgres

# Reset database
docker-compose down -v
docker-compose up
```

### API Not Responding
```bash
# Check backend logs
docker-compose logs backend

# Test health check
curl http://localhost:8000/health

# View FastAPI docs
curl http://localhost:8000/docs
```

### Frontend Connection to API
```bash
# Check NEXT_PUBLIC_API_URL
echo $NEXT_PUBLIC_API_URL

# Check CORS headers
curl -i http://localhost:8000/patents
```

---

## Support & Questions

For issues, please create a GitHub issue with:
- Error message and traceback
- Steps to reproduce
- Environment (Docker/manual setup)
- Expected vs. actual behavior

---

**Last Updated**: 2026-04-09  
**Maintainers**: Patent Platform Team  
**Phase**: 0 (MVP)
