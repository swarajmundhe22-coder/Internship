from __future__ import annotations

from app.core.performance import RollingPerformanceMonitor, percentile


def _monitor() -> RollingPerformanceMonitor:
    return RollingPerformanceMonitor(
        window_seconds=60,
        max_samples=10,
        p95_budget_ms=100,
        p99_budget_ms=120,
        error_budget_rate=0.1,
        min_samples_for_alerts=3,
    )


def test_percentile_handles_empty_and_single_values() -> None:
    assert percentile([], 0.95) == 0.0
    assert percentile([42.0], 0.95) == 42.0


def test_snapshot_computes_latency_and_error_metrics() -> None:
    monitor = _monitor()
    monitor.record_request(method="POST", path="/api/v1/simulation/simulate", status_code=200, latency_ms=80, now_epoch=10)
    monitor.record_request(method="POST", path="/api/v1/simulation/simulate", status_code=200, latency_ms=110, now_epoch=11)
    monitor.record_request(method="POST", path="/api/v1/simulation/simulate", status_code=500, latency_ms=140, now_epoch=12)

    payload = monitor.snapshot(path_filter="/api/v1/simulation/simulate", now_epoch=12)

    assert payload["request_count"] == 3
    assert payload["server_error_count"] == 1
    assert payload["error_rate_5xx"] == 1 / 3
    assert payload["latency_ms"]["p95"] == 140.0
    assert payload["latency_ms"]["p99"] == 140.0
    assert payload["checks"]["p95_latency_budget"] is False
    assert payload["checks"]["p99_latency_budget"] is False


def test_snapshot_prunes_old_samples_and_respects_max_samples() -> None:
    monitor = _monitor()
    for idx in range(12):
        monitor.record_request(
            method="GET",
            path="/health",
            status_code=200,
            latency_ms=10 + idx,
            now_epoch=float(idx),
        )

    payload_after_cap = monitor.snapshot(now_epoch=12)
    assert payload_after_cap["request_count"] == 10

    payload_after_window = monitor.snapshot(now_epoch=130)
    assert payload_after_window["request_count"] == 0


def test_alerts_trigger_only_after_minimum_sample_threshold() -> None:
    monitor = _monitor()
    for idx in range(2):
        monitor.record_request(
            method="POST",
            path="/api/v1/simulation/simulate",
            status_code=500,
            latency_ms=200,
            now_epoch=10 + idx,
        )

    too_few = monitor.snapshot(path_filter="/api/v1/simulation/simulate", now_epoch=12)
    assert too_few["alerts"]["critical_latency_p99"] is False
    assert too_few["alerts"]["critical_api_5xx_spike"] is False

    monitor.record_request(
        method="POST",
        path="/api/v1/simulation/simulate",
        status_code=500,
        latency_ms=220,
        now_epoch=13,
    )

    enough = monitor.snapshot(path_filter="/api/v1/simulation/simulate", now_epoch=13)
    assert enough["alerts"]["critical_latency_p99"] is True
    assert enough["alerts"]["critical_api_5xx_spike"] is True


def test_path_breakdown_orders_slowest_endpoints() -> None:
    monitor = _monitor()
    monitor.record_request(method="GET", path="/a", status_code=200, latency_ms=20, now_epoch=1)
    monitor.record_request(method="GET", path="/a", status_code=200, latency_ms=40, now_epoch=2)
    monitor.record_request(method="GET", path="/b", status_code=200, latency_ms=100, now_epoch=3)

    payload = monitor.snapshot(include_path_breakdown=True, top_paths=2, now_epoch=3)
    top = payload["top_slowest_paths"]

    assert len(top) == 2
    assert top[0]["endpoint"] == "GET /b"
    assert top[1]["endpoint"] == "GET /a"
