# Real-Time Developer Accuracy and Reliability Assessment

Date: 2026-04-03
Scope: Production-oriented assessment of API/model behavior for real-time developer workflows.
System: The On Looker API and simulation/twin/export pipeline.

## 1. Assessment Method

This assessment combines six evidence streams:

1. Calibration validation outputs
2. Holdout field validation outputs
3. Drift monitoring outputs
4. Sustained-load reliability gate outputs (multiple load tiers)
5. Failure-mode chaos gate outputs (burst malformed/valid traffic)
6. End-to-end workflow smoke and timed workflow benchmark runs

The intent is to measure both model correctness and operational behavior under developer-realistic usage.

## 2. Measurable Metrics and Definitions

### 2.1 Prediction Accuracy Metrics

1. Calibration pass rate: fraction of canonical calibration scenarios passing acceptance checks
2. Risk score MAE: mean absolute error between expected and predicted risk score
3. Design-rate MAPE: mean absolute percentage error of design corrosion rate
4. Lifespan MAPE: mean absolute percentage error of estimated lifespan
5. Interval coverage: fraction of records where true values lie in model uncertainty intervals
6. Drift ratio: relative drift versus baseline calibration for global and regional aggregates

### 2.2 Reliability and Real-Time Metrics

1. p95 latency and p99 latency for sustained simulation traffic
2. Error rate under sustained load
3. Unexpected 5xx frequency during failure-mode scenarios
4. Valid burst success rate during concurrent request spikes
5. Malformed burst controlled-rejection rate (expected validation failure)
6. End-to-end workflow step latency for real developer paths (auth, tenant, simulation, twin, playback, export, audit)

### 2.3 Security/Correctness Metrics

1. Authz enforcement for protected simulation route
2. Payload validation enforcement for malformed simulation requests
3. Security header checks on health endpoint

## 3. Test Scenarios (Real Developer Workflow Simulation)

### Scenario A: Baseline Real-Time Workflow

Flow:

1. Register admin and engineer users
2. Create tenant and bind engineer
3. Create material and environment
4. Run simulation
5. Generate digital twin
6. Prepare playback
7. Export artifact
8. Verify audit event

Evidence:

- Smoke workflow pass confirmed on latest run
- Timed workflow benchmark executed for 3 full runs

### Scenario B: Sustained Simulation Load

Three request volumes evaluated:

1. 120 total requests
2. 360 total requests
3. 720 total requests

Gate budgets used by implementation:

- p95 <= 1200 ms
- p99 <= 2000 ms
- error_rate <= 0.02

### Scenario C: Failure-Mode and Edge-Case Burst

Cases exercised:

1. Unauthorized request
2. Invalid token
3. Negative-value malformed request
4. High-volume valid burst
5. High-volume malformed burst

### Scenario D: Security DAST Gate

Checks exercised:

1. Health endpoint availability
2. Security headers
3. Auth required on simulation endpoint
4. Payload validation behavior
5. Authenticated simulation success

### Scenario E: Predictive Correctness and Drift

1. Calibration scenario sweep (8 scenarios)
2. Holdout field validation by region (7 rows)
3. Drift comparison against baseline thresholds

## 4. Measured Results

## 4.1 Accuracy Results

Calibration aggregate:

- scenarios: 8
- pass rate: 100%
- model version: global-calibrated-v1.1.0
- average risk score: 60.87
- average design corrosion rate: 0.42744 mm/year
- average lifespan: 52.151 years

Field validation holdout (7 rows):

- risk_score_mae: approximately 2.18e-14
- design_rate_mape: approximately 1.06e-15
- lifespan_mape: approximately 6.21e-16
- interval_coverage: 1.0
- fallback_rate: 0.0
- status: PASS

Drift report:

- global drift metrics all 0.0 relative drift, PASS
- regional drift metrics all 0.0 relative drift, PASS

## 4.2 Real-Time Reliability and Latency Results

Sustained-load gate:

- Tier 1 (120 req): PASS
  - p95 813.79 ms, p99 1314.94 ms, error_rate 0.0
- Tier 2 (360 req): FAIL latency budget
  - p95 1730.35 ms, p99 3200.10 ms, error_rate 0.0
- Tier 3 (720 req): FAIL latency budget
  - p95 1908.36 ms, p99 3377.02 ms, error_rate 0.0

Interpretation:

- Reliability is strong in terms of correctness and absence of request failures (error_rate remains zero).
- The current bottleneck is latency scaling under medium and high concurrency.

Failure-mode chaos gate (largest run):

