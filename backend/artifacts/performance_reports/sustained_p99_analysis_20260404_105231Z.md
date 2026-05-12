# P99 Sustained Load Analysis

Generated UTC: 2026-04-04T10:52:31.118484+00:00

## Pre-Optimization P99 Heatmap

| Tier | Endpoint | P50 (ms) | P95 (ms) | P99 (ms) | Max (ms) | Spikes > Ceiling | SLA P99 | Status |
|---|---|---:|---:|---:|---:|---:|---:|---|
| low | simulate_post | 11.05 | 20.70 | 35.49 | 35.49 | 0 | 100 | PASS |
| low | ops_performance_get | 14.43 | 23.99 | 23.99 | 23.99 | 0 | 100 | PASS |
| low | auth_login_post | 40.25 | 50.62 | 50.62 | 50.62 | 0 | 100 | PASS |
| low | health_get | 4.56 | 8.40 | 8.40 | 8.40 | 0 | 100 | PASS |
| medium | health_get | 4.88 | 8.16 | 8.78 | 8.78 | 0 | 150 | PASS |
| medium | auth_login_post | 47.58 | 59.25 | 59.25 | 59.25 | 0 | 150 | PASS |
| medium | ops_performance_get | 12.31 | 14.09 | 14.09 | 14.09 | 0 | 150 | PASS |
| medium | simulate_post | 14.02 | 19.25 | 24.02 | 28.23 | 0 | 150 | PASS |
| high | simulate_post | 15.01 | 30.46 | 75.25 | 78.20 | 0 | 200 | PASS |
| high | health_get | 4.68 | 9.67 | 9.88 | 9.88 | 0 | 200 | PASS |
| high | ops_performance_get | 12.98 | 23.97 | 28.02 | 28.02 | 0 | 200 | PASS |
| high | auth_login_post | 52.52 | 108.10 | 112.84 | 112.84 | 0 | 200 | PASS |

## 瓶颈分析

- thread_starvation_or_event_loop_lag
- cache_misses

## Flame-Graph Evidence

- Profile artifacts: see `artifacts/performance_reports/simulation_profile_*.prof` and `simulation_profile_*.txt`.
