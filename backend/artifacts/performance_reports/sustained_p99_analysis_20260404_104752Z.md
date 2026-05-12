# P99 Sustained Load Analysis

Generated UTC: 2026-04-04T10:47:52.128602+00:00

## Pre-Optimization P99 Heatmap

| Tier | Endpoint | P50 (ms) | P95 (ms) | P99 (ms) | Max (ms) | Spikes > Ceiling | SLA P99 | Status |
|---|---|---:|---:|---:|---:|---:|---:|---|
| low | auth_login_post | 118.09 | 158.94 | 172.19 | 172.19 | 0 | 100 | FAIL |
| low | simulate_post | 51.76 | 82.41 | 95.64 | 95.64 | 0 | 100 | PASS |
| low | health_get | 6.95 | 13.48 | 13.48 | 13.48 | 0 | 100 | PASS |
| low | ops_performance_get | 18.51 | 34.65 | 34.65 | 34.65 | 0 | 100 | PASS |
| medium | health_get | 9.36 | 30.54 | 35.88 | 35.88 | 0 | 150 | PASS |
| medium | simulate_post | 63.64 | 131.30 | 242.56 | 268.81 | 1 | 150 | FAIL |
| medium | auth_login_post | 149.98 | 254.68 | 314.58 | 314.58 | 5 | 150 | FAIL |
| medium | ops_performance_get | 26.03 | 79.87 | 115.97 | 115.97 | 0 | 150 | PASS |
| high | simulate_post | 8848.40 | 21886.90 | 25497.88 | 30010.14 | 414 | 200 | FAIL |
| high | auth_login_post | 10993.87 | 25905.51 | 30325.82 | 31718.40 | 102 | 200 | FAIL |
| high | health_get | 1194.50 | 13603.51 | 14309.59 | 14316.54 | 63 | 200 | FAIL |
| high | ops_performance_get | 7401.75 | 20295.81 | 22928.53 | 24721.60 | 99 | 200 | FAIL |

## 瓶颈分析

- thread_starvation_or_event_loop_lag
- cache_misses

## Flame-Graph Evidence

- Profile artifacts: see `artifacts/performance_reports/simulation_profile_*.prof` and `simulation_profile_*.txt`.
