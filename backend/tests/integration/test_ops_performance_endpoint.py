from __future__ import annotations

from collections.abc import Generator
from uuid import uuid4

import pytest
from httpx import AsyncClient

from app.core.performance import get_performance_monitor


@pytest.fixture(autouse=True)
def clear_performance_monitor() -> Generator[None, None, None]:
    monitor = get_performance_monitor()
    monitor.clear()
    yield
    monitor.clear()


async def _register(api_client: AsyncClient, role: str) -> dict[str, str]:
    response = await api_client.post(
        "/api/v1/auth/register",
        json={
            "email": f"ops-performance-{role}-{uuid4().hex}@example.com",
            "password": "StrongPass123",
            "role": role,
        },
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_ops_performance_endpoint_returns_runtime_metrics_for_engineer(api_client: AsyncClient) -> None:
    monitor = get_performance_monitor()
    for idx in range(60):
        monitor.record_request(
            method="POST",
            path="/api/v1/simulation/simulate",
            status_code=200 if idx < 58 else 500,
            latency_ms=90.0 + idx,
        )

    headers = await _register(api_client, role="engineer")
    response = await api_client.get(
        "/api/v1/ops/performance",
        headers=headers,
        params={"path": "/api/v1/simulation/simulate", "include_paths": "true", "top": "2"},
    )

    assert response.status_code == 200
    payload = response.json()

    assert payload["request_count"] == 60
    assert payload["server_error_count"] == 2
    assert payload["latency_ms"]["p99"] >= payload["latency_ms"]["p95"]
    assert payload["budgets"]["p99_latency_ms"] >= 100
    assert payload["alerts"]["error_budget_burn_rate"] >= 0
    assert len(payload["top_slowest_paths"]) >= 1


@pytest.mark.asyncio
async def test_ops_performance_endpoint_forbids_viewer(api_client: AsyncClient) -> None:
    headers = await _register(api_client, role="viewer")
    response = await api_client.get("/api/v1/ops/performance", headers=headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_ops_performance_endpoint_requires_auth(api_client: AsyncClient) -> None:
    response = await api_client.get("/api/v1/ops/performance")
    assert response.status_code in (401, 403)
