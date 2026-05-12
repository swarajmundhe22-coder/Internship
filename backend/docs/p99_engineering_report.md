# Tiered P99 Engineering Report

## 1. Objective and Acceptance Criteria

This report documents the P99 latency optimization initiative for sustained traffic tiers and links each requirement to executable evidence.

Tiered SLO policy:

- Low tier (1x baseline QPS): p99 <= 100 ms
- Medium tier (3x baseline QPS): p99 <= 150 ms
- High tier (5x baseline QPS): p99 <= 200 ms
- Spike ceiling: 0 spikes above 250 ms during sustained tests

## 2. Evidence Bundle

Primary sustained-load artifacts:

- Pre-optimization/failing snapshot: `artifacts/performance_reports/sustained_p99_analysis_20260404_104821Z.json`
- Pre-optimization/failing markdown: `artifacts/performance_reports/sustained_p99_analysis_20260404_104821Z.md`
- Post-optimization/passing snapshot: `artifacts/performance_reports/sustained_p99_analysis_20260404_105231Z.json`
- Post-optimization/passing markdown: `artifacts/performance_reports/sustained_p99_analysis_20260404_105231Z.md`

Profiling evidence for bottleneck review:

- Profile summary JSON: `artifacts/performance_reports/simulation_profile_20260404_105636Z.json`
- Profile text: `artifacts/performance_reports/simulation_profile_20260404_105636Z.txt`
- Profile binary (flamegraph-compatible input): `artifacts/performance_reports/simulation_profile_20260404_105636Z.prof`

## 3. Pre-Optimization Heatmap (Failing)

Source: `sustained_p99_analysis_20260404_104821Z.json`.

| Tier | Endpoint | P99 (ms) | SLA (ms) | Spikes > 250 ms | Status |
|---|---|---:|---:|---:|---|
| low | simulate_post | 223.06 | 100 | 0 | FAIL |
| low | auth_login_post | 359.64 | 100 | 3 | FAIL |
| medium | simulate_post | 25249.17 | 150 | 272 | FAIL |
| medium | auth_login_post | 19385.83 | 150 | 58 | FAIL |
| medium | ops_performance_get | 23761.53 | 150 | 53 | FAIL |
| high | simulate_post | 1260.90 | 200 | 50 | FAIL |
| high | auth_login_post | 3248.04 | 200 | 21 | FAIL |
| high | ops_performance_get | 282.76 | 200 | 1 | FAIL |

Additional pre-optimization signals:

- Event-loop lag: p95 3367.28 ms, p99 3903.97 ms, max 4067.44 ms.
- DB pool churn/leak stress: 25.72 checkouts/sec, 9 leak alerts, max hold 6.28 sec.
- Cache effectiveness: 0.0 hit rate for report cache namespace in the sampled window.

## 4. Bottleneck Analysis and Root-Cause Findings

Primary bottlenecks detected by sustained analyzer and ops snapshot:

- Thread starvation or event-loop lag under concurrent sustained load.
- Cache misses (read-through cache did not materially engage in the failing run).
- Connection churn and long-hold outliers in DB pool behavior during saturation windows.

Profiler evidence (cumulative top frames) from `simulation_profile_20260404_105636Z.txt`:

- Async runtime scheduling and Windows completion polling dominate cumulative time under synthetic load.
- HTTP client setup and SSL context setup appear prominently in short-run test overhead.
- Workload summary stayed healthy in this profile sample (p99 114.50 ms, 0% 5xx).

Flamegraph workflow:

- Use `.prof` artifact with Snakeviz or gprof2dot to generate a visual flamegraph for incident review and change PR evidence.

## 5. Optimization Package Implemented

The following controls were implemented and integrated into runtime/CI:

- DB pool tuning and telemetry: pool size/overflow/timeout/lifetime controls and checkout hold/leak instrumentation.
- Read-through caching: Redis-compatible cache layer with fallback and telemetry snapshots.
- Async audit write path: queue-based audit persistence with optional Kafka batching and controlled fallback.
- Prometheus latency metrics: request histogram and request counters exposed for internal scraping.
- Tiered sustained analyzer: low/medium/high run orchestration with SLA and spike checks.
- Regression enforcement: candidate-vs-baseline P99 guardrail with max regression threshold.
- Resilience controller: request shedding + circuit breaker protection for latency-critical paths.
- Autoscaling and observability assets: HPA policy plus alert rules and Grafana dashboard JSON.

## 6. Canary Rollout Plan

Feature-flag rollout sequence:

1. Stage 0 (0%): deploy with `AUDIT_ASYNC_ENABLED=false`, collect baseline analyzer artifacts.
2. Stage 1 (10%): enable `AUDIT_ASYNC_ENABLED=true` for canary pool only.
3. Stage 2 (25%): if no tier breach and no burn-rate alert for 30 minutes, expand to 25%.
4. Stage 3 (50%): validate sustained analyzer and runtime telemetry trends.
5. Stage 4 (100%): full rollout only after regression checker and chaos gate pass.

Canary promotion gates:

