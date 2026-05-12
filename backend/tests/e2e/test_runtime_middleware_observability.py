from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import get_settings
from app.core.performance import get_performance_monitor
from app.main import app


@pytest.mark.asyncio
async def test_main_app_records_runtime_latency_and_headers() -> None:
    settings = get_settings()
    original_auto_init = settings.auto_initialize_db
    settings.auto_initialize_db = False

    monitor = get_performance_monitor()
    monitor.clear()

    try:
        transport = ASGITransport(app=app, raise_app_exceptions=False)
        async with AsyncClient(transport=transport, base_url="http://testserver") as client:
            response = await client.get("/")

        assert response.status_code == 200
        assert response.headers.get("X-Correlation-ID")
        assert response.headers.get("X-Process-Time-Ms")

        snapshot = monitor.snapshot(path_filter="/")
        assert snapshot["request_count"] >= 1
        assert snapshot["latency_ms"]["p99"] >= 0
    finally:
        settings.auto_initialize_db = original_auto_init
        monitor.clear()
