from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import UTC, datetime
from threading import Lock
from time import monotonic
from typing import Any


@dataclass(frozen=True)
class PoolHoldSample:
    checkout_duration_seconds: float
    recorded_epoch: float


class DbPoolMonitor:
    def __init__(self, *, leak_threshold_seconds: int, sample_window: int = 2000) -> None:
        self.leak_threshold_seconds = max(int(leak_threshold_seconds), 1)
        self._samples: deque[PoolHoldSample] = deque(maxlen=max(sample_window, 100))
        self._active_checkouts: dict[int, float] = {}
        self._checkout_count = 0
        self._checkin_count = 0
        self._leak_alert_count = 0
        self._first_event_epoch = monotonic()
        self._lock = Lock()

    def on_checkout(self, connection_record_id: int) -> None:
        now_value = monotonic()
        with self._lock:
            self._checkout_count += 1
            self._active_checkouts[connection_record_id] = now_value

    def on_checkin(self, connection_record_id: int) -> float:
        now_value = monotonic()
        with self._lock:
            self._checkin_count += 1
            started_at = self._active_checkouts.pop(connection_record_id, None)
            if started_at is None:
                return 0.0

            held_for = max(now_value - started_at, 0.0)
            self._samples.append(PoolHoldSample(checkout_duration_seconds=held_for, recorded_epoch=now_value))
            if held_for >= self.leak_threshold_seconds:
                self._leak_alert_count += 1
            return held_for

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            durations = [sample.checkout_duration_seconds for sample in self._samples]
            elapsed = max(monotonic() - self._first_event_epoch, 0.001)
            churn_per_second = self._checkout_count / elapsed
            return {
                "generated_at_utc": datetime.now(UTC).isoformat(),
                "active_checkouts": len(self._active_checkouts),
                "checkout_count": self._checkout_count,
                "checkin_count": self._checkin_count,
                "connection_churn_per_second": churn_per_second,
                "leak_alert_count": self._leak_alert_count,
                "max_hold_seconds": max(durations) if durations else 0.0,
                "p95_hold_seconds": _percentile(durations, 0.95),
                "p99_hold_seconds": _percentile(durations, 0.99),
                "leak_threshold_seconds": self.leak_threshold_seconds,
            }


# Local utility to avoid importing percentile helper from request-performance module.
def _percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = max(min(int(len(ordered) * p) - 1, len(ordered) - 1), 0)
    return float(ordered[idx])
