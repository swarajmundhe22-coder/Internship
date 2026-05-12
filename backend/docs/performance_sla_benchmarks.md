# Performance SLA Benchmarks and Optimization Strategy

## 1. Current Runtime Baseline

Observed runtime snapshot (latest live monitor run):

- p99 latency: 86.97 ms
- 5xx error rate: 0.0
- sampled requests: 422

Interpretation:

- The system is currently healthy and below 100 ms p99.
- The system is above the new normal-load target of 75 ms p99 and above the stretch target of 50 ms p99.

## 2. Target SLA and SLO Policy

Primary production targets:

- Normal load p99 latency <= 75 ms
- Availability >= 99.9%
- Zero critical errors under normal load

Stretch target:

- Consistent p99 latency <= 50 ms under normal load

Burst/load-resilience target:

- 10x traffic scenario (4,000+ concurrent requests) with p99 <= 100 ms

## 3. Implemented Optimization Controls

### 3.1 Resilience and Overload Protection

Implemented controls:

- Request shedding when in-flight capacity is saturated (`RESILIENCE_MAX_INFLIGHT_REQUESTS`).
- Path-level circuit breakers for critical routes (default: `/api/v1/simulation/simulate`, `/api/v1/auth/login`).
- Circuit opening based on combined failure criteria:
  - 5xx responses, and
  - latency over `CIRCUIT_BREAKER_LATENCY_FAILURE_THRESHOLD_MS`.

Outcome:

- Tail-latency protection during spikes by failing fast instead of queueing until timeout.
- Reduced risk of cascading resource collapse.

### 3.2 Autoscaling Policy Improvements

Implemented controls:

- HPA resource metrics: CPU 60%, memory 70%.
- HPA custom pod metric: average `onlooker_active_requests` target of 800.

Outcome:

- Faster scale-up signal from request pressure, not only CPU/memory lagging indicators.

### 3.3 Monitoring and Alerting Coverage

Added/updated signals:

- Request shed rate (`onlooker_request_shed_total`).
- Circuit breaker state (`onlooker_circuit_breaker_state`).
- In-flight request saturation (`onlooker_active_requests / onlooker_request_capacity`).

Alert classes:

- Latency SLA breaches (low/medium/high).
- Error-budget burn.
- Request shedding sustained.
- Circuit breaker open sustained.
- In-flight request saturation > 90%.

### 3.4 10x Load Scenario Harness

Added script:

- `python scripts/load_resilience_10x.py --concurrency 4000 --total-requests 12000 --p99-budget-ms 100 --strict`

Outcome:

- Standardized artifact-driven scenario for 4,000+ concurrent request validation.

## 4. Bottleneck Identification Framework

During each performance campaign, classify regressions by these signatures:

- Queueing saturation: rising active requests, request shedding, and p95/p99 divergence.
- Breaker pressure: breaker state opens and elevated shed reason `circuit_open`.
- DB pressure: pool hold-time tail growth and churn anomalies in `/ops/performance`.
- Cache underutilization: low hit-rate versus target on read-through namespaces.
- Runtime pressure: elevated event-loop lag and process CPU/memory trends in analyzer artifacts.

## 5. Benchmark Execution Matrix

### Normal-Load Stability

1. `python scripts/monitor_p99_latency.py --base-url http://127.0.0.1:8000/api/v1 --p99-budget-ms 75 --strict`
2. `python scripts/sustained_p99_analyzer.py --base-url http://127.0.0.1:8000/api/v1 --baseline-qps <normal> --duration-seconds 1800 --strict`

Passing criteria:

- runtime p99 <= 75 ms
- zero critical latency/error alerts
- no request shedding during normal load

### 10x Concurrency Resilience

1. `python scripts/load_resilience_10x.py --base-url http://127.0.0.1:8000/api/v1 --concurrency 4000 --total-requests 12000 --p99-budget-ms 100 --strict`

Passing criteria:

- concurrency requirement satisfied (>= 4000)
- aggregate p99 <= 100 ms
- 5xx error rate within budget

## 6. Capacity Objective (50% Higher Load)

Support strategy with existing infrastructure:

- Keep in-flight protection enabled to prevent collapse.
- Scale based on active-request pressure before CPU saturation.
- Use circuit-breaker fast-fail behavior to preserve healthy path latency.
- Tune pool/cache/audit-batch settings based on artifacts from sustained and 10x tests.

## 7. Release Gate Requirements

Release is approved only when:

- normal-load p99 <= 75 ms,
- 99.9% availability objective remains on trend,
- no critical error path is active under normal load,
- 10x scenario artifacts are generated and reviewed,
- no unresolved critical alerts in resilience or latency panels.