- No tier SLA violation in sustained analyzer.
- No spikes > 250 ms in any tier endpoint.
- No critical p99 alert and no rapid error-budget burn.

## 7. Post-Optimization Results (Passing)

Source: `sustained_p99_analysis_20260404_105231Z.json` (run with async audit batching enabled).

| Tier | Endpoint | P99 (ms) | SLA (ms) | Spikes > 250 ms | Status |
|---|---|---:|---:|---:|---|
| low | simulate_post | 35.49 | 100 | 0 | PASS |
| low | auth_login_post | 50.62 | 100 | 0 | PASS |
| medium | simulate_post | 24.02 | 150 | 0 | PASS |
| medium | auth_login_post | 59.25 | 150 | 0 | PASS |
| medium | ops_performance_get | 14.09 | 150 | 0 | PASS |
| high | simulate_post | 75.25 | 200 | 0 | PASS |
| high | auth_login_post | 112.84 | 200 | 0 | PASS |
| high | ops_performance_get | 28.02 | 200 | 0 | PASS |

Post-optimization ops snapshot highlights:

- Window p99: 96.58 ms
- 5xx rate: 0.0
- DB leak alerts: 0
- DB max hold: 0.25 sec
- Audit batch enabled and stable: 412 enqueued / 412 persisted / 0 dropped

## 8. Rollback Plan and Trigger

Immediate rollback trigger:

- Any key endpoint p99 degrades by more than 10% versus latest approved baseline for 10 continuous minutes, or
- Any tiered analyzer run fails SLA or spike ceiling.

Rollback sequence:

1. Disable async audit path:
   - `AUDIT_ASYNC_ENABLED=false`
   - `KAFKA_ASYNC_BATCHING_ENABLED=false`
2. Revert to previous release image/tag.
3. Temporarily tighten ingress to stable replica set while HPA re-stabilizes.
4. Re-run:
   - `python scripts/sustained_p99_analyzer.py ... --strict`
   - `python scripts/assert_p99_regression.py ... --max-regression-pct 5`
5. Keep rollback in place until p99 and error budget return to green and root cause is documented.

## 9. On-Call Operating Guide

Dashboards and alerts to watch first:

- Prometheus alert rules: `deploy/observability/prometheus-alert-rules.yaml`
- Grafana dashboard: `deploy/observability/grafana-p99-dashboard.json`
- Runtime diagnostics API: `GET /api/v1/ops/performance`
- Prometheus scrape endpoint: `GET /api/v1/ops/metrics/prometheus`

Emergency tuning knobs:

- `DB_POOL_SIZE`, `DB_POOL_MAX_OVERFLOW`, `DB_POOL_TIMEOUT_SECONDS`
- `DB_POOL_MAX_LIFETIME_SECONDS`, `DB_POOL_LEAK_DETECTION_THRESHOLD_SECONDS`
- `REDIS_URL`, `REDIS_READTHROUGH_HARD_TTL_SECONDS`, `REDIS_READTHROUGH_REFRESH_TTL_MS`
- `AUDIT_ASYNC_ENABLED`, `AUDIT_BATCH_QUEUE_SIZE`
- `KAFKA_ASYNC_BATCHING_ENABLED`, `KAFKA_BATCH_SIZE_BYTES`, `KAFKA_LINGER_MS`
- `SIMULATION_SLO_LOW_LOAD_P99_MS`, `SIMULATION_SLO_MEDIUM_LOAD_P99_MS`, `SIMULATION_SLO_HIGH_LOAD_P99_MS`, `SIMULATION_SLO_SPIKE_CEILING_MS`

## 10. Requirement Traceability

| Requirement | Status | Evidence |
|---|---|---|
| Tiered sustained P99 SLOs and spike ceiling | Implemented and validated in latest local run | `sustained_p99_analysis_20260404_105231Z.json` |
| Bottleneck classification | Implemented with analyzer heuristics + ops telemetry | `sustained_p99_analysis_20260404_104821Z.json` |
| Pool/cache/batching optimization controls | Implemented | `app/core/config.py`, `app/database/session.py`, `app/core/readthrough_cache.py`, `app/core/audit_batch_processor.py` |
| Prometheus/Grafana/alerts and HPA assets | Implemented | `deploy/observability/*`, `deploy/k8s/backend-hpa.yaml` |
| Circuit breaker and overload shedding | Implemented | `app/core/resilience.py`, `app/main.py` |
| CI regression enforcement (<5%) | Implemented | `.github/workflows/backend-ci.yml`, `scripts/assert_p99_regression.py` |
| 10x (4,000+ concurrency) load scenario harness | Implemented | `scripts/load_resilience_10x.py` |
| Engineering report + rollback/canary guidance | Implemented | This document and `docs/performance_reliability_runbook.md` |

## 11. Remaining Work for Release Sign-Off

- Execute full-duration release-profile sustained tests (for example 60 minutes per tier) at production-equivalent baseline QPS.
- Run and archive the Gatling sustained replay job in CI (`gatling-replay`) for the release branch.
- Attach generated artifacts to the release evidence bundle and obtain SRE sign-off.
