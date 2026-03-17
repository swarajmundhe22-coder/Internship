from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

import httpx
import pytest

from app.models.auth import AuthPrincipal, UserRole
from app.models.intelligence import IoTConnectorEvent, IoTStreamIngestRequest
from app.services.connector_adapter_service import ConnectorAdapterService, ConnectorPullRequest
from app.services.intelligence_service import IntelligenceService
from app.services.satellite_provider_client_service import SatelliteProviderClientService


@pytest.mark.asyncio
async def test_satellite_provider_client_signs_requests(monkeypatch: pytest.MonkeyPatch) -> None:
    client = SatelliteProviderClientService()
    original = {
        "satellite_provider_base_url": client.settings.satellite_provider_base_url,
        "satellite_provider_api_key": client.settings.satellite_provider_api_key,
        "satellite_provider_hmac_secret": client.settings.satellite_provider_hmac_secret,
        "satellite_provider_mock_mode": client.settings.satellite_provider_mock_mode,
        "satellite_provider_timeout_seconds": client.settings.satellite_provider_timeout_seconds,
    }
    client.settings.satellite_provider_base_url = "https://provider.example.com"
    client.settings.satellite_provider_api_key = "api-key-123"
    client.settings.satellite_provider_hmac_secret = "secret-xyz"
    client.settings.satellite_provider_mock_mode = False
    client.settings.satellite_provider_timeout_seconds = 5

    observed: dict[str, object] = {}

    async def fake_post(self, url, json=None, headers=None, **kwargs):  # type: ignore[no-untyped-def]
        observed["url"] = url
        observed["headers"] = headers or {}
        request = httpx.Request("POST", url)
        return httpx.Response(
            status_code=200,
            request=request,
            json={"provider": "sentinel", "region": "north-sea", "severity_index": 0.72, "frames": []},
        )

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

    try:
        payload = await client.fetch_imagery(provider="sentinel", region="north-sea")
        assert payload["provider"] == "sentinel"

        headers = observed["headers"]
        assert isinstance(headers, dict)
        assert headers.get("Authorization") == "Bearer api-key-123"
        assert isinstance(headers.get("X-OnLooker-Signature"), str)
        assert len(headers["X-OnLooker-Signature"]) >= 32
    finally:
        client.settings.satellite_provider_base_url = original["satellite_provider_base_url"]
        client.settings.satellite_provider_api_key = original["satellite_provider_api_key"]
        client.settings.satellite_provider_hmac_secret = original["satellite_provider_hmac_secret"]
        client.settings.satellite_provider_mock_mode = original["satellite_provider_mock_mode"]
        client.settings.satellite_provider_timeout_seconds = original["satellite_provider_timeout_seconds"]


@pytest.mark.asyncio
async def test_connector_device_gateway_uses_signed_headers(monkeypatch: pytest.MonkeyPatch) -> None:
    adapter = ConnectorAdapterService()
    original = {
        "device_gateway_url": adapter.settings.device_gateway_url,
        "device_gateway_api_key": adapter.settings.device_gateway_api_key,
        "device_gateway_hmac_secret": adapter.settings.device_gateway_hmac_secret,
    }
    adapter.settings.device_gateway_url = "https://gateway.example.com"
    adapter.settings.device_gateway_api_key = "gw-key"
    adapter.settings.device_gateway_hmac_secret = "gw-secret"

    observed: dict[str, object] = {}

    async def fake_get(self, url, params=None, headers=None, **kwargs):  # type: ignore[no-untyped-def]
        observed["url"] = url
        observed["params"] = params
        observed["headers"] = headers or {}
        request = httpx.Request("GET", url)
        return httpx.Response(
            status_code=200,
            request=request,
            json=[
                {
                    "sensor_id": "gateway-01",
                    "payload": {"temperature_c": 27.4, "humidity_pct": 64.0},
                }
            ],
        )

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    try:
        events = await adapter.pull_events(
            ConnectorPullRequest(
                connector_type="device_gateway",
                tenant_id=str(uuid4()),
                max_events=10,
            )
        )

        assert len(events) == 1
        assert events[0].sensor_id == "gateway-01"
        headers = observed["headers"]
        assert isinstance(headers, dict)
        assert headers.get("Authorization") == "Bearer gw-key"
        assert isinstance(headers.get("X-OnLooker-Signature"), str)
    finally:
        adapter.settings.device_gateway_url = original["device_gateway_url"]
        adapter.settings.device_gateway_api_key = original["device_gateway_api_key"]
        adapter.settings.device_gateway_hmac_secret = original["device_gateway_hmac_secret"]


class _FakeRepo:
    async def tenant_exists(self, tenant_id):  # type: ignore[no-untyped-def]
        return True

    async def user_in_tenant(self, *, user_id, tenant_id):  # type: ignore[no-untyped-def]
        return True

    async def create_iot_data(self, *, tenant_id, sensor_id, payload):  # type: ignore[no-untyped-def]
        return SimpleNamespace(tenant_id=tenant_id, sensor_id=sensor_id, payload_json=str(payload))


class _FakeAdapter:
    async def pull_events(self, request):  # type: ignore[no-untyped-def]
        return [IoTConnectorEvent(sensor_id="kafka-01", payload={"temperature_c": 29.1})]


@pytest.mark.asyncio
async def test_intelligence_stream_ingest_pulls_from_adapter_when_events_empty() -> None:
    service = IntelligenceService(repository=_FakeRepo(), connector_adapter=_FakeAdapter())
    principal = AuthPrincipal(
        user_id=uuid4(),
        email="engineer@example.com",
        role=UserRole.engineer,
        session_id=uuid4(),
    )

    result = await service.ingest_iot_stream(
        principal=principal,
        payload=IoTStreamIngestRequest(
            tenant_id=uuid4(),
            connector_type="kafka",
            events=[],
            max_events=5,
        ),
    )

    assert result.accepted_events == 1
    assert result.dead_lettered_events == 0
