from __future__ import annotations

try:
    from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, Counter, Gauge, Histogram, generate_latest

    _registry = CollectorRegistry(auto_describe=True)

    _request_count = Counter(
        "onlooker_http_requests_total",
        "Total HTTP requests by method/path/status",
        labelnames=("method", "path", "status_code"),
        registry=_registry,
    )

    _request_latency = Histogram(
        "onlooker_http_request_latency_seconds",
        "HTTP request latency in seconds by method/path/status",
        labelnames=("method", "path", "status_code"),
        # Buckets tuned to sub-250 ms focus while still capturing long tails.
        buckets=(0.005, 0.01, 0.02, 0.05, 0.075, 0.1, 0.15, 0.2, 0.25, 0.5, 1.0, 2.0, 5.0),
        registry=_registry,
    )

    _active_requests = Gauge(
        "onlooker_active_requests",
        "Current active in-flight requests",
        registry=_registry,
    )

    _request_capacity = Gauge(
        "onlooker_request_capacity",
        "Configured in-flight request capacity before shedding",
        registry=_registry,
    )

    _request_shed = Counter(
        "onlooker_request_shed_total",
        "Total requests shed by resilience controls",
        labelnames=("path", "reason"),
        registry=_registry,
    )

    _circuit_breaker_open = Counter(
        "onlooker_circuit_breaker_open_total",
        "Total number of circuit breaker open transitions",
        labelnames=("path",),
        registry=_registry,
    )

    _circuit_breaker_state = Gauge(
        "onlooker_circuit_breaker_state",
        "Circuit breaker state by path: closed=0, half_open=0.5, open=1",
        labelnames=("path",),
        registry=_registry,
    )
except Exception:  # pragma: no cover - telemetry package may be unavailable in minimal envs.
    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4"
    _registry = None
    _request_count = None
    _request_latency = None
    _active_requests = None
    _request_capacity = None
    _request_shed = None
    _circuit_breaker_open = None
    _circuit_breaker_state = None

    def generate_latest(_registry_obj):  # type: ignore[no-redef]
        return b""


def observe_request(*, method: str, path: str, status_code: int, latency_ms: float) -> None:
    if _request_count is None or _request_latency is None:
        return
    status = str(status_code)
    _request_count.labels(method=method.upper(), path=path, status_code=status).inc()
    _request_latency.labels(method=method.upper(), path=path, status_code=status).observe(max(latency_ms, 0.0) / 1000.0)


def set_active_requests(value: int) -> None:
    if _active_requests is None:
        return
    _active_requests.set(max(int(value), 0))


def set_request_capacity(value: int) -> None:
    if _request_capacity is None:
        return
    _request_capacity.set(max(int(value), 0))


def inc_request_shed(*, path: str, reason: str) -> None:
    if _request_shed is None:
        return
    _request_shed.labels(path=path, reason=reason).inc()


def inc_circuit_breaker_open(*, path: str) -> None:
    if _circuit_breaker_open is None:
        return
    _circuit_breaker_open.labels(path=path).inc()


def set_circuit_breaker_state(*, path: str, state_value: float) -> None:
    if _circuit_breaker_state is None:
        return
    _circuit_breaker_state.labels(path=path).set(float(state_value))


def export_prometheus_payload() -> tuple[bytes, str]:
    return generate_latest(_registry), CONTENT_TYPE_LATEST
