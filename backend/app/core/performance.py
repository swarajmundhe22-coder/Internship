from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import UTC, datetime
import math
from threading import Lock
from time import time
from typing import Any

from app.core.config import get_settings


@dataclass(frozen=True)
class RequestObservation:
    timestamp_epoch: float
    method: str
    path: str
    status_code: int
    latency_ms: float


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(max(math.ceil(len(ordered) * p) - 1, 0), len(ordered) - 1)
    return float(ordered[index])


class RollingPerformanceMonitor:
    def __init__(
        self,
        *,
        window_seconds: int,
        max_samples: int,
        p95_budget_ms: int,
        p99_budget_ms: int,
        error_budget_rate: float,
        min_samples_for_alerts: int,
    ) -> None:
        self.window_seconds = window_seconds
        self.max_samples = max_samples
        self.p95_budget_ms = p95_budget_ms
        self.p99_budget_ms = p99_budget_ms
        self.error_budget_rate = error_budget_rate
        self.min_samples_for_alerts = min_samples_for_alerts

        self._samples: deque[RequestObservation] = deque()
        self._lock = Lock()

    def clear(self) -> None:
        with self._lock:
            self._samples.clear()

    def record_request(
        self,
        *,
        method: str,
        path: str,
        status_code: int,
        latency_ms: float,
        now_epoch: float | None = None,
    ) -> None:
        now_value = now_epoch if now_epoch is not None else time()
        sample = RequestObservation(
            timestamp_epoch=now_value,
            method=method.upper(),
            path=path,
            status_code=status_code,
            latency_ms=max(float(latency_ms), 0.0),
        )

        with self._lock:
            self._samples.append(sample)
            self._prune_locked(now_value)

    def snapshot(
        self,
        *,
        path_filter: str | None = None,
        include_path_breakdown: bool = False,
        top_paths: int = 5,
        now_epoch: float | None = None,
    ) -> dict[str, Any]:
        now_value = now_epoch if now_epoch is not None else time()
        with self._lock:
            self._prune_locked(now_value)
            rows = list(self._samples)

        if path_filter:
            rows = [row for row in rows if row.path == path_filter]

        latency_values = [row.latency_ms for row in rows]
        request_count = len(rows)
        server_errors = sum(1 for row in rows if row.status_code >= 500)
        success_count = request_count - server_errors
        error_rate = (server_errors / request_count) if request_count else 0.0

        p50_latency = percentile(latency_values, 0.50)
        p95_latency = percentile(latency_values, 0.95)
        p99_latency = percentile(latency_values, 0.99)
        avg_latency = (sum(latency_values) / request_count) if request_count else 0.0
        max_latency = max(latency_values) if latency_values else 0.0

        checks = {
            "p95_latency_budget": p95_latency <= self.p95_budget_ms,
            "p99_latency_budget": p99_latency <= self.p99_budget_ms,
            "error_budget": error_rate <= self.error_budget_rate,
        }

        burn_rate = (error_rate / self.error_budget_rate) if self.error_budget_rate > 0 else 0.0
        enough_samples = request_count >= self.min_samples_for_alerts
        alerts = {
            "critical_api_5xx_spike": enough_samples and error_rate > 0.05,
            "warning_latency_p95": enough_samples and p95_latency > self.p95_budget_ms,
            "critical_latency_p99": enough_samples and p99_latency > self.p99_budget_ms,
            "warning_error_budget_burn": enough_samples and burn_rate >= 4.0,
        }

        response: dict[str, Any] = {
            "generated_at_utc": datetime.now(UTC).isoformat(),
            "window_seconds": self.window_seconds,
            "window_start_utc": datetime.fromtimestamp(max(now_value - self.window_seconds, 0), tz=UTC).isoformat(),
            "window_end_utc": datetime.fromtimestamp(now_value, tz=UTC).isoformat(),
            "path_filter": path_filter,
            "request_count": request_count,
            "success_count": success_count,
            "server_error_count": server_errors,
            "error_rate_5xx": error_rate,
            "latency_ms": {
                "p50": p50_latency,
                "p95": p95_latency,
                "p99": p99_latency,
                "avg": avg_latency,
                "max": max_latency,
            },
            "budgets": {
                "p95_latency_ms": self.p95_budget_ms,
                "p99_latency_ms": self.p99_budget_ms,
                "error_rate": self.error_budget_rate,
            },
            "checks": checks,
            "alerts": {
                **alerts,
                "error_budget_burn_rate": burn_rate,
            },
        }

        if include_path_breakdown:
            response["top_slowest_paths"] = self._build_path_breakdown(rows=rows, top_paths=top_paths)

        return response

    def _build_path_breakdown(self, *, rows: list[RequestObservation], top_paths: int) -> list[dict[str, Any]]:
        groups: dict[str, list[RequestObservation]] = {}
        for row in rows:
            key = f"{row.method} {row.path}"
            groups.setdefault(key, []).append(row)

        metrics: list[dict[str, Any]] = []
        for key, group in groups.items():
            latencies = [item.latency_ms for item in group]
            request_count = len(group)
            server_errors = sum(1 for item in group if item.status_code >= 500)
            metrics.append(
                {
                    "endpoint": key,
                    "request_count": request_count,
                    "error_rate_5xx": (server_errors / request_count) if request_count else 0.0,
                    "p95_latency_ms": percentile(latencies, 0.95),
                    "p99_latency_ms": percentile(latencies, 0.99),
                    "avg_latency_ms": (sum(latencies) / request_count) if request_count else 0.0,
                }
            )

        metrics.sort(key=lambda item: (item["p99_latency_ms"], item["avg_latency_ms"]), reverse=True)
        return metrics[: max(1, top_paths)]

    def _prune_locked(self, now_epoch: float) -> None:
        cutoff = now_epoch - self.window_seconds
        while self._samples and self._samples[0].timestamp_epoch < cutoff:
            self._samples.popleft()

        while len(self._samples) > self.max_samples:
            self._samples.popleft()


_settings = get_settings()
_monitor = RollingPerformanceMonitor(
    window_seconds=_settings.performance_window_seconds,
    max_samples=_settings.performance_max_samples,
    p95_budget_ms=_settings.simulation_slo_p95_ms,
    p99_budget_ms=_settings.simulation_slo_p99_ms,
    error_budget_rate=_settings.simulation_error_budget_rate,
    min_samples_for_alerts=_settings.performance_min_samples_for_alerts,
)


def get_performance_monitor() -> RollingPerformanceMonitor:
    return _monitor
