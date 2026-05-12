# Sustained 80-User Validation Report

Generated UTC: 2026-04-04T12:29:47.593756+00:00
Base URL: http://127.0.0.1:18006/api/v1

## Workload

- Active users: 80
- Duration target: 300 s
- Duration observed: 301.03 s
- Observed RPS: 120.56

## Aggregate Results

- Error rate 5xx: 0.000220
- Latency avg: 266.58 ms
- Latency p95: 1063.01 ms
- Latency p99: 2176.92 ms
- Latency max: 6806.28 ms

## Checks

- duration_requirement: PASS
- aggregate_p99_budget: FAIL
- aggregate_error_budget: FAIL
- window_stability: FAIL

## Final Status: FAIL
