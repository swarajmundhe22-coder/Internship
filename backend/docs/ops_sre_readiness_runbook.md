# Ops and SRE Readiness Runbook

This runbook defines SLOs, alerting, dashboard requirements, and operational drill procedures for production operation of the backend API.

## Service Level Objectives

Primary service: `POST /api/v1/simulation/simulate`

- Availability SLO: >= 99.9% monthly successful responses (`2xx|4xx` except auth abuse).
- Latency SLO p95: <= 1200 ms.
- Latency SLO p99: <= 2000 ms.
- Error budget SLO: <= 2.0% 5xx error rate over rolling 30 days.

Authentication service objective:

- Login success SLO: >= 99.9% over rolling 30 days for auth login events (`auth.login`, `auth.login.otp.verify`, `auth.sso.exchange`, `auth.oauth.callback`).

Configuration source:

- `SIMULATION_SLO_P95_MS`
- `SIMULATION_SLO_P99_MS`
- `SIMULATION_ERROR_BUDGET_RATE`

Authentication SLO monitoring command:

```bash
python scripts/auth_login_slo_monitor.py --window-hours 24 --target-success-rate-pct 99.9 --strict
```

Runtime latency telemetry monitoring command:

```bash
python scripts/monitor_p99_latency.py --base-url http://127.0.0.1:8000/api/v1 --p99-budget-ms 2000 --error-budget-rate 0.02 --strict
```

Live telemetry API:

- `GET /api/v1/ops/performance`
  - Optional filters: `path`, `include_paths`, `top`
  - Access: `admin`, `engineer`

## Alerting Policy

Alert windows should be evaluated over both 5-minute and 30-minute windows.

- `critical-api-5xx-spike`
  - Trigger: `5xx_rate > 5%` for 5 minutes.
  - Action: page on-call engineer immediately.
- `warning-latency-p95`
  - Trigger: `p95 > SIMULATION_SLO_P95_MS` for 15 minutes.
  - Action: create high-priority incident and assign service owner.
- `critical-latency-p99`
  - Trigger: `p99 > SIMULATION_SLO_P99_MS` for 10 minutes.
  - Action: page on-call and activate incident commander.
- `warning-error-budget-burn`
  - Trigger: burn rate projects monthly error budget exhaustion within 7 days.
  - Action: freeze non-essential deployments and open mitigation plan.

## Dashboard Requirements

Minimum production dashboard panels:

- Request throughput by endpoint (`/health`, `/simulation/simulate`, `/reports/*`).
- p50, p95, p99 latency for `simulation/simulate`.
- Runtime `/ops/performance` check statuses and alert flags.
- 4xx and 5xx rate with top error families.
- Database connection pool utilization and query duration percentiles.
- Queue lag and ingest backlog (if Kafka/MQTT enabled).
- Calibration confidence and fallback rate trends.
- Drift gate status and last successful validation timestamp.

## Backup and Restore Drill

Run at least weekly in staging and monthly in production shadow mode.

Command:

```bash
python scripts/backup_restore_drill.py --strict
```

Expected behavior:

- SQLite environments: creates backup copy and validates restore with integrity query.
- PostgreSQL environments: creates schema-only `pg_dump` artifact.

Evidence to retain:

- Drill timestamp.
- Command output.
- Artifact path in `artifacts/backup_drills`.
- Operator and reviewer sign-off.

## Incident Response Runbook

### Severity Levels

- `SEV-1`: customer-impacting outage, security breach, or sustained data corruption risk.
- `SEV-2`: major feature degradation with mitigation path.
- `SEV-3`: localized issue with acceptable workaround.

### First 15 Minutes

1. Acknowledge alert and assign incident commander.
2. Confirm blast radius (tenants, regions, endpoints, data paths).
3. Decide containment action (rollback, feature flag disable, traffic shedding).
4. Post first status update to incident channel and stakeholder list.

### Mitigation and Recovery

1. Stabilize service and restore SLO trend.
2. Validate data integrity and audit logs.
3. Resume normal traffic in controlled stages.
4. Publish closure note with customer impact window.

### Post-Incident Requirements

- Postmortem due in 48 hours.
- Root cause and contributing factors documented.
- Corrective actions with owners and target dates.
- Runbook updates merged before next release cycle.
