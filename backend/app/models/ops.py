from __future__ import annotations

from datetime import datetime

from pydantic import Field

from app.models.common import BaseDomainModel


class OpsLatencySummary(BaseDomainModel):
    p50: float
    p95: float
    p99: float
    avg: float
    max: float


class OpsBudgetSummary(BaseDomainModel):
    p95_latency_ms: int
    p99_latency_ms: int
    error_rate: float


class OpsCheckSummary(BaseDomainModel):
    p95_latency_budget: bool
    p99_latency_budget: bool
    error_budget: bool


class OpsAlertSummary(BaseDomainModel):
    critical_api_5xx_spike: bool
    warning_latency_p95: bool
    critical_latency_p99: bool
    warning_error_budget_burn: bool
    error_budget_burn_rate: float


class OpsEndpointLatencySummary(BaseDomainModel):
    endpoint: str
    request_count: int
    error_rate_5xx: float
    p95_latency_ms: float
    p99_latency_ms: float
    avg_latency_ms: float


class OpsDbPoolSummary(BaseDomainModel):
    generated_at_utc: datetime
    active_checkouts: int
    checkout_count: int
    checkin_count: int
    connection_churn_per_second: float
    leak_alert_count: int
    max_hold_seconds: float
    p95_hold_seconds: float
    p99_hold_seconds: float
    leak_threshold_seconds: int


class OpsCacheSummary(BaseDomainModel):
    generated_at_utc: datetime
    namespace: str
    hits: int
    misses: int
    hit_rate: float
    target_hit_rate: float
    refreshes: int
    backend_errors: int
    backend: str
    local_entries: int


class OpsAuditBatchSummary(BaseDomainModel):
    generated_at_utc: datetime
    enabled: bool
    queue_depth: int
    enqueued: int
    dropped: int
    persisted: int
    batch_flush_count: int
    kafka_error_count: int
    db_error_count: int
    kafka_batch_size_bytes: int
    kafka_linger_ms: int


class OpsCircuitBreakerState(BaseDomainModel):
    path: str
    state: str
    recent_request_count: int
    recent_failure_rate: float
    opened_until_monotonic: float
    half_open_remaining: int
    latency_failure_threshold_ms: int


class OpsResilienceSummary(BaseDomainModel):
    generated_at_utc: datetime
    enabled: bool
    active_requests: int
    max_inflight_requests: int
    shed_total: int
    shed_overload: int
    shed_circuit_open: int
    circuit_breakers: list[OpsCircuitBreakerState] = Field(default_factory=list)


class OpsPerformanceResponse(BaseDomainModel):
    generated_at_utc: datetime
    window_seconds: int
    window_start_utc: datetime
    window_end_utc: datetime
    path_filter: str | None = None
    request_count: int
    success_count: int
    server_error_count: int
    error_rate_5xx: float
    latency_ms: OpsLatencySummary
    budgets: OpsBudgetSummary
    checks: OpsCheckSummary
    alerts: OpsAlertSummary
    top_slowest_paths: list[OpsEndpointLatencySummary] = Field(default_factory=list)
    db_pool: OpsDbPoolSummary | None = None
    caches: list[OpsCacheSummary] = Field(default_factory=list)
    audit_batch: OpsAuditBatchSummary | None = None
    resilience: OpsResilienceSummary | None = None
