# Performance Optimization Strategy (P99 Readiness)

This document records the optimization and reliability strategy used to enforce the backend latency target: p99 <= `SIMULATION_SLO_P99_MS`.

## 1. Request-Path Optimization

Implemented changes:

- Replaced per-request logger filter injection with context-local correlation IDs.
- Prevented logging handler duplication by making logging setup idempotent.
- Switched request timing to `time.perf_counter()` for stable high-resolution latency measurement.

Why it matters:

- Avoids unbounded logger filter growth over uptime.
- Reduces per-request middleware overhead.
- Produces more accurate latency telemetry for p95/p99 calculations.

## 2. Runtime P99 Telemetry

Implemented changes:

- Added a rolling in-memory performance monitor in `app/core/performance.py`.
- Captures request latency and status across a configurable sliding window.
- Computes p50/p95/p99, 5xx error rate, SLO checks, and alert states.
- Exposes telemetry through RBAC-protected endpoint: `GET /api/v1/ops/performance`.

Why it matters:

- Enables continuous in-process latency tracking.
- Aligns runtime signal with release gates and on-call dashboards.
- Provides path-level drill-down for top slow endpoints.

## 3. Alerting and Monitoring Automation

Implemented changes:

- Added `scripts/monitor_p99_latency.py`.
- Script runs synthetic simulation traffic, polls `/ops/performance`, and fails in strict mode on SLO breach.

Alert states tracked:

- `critical_latency_p99`
- `warning_latency_p95`
- `critical_api_5xx_spike`
- `warning_error_budget_burn`

## 4. Profiling for Bottleneck Discovery

Implemented changes:

- Added `scripts/profile_simulation_endpoint.py` using `cProfile`/`pstats`.
- Emits `.prof`, text, and JSON artifacts under `artifacts/performance_reports`.

Why it matters:

- Supports repeatable bottleneck analysis against real endpoint paths.
- Makes optimization work evidence-based before and after code changes.

## 5. Test and Regression Enforcement

Implemented changes:

- Unit tests: `tests/unit/test_performance_monitor.py`
- Integration tests: `tests/integration/test_ops_performance_endpoint.py`
- E2E middleware observability test: `tests/e2e/test_runtime_middleware_observability.py`
- Added release E2E script: `scripts/e2e_regression_suite.py`

Coverage goals:

- Validate telemetry math and alert behavior.
- Validate RBAC and response shape for ops monitoring endpoint.
- Validate middleware headers and runtime telemetry recording.
- Validate critical production workflows and latency guardrails in one strict suite.

## 6. CI/CD Enforcement

Production-readiness CI now runs:

- `scripts/performance_reliability_gate.py --strict`
- `scripts/monitor_p99_latency.py --strict`
- `scripts/e2e_regression_suite.py --strict`
- `scripts/failure_mode_chaos_gate.py --strict`
- `scripts/profile_simulation_endpoint.py`

This ensures p99 tracking, regression protection, and profiling evidence are required for release.

## 7. Validation Procedure

Recommended release validation sequence:

1. Run unit and integration tests (`pytest -q`).
2. Start API and run performance + chaos gates.
3. Run runtime P99 monitor in strict mode.
4. Run E2E regression suite in strict mode.
5. Generate and review simulation profiling artifacts.
6. Archive artifacts in release evidence bundle.
