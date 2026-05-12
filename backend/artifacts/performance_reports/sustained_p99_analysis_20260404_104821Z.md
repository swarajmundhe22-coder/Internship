# P99 Sustained Load Analysis

Generated UTC: 2026-04-04T10:48:21.700710+00:00

## Pre-Optimization P99 Heatmap

| Tier | Endpoint | P50 (ms) | P95 (ms) | P99 (ms) | Max (ms) | Spikes > Ceiling | SLA P99 | Status |
|---|---|---:|---:|---:|---:|---:|---:|---|
| low | simulate_post | 70.16 | 139.42 | 223.06 | 223.06 | 0 | 100 | FAIL |
| low | ops_performance_get | 29.87 | 61.99 | 61.99 | 61.99 | 0 | 100 | PASS |
| low | auth_login_post | 172.19 | 309.66 | 359.64 | 359.64 | 3 | 100 | FAIL |
| low | health_get | 12.21 | 18.66 | 19.01 | 19.01 | 0 | 100 | PASS |
| medium | ops_performance_get | 4815.76 | 20402.44 | 23761.53 | 23761.53 | 53 | 150 | FAIL |
| medium | auth_login_post | 5641.52 | 18957.78 | 19385.83 | 19385.83 | 58 | 150 | FAIL |
| medium | health_get | 36.34 | 1523.04 | 1577.06 | 1577.06 | 10 | 150 | FAIL |
| medium | simulate_post | 5857.15 | 18515.06 | 25249.17 | 26532.47 | 272 | 150 | FAIL |
| high | auth_login_post | 86.24 | 1285.51 | 3248.04 | 3752.40 | 21 | 200 | FAIL |
| high | simulate_post | 33.92 | 476.47 | 1260.90 | 3346.38 | 50 | 200 | FAIL |
| high | ops_performance_get | 17.46 | 214.41 | 282.76 | 282.76 | 1 | 200 | FAIL |
| high | health_get | 5.53 | 31.34 | 67.72 | 100.60 | 0 | 200 | PASS |

## 瓶颈分析

- thread_starvation_or_event_loop_lag
- cache_misses

## Flame-Graph Evidence

- Profile artifacts: see `artifacts/performance_reports/simulation_profile_*.prof` and `simulation_profile_*.txt`.
