# Performance and Reliability Runbook

This runbook defines sustained-load and failure-mode validation expected before release.

## Staging Parity Requirement

All performance and reliability gates must run against a staging environment that matches production for:

- application version,
- database engine and schema,
- network policy,
- CPU/memory limits,
- external dependency mocks or mirrors.

## Sustained-Load Gate

Command:

```bash
python scripts/performance_reliability_gate.py --strict
```

Checks:

- p95 and p99 latency budgets.
- error budget rate.
- controlled behavior for unauthorized and malformed requests.
- runtime telemetry parity by verifying `/api/v1/ops/performance` P95/P99/error budgets.

## Runtime P99 Monitoring

Command:

```bash
python scripts/monitor_p99_latency.py --base-url http://127.0.0.1:8000/api/v1 --strict
```

Checks:

- live runtime telemetry exists and includes enough samples,
- runtime p99 remains within SLO budget,
- runtime 5xx error rate remains inside error budget,
- critical p99 alert state is not active.

## Tiered Sustained P99 Program

Use the tiered analyzer to validate low/medium/high traffic tiers against explicit p99 and spike ceilings.

Command:

```bash
python scripts/sustained_p99_analyzer.py \
	--base-url http://127.0.0.1:8000/api/v1 \
	--baseline-qps 20 \
	--duration-seconds 1800 \
	--chaos-fault-rate 0.01 \
	--strict
```

Policy:

- low (1x) p99 <= 100 ms,
- medium (3x) p99 <= 150 ms,
- high (5x) p99 <= 200 ms,
- zero spikes above 250 ms.

Regression guardrail command (candidate must not regress more than 5%):

```bash
python scripts/assert_p99_regression.py \
	--baseline docs/performance_baseline_reference.json \
	--candidate artifacts/performance_reports/sustained_p99_analysis_<timestamp>.json \
	--max-regression-pct 5
```

Long-horizon replay command (Gatling runner):

```bash
python scripts/run_gatling_latency_suite.py \
	--base-url http://127.0.0.1:8000/api/v1 \
	--duration-minutes 60 \
	--chaos-rate 0.01
```

10x concurrency resilience scenario (4,000+ concurrent requests):

```bash
python scripts/load_resilience_10x.py \
	--base-url http://127.0.0.1:8000/api/v1 \
	--concurrency 4000 \
	--total-requests 12000 \
	--p99-budget-ms 100 \
	--strict
```

## End-to-End Regression Suite

Command:

```bash
python scripts/e2e_regression_suite.py --base-url http://127.0.0.1:8000/api/v1 --strict
```

Checks:

- core auth/material/environment/simulation/report workflows remain functional,
- optimistic locking and OAuth failure classification regressions are guarded,
- runtime `/ops/performance` telemetry aligns with latency and error budgets.

## Performance Profiling

Command:

```bash
python scripts/profile_simulation_endpoint.py --base-url http://127.0.0.1:8000/api/v1
```

Profiling artifacts:

- `artifacts/performance_reports/simulation_profile_*.prof`
- `artifacts/performance_reports/simulation_profile_*.txt`
- `artifacts/performance_reports/simulation_profile_*.json`

## Dashboards and Alert Sources

- Runtime diagnostic API: `GET /api/v1/ops/performance`
- Prometheus scrape endpoint: `GET /api/v1/ops/metrics/prometheus`
- Prometheus alert rules: `deploy/observability/prometheus-alert-rules.yaml`
- Grafana dashboard: `deploy/observability/grafana-p99-dashboard.json`
- HPA policy: `deploy/k8s/backend-hpa.yaml`

Key Prometheus thresholds for `/simulation/simulate`:

- warning if p99 > 110 ms for 5m (low-tier +10%),
- warning if p99 > 165 ms for 5m (medium-tier +10%),
- critical if p99 > 220 ms for 5m (high-tier +10%).

## Canary and Rollback Procedure

Canary rollout:

1. Deploy with `AUDIT_ASYNC_ENABLED=false` and capture baseline tiered artifact.
2. Enable `AUDIT_ASYNC_ENABLED=true` for canary pods only.
3. Expand canary traffic 10% -> 25% -> 50% -> 100% only if no tier breach and no error-budget burn warning.
4. Run sustained analyzer and regression assertion at each promotion stage.

Rollback trigger:

- p99 degradation > 10% versus approved baseline for 10 consecutive minutes, or
- any tier SLA/spike failure in sustained analyzer.

Rollback actions:

1. Set `AUDIT_ASYNC_ENABLED=false`.
2. Set `KAFKA_ASYNC_BATCHING_ENABLED=false`.
3. Roll deployment back to prior release image.
4. Re-run sustained analyzer and regression assertion before re-promoting.

## Emergency Tuning Knobs

Use these in incident mitigation (small deltas, one change set at a time):

- DB pool capacity/timeouts:
	- `DB_POOL_SIZE`, `DB_POOL_MAX_OVERFLOW`, `DB_POOL_TIMEOUT_SECONDS`
- DB connection lifecycle/leak visibility:
	- `DB_POOL_MAX_LIFETIME_SECONDS`, `DB_POOL_LEAK_DETECTION_THRESHOLD_SECONDS`
- Cache behavior:
	- `REDIS_URL`, `REDIS_READTHROUGH_HARD_TTL_SECONDS`, `REDIS_READTHROUGH_REFRESH_TTL_MS`
- Audit throughput path:
	- `AUDIT_ASYNC_ENABLED`, `AUDIT_BATCH_QUEUE_SIZE`
- Kafka batching:
	- `KAFKA_ASYNC_BATCHING_ENABLED`, `KAFKA_BATCH_SIZE_BYTES`, `KAFKA_LINGER_MS`
- Tiered SLO thresholds:
	- `SIMULATION_SLO_LOW_LOAD_P99_MS`, `SIMULATION_SLO_MEDIUM_LOAD_P99_MS`, `SIMULATION_SLO_HIGH_LOAD_P99_MS`, `SIMULATION_SLO_SPIKE_CEILING_MS`

## Failure-Mode and Chaos Gate

Command:

```bash
python scripts/failure_mode_chaos_gate.py --strict
```

Checks:

- no unexpected 5xx responses during valid and malformed request bursts,
- unauthorized and invalid-token paths reject correctly,
- malformed and negative-value payloads fail with controlled validation responses.

## Release Criteria

A release candidate is eligible only when all are true:

- sustained-load gate passes,
- runtime p99 monitor passes,
- tiered sustained analyzer passes,
- p99 regression assertion (<5%) passes,
- chaos/failure-mode gate passes,
- end-to-end regression suite passes,
- no unresolved P0/P1 reliability issues,
- latest backup drill passed in last 30 days,
- engineering evidence report is updated (`docs/p99_engineering_report.md`).

## Regression Handling

If any gate fails:

1. block release branch promotion,
2. open reliability incident with owner,
3. attach report artifacts from `artifacts/performance_reports` and `artifacts/chaos_reports`,
4. inspect latest profile summary for top cumulative functions and remediation candidates,
5. if degradation exceeds 10%, execute rollback procedure before retry,
6. rerun gates only after fix merge.
