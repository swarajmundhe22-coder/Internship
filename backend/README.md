# The On Looker Backend

Starter FastAPI backend for the GIFIP-aligned predictive infrastructure intelligence platform.

## Structure

- `app/models`: Pydantic contracts for materials, environment, simulation, and reports.
- `app/algorithms`: Scientific algorithm modules (risk scoring, electrochemistry, degradation, lifespan, risk class, recommendations).
- `app/services`: Orchestration layer coordinating algorithms and future repositories.
- `app/api`: Versioned FastAPI routes.
- `app/database`: SQLAlchemy setup and ORM entities.
- `database/schema.sql`: PostgreSQL DDL with constraints and indexes.

## Run

```bash
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Migrations

```bash
alembic -c alembic.ini upgrade head
```

### Rollback Runbook (Release)

Use this minimal sequence when a production release must be rolled back.

```bash
# 1) Check current revision
alembic -c alembic.ini current

# 2) Roll back one migration step
alembic -c alembic.ini downgrade -1

# 3) Verify current revision after rollback
alembic -c alembic.ini current

# 4) Optional: show all known revision heads/history for audit notes
alembic -c alembic.ini heads
alembic -c alembic.ini history -v
```

## Seed Data

- Baseline materials and environment profiles are loaded idempotently at startup.
- Automatic startup initialization can be toggled with `AUTO_INITIALIZE_DB`.

## Test

```bash
pytest
```

## Infrastructure Validation (ASCE/Eurocode/GB + Microclimate)

- New infrastructure endpoints (included in Swagger/OpenAPI):
	- `POST /api/v1/infrastructure/validate`
	- `POST /api/v1/infrastructure/validate/pdf`
	- `POST /api/v1/infrastructure/hourly-update`

- Standards and checks covered:
	- ASCE 7-22 load envelope with Chapters 26-31 wind handling
	- Eurocode ULS/SLS combinations (EN 1990/1991/1993/1998) with India NA factors
	- GB 50009-2012, GB 50011-2010, GB 50017-2017 combinations
	- Limit-state pass/fail plus margin-of-safety per combination

- Microclimate coverage:
	- Wind speed 0-200 mph in 1 mph increments with ASCE exposure-based height adjustment
	- Seismic zones 0-8 with Ss/S1 spectral proxies
	- Precipitation intensity 1-1000 mm/hr and 100-year IDF values
	- Freeze-thaw cycles, salt-spray intensity, SO2 deposition, and pressure (850-1100 hPa)
	- Interpolation audit trail and nearest-validated-station fallback

- Coverage and range gate:

```bash
python scripts/validate_infrastructure_parameter_coverage.py --strict
```

- Hourly update pipeline:

```bash
python scripts/run_hourly_microclimate_update.py
```

- Demo for Miami (US) and Chennai (IN):

```bash
python scripts/infrastructure_demo_miami_chennai.py
```

## Calibration Validation Reports

- Run structured multi-scenario calibration validation:

```bash
python scripts/generate_calibration_report.py
```

- Output artifacts are written to `artifacts/calibration_reports` as both `.json` and `.md`.
- Use strict mode to fail CI when any scenario is out of calibration envelope:

```bash
python scripts/generate_calibration_report.py --strict
```

## Production Readiness Gates (Phase 9)

The backend now includes executable gates for model governance, security, reliability, and operations.

See the consolidated release checklist in [docs/production_readiness_checklist.md](docs/production_readiness_checklist.md).

### External Field Validation

- Holdout benchmark validation with global and region targets:

```bash
python scripts/run_field_validation.py --dataset docs/field_validation_benchmark.csv --strict
```

- Threshold config:
	- `docs/field_validation_targets.json`
- Reports:
	- `artifacts/field_validation/*.json`
	- `artifacts/field_validation/*.md`

### Model Drift Detection

```bash
python scripts/check_model_drift.py --strict
```

- Baseline reference:
	- `docs/model_drift_baseline.json`
- Reports:
	- `artifacts/model_drift/*.json`
	- `artifacts/model_drift/*.md`

### Security Gates

```bash
python scripts/security_dast_gate.py --base-url http://127.0.0.1:8000/api/v1 --strict
```

### Performance and Reliability Gates

```bash
python scripts/performance_reliability_gate.py --base-url http://127.0.0.1:8000/api/v1 --strict
python scripts/monitor_p99_latency.py --base-url http://127.0.0.1:8000/api/v1 --strict
python scripts/failure_mode_chaos_gate.py --base-url http://127.0.0.1:8000/api/v1 --strict
python scripts/e2e_regression_suite.py --base-url http://127.0.0.1:8000/api/v1 --strict
python scripts/profile_simulation_endpoint.py --base-url http://127.0.0.1:8000/api/v1
python scripts/sustained_p99_analyzer.py --base-url http://127.0.0.1:8000/api/v1 --strict
python scripts/load_resilience_10x.py --base-url http://127.0.0.1:8000/api/v1 --concurrency 4000 --total-requests 12000 --p99-budget-ms 100 --strict
```

- Runtime telemetry endpoint (RBAC-protected):
	- `GET /api/v1/ops/performance`
	- Optional query params: `path`, `include_paths`, `top`

- Prometheus scrape endpoint:
	- `GET /api/v1/ops/metrics/prometheus`
	- Intended for internal scrape only.

### Tiered P99 Program (Low/Medium/High)

- Tier policy defaults:
	- Low (1x baseline QPS): p99 <= 100 ms
	- Medium (3x baseline QPS): p99 <= 150 ms
	- High (5x baseline QPS): p99 <= 200 ms
	- Spike ceiling: no p99 spikes > 250 ms in sustained runs

- Run tiered sustained analyzer:

```bash
python scripts/sustained_p99_analyzer.py \
  --base-url http://127.0.0.1:8000/api/v1 \
  --baseline-qps 20 \
  --duration-seconds 1800 \
  --chaos-fault-rate 0.01 \
  --strict
```

- Enforce candidate regression gate (<5% vs baseline):

```bash
python scripts/assert_p99_regression.py \
  --baseline docs/performance_baseline_reference.json \
  --candidate artifacts/performance_reports/sustained_p99_analysis_<timestamp>.json \
  --max-regression-pct 5
```

### Gatling 7-Day Traffic Replay

- Gatling suite location:
	- `performance/gatling/src/test/scala/onlookers/SustainedLatencySimulation.scala`

- Runner script (creates token, executes low/medium/high tiers, emits artifact):

```bash
python scripts/run_gatling_latency_suite.py \
  --base-url http://127.0.0.1:8000/api/v1 \
  --duration-minutes 60 \
  --chaos-rate 0.01
```

### Deploy/Observability Assets

- Kubernetes deployment + service:
	- `deploy/k8s/backend-deployment.yaml`
- HPA policy (CPU 60%, memory 70%, 10-200 replicas, 30s scale-up window):
	- `deploy/k8s/backend-hpa.yaml`
- Prometheus alerts:
	- `deploy/observability/prometheus-alert-rules.yaml`
- Grafana dashboard JSON:
	- `deploy/observability/grafana-p99-dashboard.json`

### Backup and Restore Drill

```bash
python scripts/backup_restore_drill.py --strict
```

### Runbooks

- `docs/model_risk_controls.md`
- `docs/security_compliance_runbook.md`
- `docs/performance_reliability_runbook.md`
- `docs/performance_optimization_strategy.md`
- `docs/p99_engineering_report.md`
- `docs/performance_sla_benchmarks.md`
- `docs/ops_sre_readiness_runbook.md`
- `docs/production_readiness_checklist.md`
- `docs/google_oauth_configuration_requirements.md`
- `docs/google_oauth_configuration_record_template.md`
- `docs/google_oauth_verification_evidence_template.md`

### OAuth Operations

- Diagnose Google OAuth configuration and callback readiness:

```bash
python scripts/diagnose_google_oauth.py --base-url http://127.0.0.1:8000/api/v1 --strict
```

- Monitor authentication login success SLO (target 99.9%):

```bash
python scripts/auth_login_slo_monitor.py --window-hours 24 --target-success-rate-pct 99.9 --strict
```

## Pagination And Filtering

- List endpoints return paginated responses with:
	- `items`, `total`, `page`, `page_size`
- Query params:
	- `page`, `page_size` on all list endpoints
	- `material_id`, `environment_id`, `risk_level`, `created_from`, `created_to` on `/simulation`
	- `simulation_id`, `created_from`, `created_to` on `/reports`

## Optimistic Locking

- `simulation` and `reports` updates use optimistic locking via `version`.
- Update payloads for `/simulation/{id}` and `/reports/{id}` must include `expected_version`.
- If `expected_version` is stale, API returns `409 Conflict`.

## CI

- Pull requests run backend CI in GitHub Actions:
	- Install dependencies
	- `alembic upgrade head`
	- `pytest -q`

## Enterprise Auth Hardening (Phase 5)

- JWT auth now returns both access and refresh tokens.
- New auth session endpoints:
	- `POST /api/v1/auth/refresh`
	- `POST /api/v1/auth/logout`
- Role-aware enforcement is applied across API routes with `admin`, `engineer`, and `viewer` policies.
- Refresh sessions are persisted and rotated to support secure session lifecycle control.
- Auth audit events are persisted for register/login/refresh/logout success and failure flows.
- Admin audit inspection endpoint:
	- `GET /api/v1/audit-logs`
	- filters: `event_type`, `user_id`, `user_email`, `created_from`, `created_to`, `page`, `page_size`

## SMTP And OTP Setup

OTP for registration and optional login second-factor is SMTP-backed.

1. Copy env template:

```bash
copy .env.example .env
```

2. Set SMTP values in `.env`:

```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-smtp-username
SMTP_PASSWORD=your-smtp-password-or-app-password
SMTP_FROM_EMAIL=you@yourdomain.com
SMTP_USE_TLS=true
OTP_ADMIN_NOTIFICATION_EMAIL=security@yourdomain.com
```

3. OTP tuning values:

```bash
REGISTRATION_OTP_EXPIRE_MINUTES=10
REGISTRATION_OTP_MAX_ATTEMPTS=5
LOGIN_OTP_EXPIRE_MINUTES=5
```

4. OTP endpoints:

- Registration OTP gate:
	- `POST /api/v1/auth/register/request-otp`
	- `POST /api/v1/auth/register/verify-otp`
- Optional login OTP second factor:
	- `POST /api/v1/auth/login/request-otp`
	- `POST /api/v1/auth/login/verify-otp`

5. Quick verify with curl:

```bash
BASE_URL="http://127.0.0.1:8000"

curl -X POST "$BASE_URL/api/v1/auth/register/request-otp" \
  -H "Content-Type: application/json" \
  -d '{"email":"otp-user@example.com","password":"StrongPass123"}'

curl -X POST "$BASE_URL/api/v1/auth/login/request-otp" \
  -H "Content-Type: application/json" \
  -d '{"email":"otp-user@example.com","password":"StrongPass123"}'
```

Notes:

- In `production`, missing SMTP config blocks OTP delivery.
- In non-production, missing SMTP falls back to dev OTP in API response for local testing.

## Analytics Endpoints

- `GET /api/v1/analytics/summary`
- `GET /api/v1/analytics/material-usage`
- `GET /api/v1/analytics/environment-usage`
- `GET /api/v1/analytics/risk-distribution`
- `GET /api/v1/analytics/simulations-over-time`
- Indexes support analytics-heavy dimensions (`simulation.created_at`, `reports.status`, `project_simulations.created_at`).

## Report Reliability Hardening

- Report payload generation uses in-memory TTL caching to reduce repeated heavy joins for repeated simulation requests.
- New PDF export endpoint: `GET /api/v1/reports/{report_id}/pdf`.
- PDF generation includes retry attempts for transient rendering failures.

## Notes

- Current scientific algorithms are production-structured placeholders with validated formulas for future calibration.
- Integrate migrations (Alembic), repositories, and test suites in next iteration.

## Project Workspaces

- Projects use the `project_simulations` join table to attach existing simulations to one or more projects.
- Endpoints:
	- `GET /api/v1/projects/{project_id}` returns project metadata and paginated simulation summaries (`material`, `environment`, `risk_level`, `lifespan_years`, `created_at`).
	- `GET /api/v1/projects/{project_id}/reports` returns project-scoped report summaries with pagination and filters (`simulation_id`, `risk_level`, `created_from`, `created_to`).
	- `POST /api/v1/projects/{project_id}/simulations/{simulation_id}` attaches an existing simulation.
	- `POST /api/v1/projects/{project_id}/simulations` supports body-based attachment with `{ "simulation_id": "..." }`.

## Comparison Sets

- Comparison sets let teams persist 2-4 project simulations for reusable engineering comparison workflows.
- Endpoints:
	- `POST /api/v1/projects/{project_id}/comparison-sets` create a set with `name` and `simulation_ids`.
	- `GET /api/v1/projects/{project_id}/comparison-sets` list project sets.
	- `GET /api/v1/comparison-sets/{comparison_set_id}` return full set detail and compare-ready payload.
	- `PATCH /api/v1/comparison-sets/{comparison_set_id}` update name and/or simulation list.
	- `DELETE /api/v1/comparison-sets/{comparison_set_id}` remove a set.
- Validation:
	- Each set must contain 2-4 unique simulations.
	- All simulations in the set must already belong to the target project.

## Phase 6 Predictive Modeling Engine

- Project-scoped predictive intelligence endpoints:
	- `POST /api/v1/projects/{project_id}/predict`
	- `GET /api/v1/projects/{project_id}/predictions`
- Predictive runs persist forecast metadata and timeline frames in `project_predictions`.
- Forecast timeline includes per-step:
	- `offset_hours`
	- `corrosion_rate_mm_per_year`
	- `estimated_lifespan_years`
	- `risk_score`
	- `risk_classification`
- Prediction listing supports pagination and filters:
	- `page`, `page_size`, `simulation_id`, `created_from`, `created_to`
- Prediction generation enforces project ownership and requires the simulation to belong to the project.

## Phase 6 AI Insights Layer

- New AI insights endpoints:
	- `GET /api/v1/projects/{project_id}/insights`
	- `GET /api/v1/projects/{project_id}/insights/report`
- Insights include:
	- AI risk summary
	- recommendation list
	- anomaly detection payloads
- Insights report export returns a text artifact suitable for attaching into governance report workflows.

## Phase 6 Enterprise Integration

- Predictive export endpoint:
	- `GET /api/v1/projects/{project_id}/predictions/export?format=csv|xlsx`
- External API token management endpoints:
	- `POST /api/v1/integrations/api-tokens`
	- `GET /api/v1/integrations/api-tokens`
	- `DELETE /api/v1/integrations/api-tokens/{token_id}`
- Webhook management for report completion events:
	- `POST /api/v1/integrations/webhooks`
	- `GET /api/v1/integrations/webhooks`
	- `DELETE /api/v1/integrations/webhooks/{webhook_id}`
	- report create/update with status `generated|completed` emits `report.completed`
- SSO exchange endpoint:
	- `POST /api/v1/auth/sso/exchange`
	- validates allowed email domains through `sso_allowed_domains` config

## Phase 7 Master Implementation

### NVIDIA Copilot (OpenAI-Compatible API)

- Endpoints:
	- `POST /api/v1/copilot/query` (scientific reasoning) model: `nvidia/llama-3.1-nemotron-ultra-253b-v1`
	- `POST /api/v1/copilot/doc` (document intelligence) model: `nvidia/llama-3.1-nemotron-nano-vl-8b-v1`
	- `POST /api/v1/copilot/search` (retrieval QA) model: `nvidia/nv-embedqa-e5-v5`
- Security:
	- role-gated to `admin` and `engineer`
- Config:
	- `NVIDIA_API_KEY`
	- when missing, APIs return deterministic fallback guidance instead of crashing startup

### 10-Minute Onboarding Runbook

- Import Postman collection:
	- `docs/postman/phase7_quickstart.postman_collection.json`
- Run requests in order (`1` to `19`) to cover:
	- auth bootstrap (admin + engineer)
	- tenant CRUD and membership
	- copilot query/doc/search
	- tenant auto-binding via simulation + project create
	- billing webhook event + audit verification

Quick curl fallback (bash-compatible):

```bash
BASE_URL="http://127.0.0.1:8000"
PASSWORD="StrongPass123"
ADMIN_EMAIL="phase7-admin@example.com"
ENGINEER_EMAIL="phase7-engineer@example.com"

ADMIN_TOKEN=$(curl -s -X POST "$BASE_URL/api/v1/auth/register" -H "Content-Type: application/json" \
	-d "{\"email\":\"$ADMIN_EMAIL\",\"password\":\"$PASSWORD\",\"role\":\"admin\"}" | jq -r '.access_token')

ENGINEER_REGISTER=$(curl -s -X POST "$BASE_URL/api/v1/auth/register" -H "Content-Type: application/json" \
	-d "{\"email\":\"$ENGINEER_EMAIL\",\"password\":\"$PASSWORD\",\"role\":\"engineer\"}")
ENGINEER_TOKEN=$(echo "$ENGINEER_REGISTER" | jq -r '.access_token')
ENGINEER_USER_ID=$(python - <<'PY'
import base64, json, os
token = os.environ["ENGINEER_TOKEN"]
payload = token.split(".")[1] + "=" * (-len(token.split(".")[1]) % 4)
print(json.loads(base64.urlsafe_b64decode(payload.encode()).decode())["sub"])
PY
)

TENANT_ID=$(curl -s -X POST "$BASE_URL/api/v1/tenants" -H "Content-Type: application/json" \
	-H "Authorization: Bearer $ADMIN_TOKEN" \
	-d '{"org_name":"Phase7 Quickstart Org","subscription_tier":"professional"}' | jq -r '.id')

curl -s -X POST "$BASE_URL/api/v1/tenants/$TENANT_ID/users" -H "Content-Type: application/json" \
	-H "Authorization: Bearer $ADMIN_TOKEN" \
	-d "{\"user_id\":\"$ENGINEER_USER_ID\",\"role\":\"admin\"}" >/dev/null

curl -s -X POST "$BASE_URL/api/v1/copilot/query" -H "Content-Type: application/json" \
	-H "Authorization: Bearer $ENGINEER_TOKEN" \
	-d '{"user_input":"Summarize corrosion risk under marine chloride exposure."}' | jq .

curl -s -X POST "$BASE_URL/api/v1/copilot/doc" -H "Content-Type: application/json" \
	-H "Authorization: Bearer $ENGINEER_TOKEN" \
	-d '{"user_input":"Extract maintenance actions from coating delamination notes."}' | jq .

curl -s -X POST "$BASE_URL/api/v1/copilot/search" -H "Content-Type: application/json" \
	-H "Authorization: Bearer $ENGINEER_TOKEN" \
	-d '{"user_input":"Find similar pitting cases with humidity over 80 percent."}' | jq .

MATERIAL_ID=$(curl -s -X POST "$BASE_URL/api/v1/materials" -H "Content-Type: application/json" \
	-H "Authorization: Bearer $ENGINEER_TOKEN" \
	-d '{"name":"Phase7 Material","alloy_group":"Ferrous","density_kg_m3":7850.0,"electrochemical_potential_v":-0.61}' | jq -r '.id')

ENVIRONMENT_ID=$(curl -s -X POST "$BASE_URL/api/v1/environment" -H "Content-Type: application/json" \
	-H "Authorization: Bearer $ENGINEER_TOKEN" \
	-d '{"profile_name":"Phase7 Marine Profile","temperature_c":24.0,"relative_humidity_pct":82.0,"chloride_ppm":12000.0,"ph":7.2,"dissolved_oxygen_mg_l":7.0}' | jq -r '.id')

SIMULATION_ID=$(curl -s -X POST "$BASE_URL/api/v1/simulation" -H "Content-Type: application/json" \
	-H "Authorization: Bearer $ENGINEER_TOKEN" \
	-d "{\"material_id\":\"$MATERIAL_ID\",\"environment_id\":\"$ENVIRONMENT_ID\",\"exposed_area_m2\":11.0,\"exposure_time_hours\":850.0,\"corrosion_rate_mm_per_year\":0.09,\"estimated_lifespan_years\":12.5,\"risk_classification\":\"moderate\"}" | jq -r '.id')

PROJECT_ID=$(curl -s -X POST "$BASE_URL/api/v1/projects" -H "Content-Type: application/json" \
	-H "Authorization: Bearer $ENGINEER_TOKEN" \
	-d '{"name":"Phase7 Tenant Project"}' | jq -r '.id')

PAYLOAD='{"event_type":"BILLING.SUBSCRIPTION.ACTIVATED","resource":{"custom_id":"'"$TENANT_ID"'","subscription_tier":"enterprise_elite"}}'
SIGNATURE=$(python - <<'PY'
import hashlib, hmac, os
secret = os.getenv("PAYPAL_WEBHOOK_SECRET", "")
payload = os.environ["PAYLOAD"]
print(hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest() if secret else "")
PY
)

curl -s -X POST "$BASE_URL/api/v1/billing/webhook" -H "Content-Type: application/json" \
	-H "X-PayPal-Signature: $SIGNATURE" -d "$PAYLOAD" | jq .

curl -s "$BASE_URL/api/v1/audit-logs?page=1&page_size=50&event_type=billing.paypal.billing.subscription.activated" \
	-H "Authorization: Bearer $ADMIN_TOKEN" | jq .

echo "Done. tenant=$TENANT_ID simulation=$SIMULATION_ID project=$PROJECT_ID"
```

### PayPal Billing + Tenant Subscription Lifecycle

- Endpoint:
	- `POST /api/v1/billing/webhook`
- Signature verification:
	- validates `X-PayPal-Signature` using HMAC and `PAYPAL_WEBHOOK_SECRET` (fallback: `PAYPAL_SECRET`)
- Supported event matrix:
	- `BILLING.SUBSCRIPTION.CREATED`
	- `BILLING.SUBSCRIPTION.UPDATED`
	- `BILLING.SUBSCRIPTION.SUSPENDED`
	- `BILLING.SUBSCRIPTION.ACTIVATED`
	- `BILLING.SUBSCRIPTION.CANCELLED`
- Tenant state transitions:
	- tier: `free | professional | enterprise_elite`
	- status: `active | suspended | canceled`
- Audit trail:
	- signature failures and all processed billing events are written to audit logs

### Multi-Tenant Architecture

- Core tables:
	- `tenants`
	- `tenant_users`
	- `tenant_simulations`
- Project tenant boundary:
	- `projects.tenant_id` enforces tenant-aware ownership context
- Admin tenant management endpoints:
	- `GET /api/v1/tenants`
	- `POST /api/v1/tenants`
	- `GET /api/v1/tenants/{tenant_id}`
	- `PATCH /api/v1/tenants/{tenant_id}`
	- `DELETE /api/v1/tenants/{tenant_id}`
	- `GET /api/v1/tenants/{tenant_id}/users`
	- `POST /api/v1/tenants/{tenant_id}/users`
	- `DELETE /api/v1/tenants/{tenant_id}/users/{user_id}`

### Automatic Tenant Binding

- Simulation creation flow auto-links new simulations to the user's primary tenant membership.
- Project creation flow auto-assigns `tenant_id` from the user's primary tenant membership.

### UI/UX Baseline (Frontend)

- Frontend stack in this workspace: Next.js + TailwindCSS + Three.js.
- Existing enterprise surfaces already support admin integrations and cinematic comparison overlays.

## Phase 8 Immersive Visualization And Digital Twins

### Backend Endpoints

- `POST /api/v1/visualization/twin`
	- generates tenant-scoped digital twin metadata bound to a simulation
	- enforces simulation-to-tenant binding and tenant membership checks
- `POST /api/v1/visualization/playback`
	- returns AR/VR-ready timeline overlays with playback HUD payloads
	- supports `mode`: `twin`, `ar`, `vr`
- `POST /api/v1/visualization/export`
	- creates investor-ready export records (`pdf` or `mp4`)
	- writes audit trail events as `visualization.export`

### Simulation Binding

- Simulation create flow now auto-generates a twin visualization record.
- Auto-generation is tenant-aware when a simulation is bound through tenant membership.

### Data Model Additions

- `visualizations`
	- simulation linkage, tenant isolation key, mode, metadata, overlay accuracy, status
- `visualization_exports`
	- visualization linkage, tenant scope, file type and file URI for cinematic artifacts

### Accuracy Enforcement

- Mission playback and export enforce predictive overlay accuracy threshold of at least `0.95`.

### Frontend Mission Control

- Mission control page: `/visualization/mission-control`
- Includes:
	- Babylon.js digital twin stage with glow-coded hotspots
	- timeline slider for cinematic foresight playback
	- WebXR session orchestration controls for AR/VR readiness
	- investor showcase export controls

### Postman Quickstart

- `docs/postman/phase8_visualization_quickstart.postman_collection.json`

### Device Certification Runbook

- `docs/phase8_device_certification_runbook.md`
	- physical validation checklist for Oculus/Meta Quest, HoloLens, and desktop browser fallback

### Phase 8 Smoke Test (Release Gating)

Run the full mission-control flow in one command:

```bash
python scripts/phase8_smoke_test.py --base-url http://127.0.0.1:8000/api/v1
```

What it validates:

- admin + engineer registration
- tenant create + membership bind
- simulation creation with accuracy score
- digital twin generation
- AR/VR playback preparation
- investor export (`mp4`)
- audit-log verification for `visualization.export`