- total_samples: 403
- unexpected_5xx: 0
- valid_success_rate: 1.0
- malformed_safe_rate: 1.0
- overall: PASS

Security DAST gate:

- all checks PASS
- auth and validation behavior consistent

Timed full workflow benchmark (3 end-to-end runs):

- workflow_total avg: 402.29 ms
- workflow_total p50: 429.99 ms
- workflow_total max: 459.10 ms
- largest average step costs:
  - register engineer: 64.87 ms
  - prepare playback: 55.20 ms
  - register admin: 50.94 ms
  - export artifact: 44.88 ms
  - create simulation: 40.41 ms

## 5. Expected vs Actual Discrepancies

## 5.1 Discrepancy 1: Latency Budget Breach at Higher Load

Expected:

- p95 <= 1200 ms and p99 <= 2000 ms at production-like sustained concurrency

Actual:

- 360 and 720 request tiers breach both latency budgets while maintaining 0% error

Impact:

- Real-time developer experience degrades (slow responses) before outright failures occur.

## 5.2 Discrepancy 2: MP4 Export Artifact Mode in Current Environment

Expected:

- Binary MP4 video rendering for export requests

Observed implementation behavior:

- Renderer falls back to JSON payload when ffmpeg is unavailable

Impact:

- Functional pipeline continuity is preserved, but media realism and downstream player compatibility expectations may differ in environments lacking ffmpeg.

## 5.3 Discrepancy 3: Near-Perfect Holdout Errors

Expected:

- Holdout metrics should generally show small but non-zero residual error

Actual:

- Holdout metrics are effectively zero (machine precision)

Impact:

- Strong pass status is useful, but this pattern can indicate an overly easy benchmark split or overlap with calibration structure; additional external and temporally shifted datasets are recommended before final production confidence statements.

## 6. Failure Modes and Edge Cases Identified

1. Throughput-latency collapse mode:
   - Under increased load, latency budgets fail while success rate remains high.
2. External tool dependency mode:
   - ffmpeg absence causes export fallback artifact behavior.
3. DB toolchain dependency mode:
   - PostgreSQL backup drill requires pg_dump in runtime environment.
4. Confidence fallback mode:
   - Simulation service has conservative fallback logic when confidence drops below threshold.
5. Tenant-access/auth edge cases:
   - Correctly rejected in current tests (401/403 and 422 paths).

## 7. Reliability Rating for Real-Time Developer Use

Current rating:

- Accuracy: High
- Functional reliability: High
- Security control behavior: High
- Real-time performance under low load: Acceptable
- Real-time performance under medium/high sustained load: Needs improvement before broad production rollout

Overall production readiness statement:

- Suitable for controlled production traffic and canary usage.
- Not yet sufficient for higher sustained concurrent traffic if strict latency SLOs must be maintained.

## 8. Recommendations (Prioritized)

P0 (Immediate)

1. Add horizontal worker scaling and isolate simulation compute path from request thread pool.
2. Add queue-backed async processing for expensive operations where synchronous response is not required.
3. Add p95/p99 per-route telemetry and percentile alarms by endpoint class.
4. Enforce ffmpeg runtime dependency in production image and add startup health check for renderer capabilities.

P1 (Near term)

1. Introduce cache layers for static calibration packs, material profiles, and region-resolution lookups.
2. Add bulkhead/timeouts around visualization export path to protect simulation latency.
3. Run load tests with realistic mixed route distributions, not only simulation endpoint.
4. Execute nightly strict gates and track trend lines (not one-off snapshots).

P2 (Validation hardening)

1. Expand holdout dataset with unseen external observations and temporal holdout windows.
2. Add adversarial data tests (distribution shifts, sparse sensors, contradictory signals).
3. Add fairness/regional robustness checks and confidence calibration drift audits.

## 9. Action Plan for Production Real-Time Developers

1. Keep current latency budgets as hard release gates.
2. Require PASS for 120/360/720 tiers before general availability.
3. Add canary ramp policy with automatic rollback on p95/p99 regressions.
4. Require ffmpeg, pg_dump, and observability dependencies in deployment baseline.
5. Revalidate against expanded external benchmark before final broad release.

## 10. Evidence Sources Used

1. Calibration reports in artifacts/calibration_reports
2. Field validation reports in artifacts/field_validation
3. Drift reports in artifacts/model_drift
4. Performance gate reports in artifacts/performance_reports
5. Chaos reports in artifacts/chaos_reports
6. Security reports in artifacts/security_reports
7. Smoke test script and successful live run
8. Workflow latency benchmark report in artifacts/performance_reports/workflow_latency_20260403_141659Z.json
