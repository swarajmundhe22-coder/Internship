from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import UTC, datetime
from threading import Lock
from time import monotonic
from typing import Any

from app.core.config import get_settings
from app.core.prometheus_metrics import (
    inc_circuit_breaker_open,
    inc_request_shed,
    set_active_requests,
    set_circuit_breaker_state,
    set_request_capacity,
)


@dataclass(frozen=True)
class _RequestOutcome:
    timestamp_monotonic: float
    failed: bool


class PathCircuitBreaker:
    def __init__(
        self,
        *,
        path: str,
        window_seconds: int,
        min_requests: int,
        failure_rate_threshold: float,
        open_seconds: int,
        half_open_max_requests: int,
        latency_failure_threshold_ms: int,
    ) -> None:
        self.path = path
        self.window_seconds = window_seconds
        self.min_requests = min_requests
        self.failure_rate_threshold = failure_rate_threshold
        self.open_seconds = open_seconds
        self.half_open_max_requests = half_open_max_requests
        self.latency_failure_threshold_ms = latency_failure_threshold_ms

        self.state = "closed"
        self._opened_until_monotonic = 0.0
        self._half_open_remaining = 0
        self._half_open_successes = 0
        self._recent: deque[_RequestOutcome] = deque()

        set_circuit_breaker_state(path=self.path, state_value=0.0)

    def allow_request(self, *, now_monotonic: float) -> tuple[bool, str | None]:
        if self.state == "open":
            if now_monotonic < self._opened_until_monotonic:
                return False, "circuit_open"
            self._transition_to_half_open()

        if self.state == "half_open":
            if self._half_open_remaining <= 0:
                return False, "circuit_half_open_limited"
            self._half_open_remaining -= 1

        return True, None

    def record_result(self, *, status_code: int, latency_ms: float, now_monotonic: float) -> None:
        failed = status_code >= 500 or latency_ms >= self.latency_failure_threshold_ms
        self._recent.append(_RequestOutcome(timestamp_monotonic=now_monotonic, failed=failed))
        self._prune(now_monotonic)

        if self.state == "half_open":
            if failed:
                self._transition_to_open(now_monotonic)
                return
            self._half_open_successes += 1
            if self._half_open_successes >= self.half_open_max_requests:
                self._transition_to_closed()
            return

        if self.state != "closed":
            return

        if len(self._recent) < self.min_requests:
            return

        failures = sum(1 for item in self._recent if item.failed)
        failure_rate = failures / len(self._recent)
        if failure_rate >= self.failure_rate_threshold:
            self._transition_to_open(now_monotonic)

    def snapshot(self) -> dict[str, Any]:
        request_count = len(self._recent)
        failures = sum(1 for item in self._recent if item.failed)
        failure_rate = (failures / request_count) if request_count else 0.0
        return {
            "path": self.path,
            "state": self.state,
            "recent_request_count": request_count,
            "recent_failure_rate": failure_rate,
            "opened_until_monotonic": self._opened_until_monotonic,
            "half_open_remaining": self._half_open_remaining,
            "latency_failure_threshold_ms": self.latency_failure_threshold_ms,
        }

    def _transition_to_open(self, now_monotonic: float) -> None:
        self.state = "open"
        self._opened_until_monotonic = now_monotonic + self.open_seconds
        self._half_open_remaining = 0
        self._half_open_successes = 0
        set_circuit_breaker_state(path=self.path, state_value=1.0)
        inc_circuit_breaker_open(path=self.path)

    def _transition_to_half_open(self) -> None:
        self.state = "half_open"
        self._half_open_remaining = self.half_open_max_requests
        self._half_open_successes = 0
        set_circuit_breaker_state(path=self.path, state_value=0.5)

    def _transition_to_closed(self) -> None:
        self.state = "closed"
        self._opened_until_monotonic = 0.0
        self._half_open_remaining = 0
        self._half_open_successes = 0
        self._recent.clear()
        set_circuit_breaker_state(path=self.path, state_value=0.0)

    def _prune(self, now_monotonic: float) -> None:
        cutoff = now_monotonic - self.window_seconds
        while self._recent and self._recent[0].timestamp_monotonic < cutoff:
            self._recent.popleft()


class ResilienceController:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.enabled = bool(self.settings.resilience_enabled)
        self.max_inflight_requests = self.settings.resilience_max_inflight_requests

        protected_paths = [
            item.strip()
            for item in self.settings.resilience_protected_paths.split(",")
            if item.strip()
        ]

        self._breakers: dict[str, PathCircuitBreaker] = {
            path: PathCircuitBreaker(
                path=path,
                window_seconds=self.settings.circuit_breaker_window_seconds,
                min_requests=self.settings.circuit_breaker_min_requests,
                failure_rate_threshold=self.settings.circuit_breaker_failure_rate_threshold,
                open_seconds=self.settings.circuit_breaker_open_seconds,
                half_open_max_requests=self.settings.circuit_breaker_half_open_max_requests,
                latency_failure_threshold_ms=self.settings.circuit_breaker_latency_failure_threshold_ms,
            )
            for path in protected_paths
        }

        self._active_requests = 0
        self._shed_total = 0
        self._shed_overload = 0
        self._shed_circuit_open = 0

        self._lock = Lock()

        set_request_capacity(self.max_inflight_requests)
        set_active_requests(0)

    def admit(self, *, path: str) -> tuple[bool, str | None]:
        with self._lock:
            if self.enabled and self._active_requests >= self.max_inflight_requests:
                self._shed_total += 1
                self._shed_overload += 1
                inc_request_shed(path=path, reason="overload")
                return False, "overload"

            breaker = self._breakers.get(path)
            if self.enabled and breaker is not None:
                allowed, reason = breaker.allow_request(now_monotonic=monotonic())
                if not allowed:
                    self._shed_total += 1
                    self._shed_circuit_open += 1
                    inc_request_shed(path=path, reason="circuit_open")
                    return False, reason

            self._active_requests += 1
            set_active_requests(self._active_requests)
            return True, None

    def release(self, *, path: str, status_code: int, latency_ms: float) -> None:
        with self._lock:
            breaker = self._breakers.get(path)
            if self.enabled and breaker is not None:
                breaker.record_result(
                    status_code=status_code,
                    latency_ms=latency_ms,
                    now_monotonic=monotonic(),
                )

            self._active_requests = max(self._active_requests - 1, 0)
            set_active_requests(self._active_requests)

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "generated_at_utc": datetime.now(UTC).isoformat(),
                "enabled": self.enabled,
                "active_requests": self._active_requests,
                "max_inflight_requests": self.max_inflight_requests,
                "shed_total": self._shed_total,
                "shed_overload": self._shed_overload,
                "shed_circuit_open": self._shed_circuit_open,
                "circuit_breakers": [breaker.snapshot() for breaker in self._breakers.values()],
            }


_controller = ResilienceController()


def get_resilience_controller() -> ResilienceController:
    return _controller
