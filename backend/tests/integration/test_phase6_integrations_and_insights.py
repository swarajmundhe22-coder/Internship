import pytest
import httpx
from httpx import AsyncClient
from uuid import uuid4


async def _register(api_client: AsyncClient, email: str, role: str = "engineer") -> dict[str, str]:
    response = await api_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "StrongPass123", "role": role},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def _create_project_with_prediction(api_client: AsyncClient, headers: dict[str, str]) -> tuple[str, str]:
    project = await api_client.post("/api/v1/projects", json={"name": "Phase6 Workspace"}, headers=headers)
    assert project.status_code == 200
    project_id = project.json()["id"]

    material = await api_client.post(
        "/api/v1/materials",
        json={
            "name": f"Phase6 Material {uuid4().hex[:8]}",
            "alloy_group": "Ferrous",
            "density_kg_m3": 7850.0,
            "electrochemical_potential_v": -0.61,
        },
        headers=headers,
    )
    environment = await api_client.post(
        "/api/v1/environment",
        json={
            "profile_name": f"Phase6 Env {uuid4().hex[:8]}",
            "temperature_c": 25.0,
            "relative_humidity_pct": 82.0,
            "chloride_ppm": 14000.0,
            "ph": 7.4,
            "dissolved_oxygen_mg_l": 7.1,
        },
        headers=headers,
    )
    simulation = await api_client.post(
        "/api/v1/simulation",
        json={
            "material_id": material.json()["id"],
            "environment_id": environment.json()["id"],
            "exposed_area_m2": 11.0,
            "exposure_time_hours": 1200.0,
            "corrosion_rate_mm_per_year": 0.11,
            "estimated_lifespan_years": 9.4,
            "risk_classification": "high",
        },
        headers=headers,
    )
    simulation_id = simulation.json()["id"]

    attached = await api_client.post(f"/api/v1/projects/{project_id}/simulations/{simulation_id}", headers=headers)
    assert attached.status_code == 200

    predicted = await api_client.post(
        f"/api/v1/projects/{project_id}/predict",
        json={"simulation_id": simulation_id, "horizon_hours": 120, "step_hours": 24},
        headers=headers,
    )
    assert predicted.status_code == 200
    return project_id, simulation_id


@pytest.mark.asyncio
async def test_project_insights_and_exports(api_client: AsyncClient) -> None:
    headers = await _register(api_client, f"phase6-insights-{uuid4().hex}@example.com")
    project_id, simulation_id = await _create_project_with_prediction(api_client, headers)

    insights = await api_client.get(f"/api/v1/projects/{project_id}/insights", headers=headers)
    assert insights.status_code == 200
    payload = insights.json()
    assert "summary" in payload
    assert isinstance(payload["recommendations"], list)

    insight_report = await api_client.get(f"/api/v1/projects/{project_id}/insights/report", headers=headers)
    assert insight_report.status_code == 200
    assert "The On Looker - AI Insights Report" in insight_report.text

    csv_export = await api_client.get(
        f"/api/v1/projects/{project_id}/predictions/export?format=csv",
        headers=headers,
    )
    assert csv_export.status_code == 200
    assert "text/csv" in csv_export.headers["content-type"]
    assert "risk_classification" in csv_export.text

    xlsx_export = await api_client.get(
        f"/api/v1/projects/{project_id}/predictions/export?format=xlsx&simulation_id={simulation_id}",
        headers=headers,
    )
    assert xlsx_export.status_code == 200
    assert "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" in xlsx_export.headers["content-type"]


@pytest.mark.asyncio
async def test_api_tokens_and_webhooks(api_client: AsyncClient) -> None:
    headers = await _register(api_client, f"phase6-integrations-{uuid4().hex}@example.com")

    token_created = await api_client.post(
        "/api/v1/integrations/api-tokens",
        json={"name": "SCADA Bridge", "scopes": ["predictions:read", "reports:read"], "expires_in_days": 30},
        headers=headers,
    )
    assert token_created.status_code == 200
    token_payload = token_created.json()
    assert token_payload["token"].startswith("olk_")

    token_list = await api_client.get("/api/v1/integrations/api-tokens", headers=headers)
    assert token_list.status_code == 200
    assert len(token_list.json()) == 1

    revoke = await api_client.delete(f"/api/v1/integrations/api-tokens/{token_payload['id']}", headers=headers)
    assert revoke.status_code == 200

    webhook_created = await api_client.post(
        "/api/v1/integrations/webhooks",
        json={"event_type": "report.completed", "target_url": "https://example.com/hooks/report"},
        headers=headers,
    )
    assert webhook_created.status_code == 200
    webhook_id = webhook_created.json()["id"]

    webhook_list = await api_client.get("/api/v1/integrations/webhooks", headers=headers)
    assert webhook_list.status_code == 200
    assert len(webhook_list.json()) == 1

    webhook_delete = await api_client.delete(f"/api/v1/integrations/webhooks/{webhook_id}", headers=headers)
    assert webhook_delete.status_code == 200


@pytest.mark.asyncio
async def test_sso_exchange_flow(api_client: AsyncClient) -> None:
    exchange = await api_client.post(
        "/api/v1/auth/sso/exchange",
        json={
            "provider": "azure-ad",
            "email": f"enterprise-{uuid4().hex}@example.com",
            "external_subject": f"aad-{uuid4().hex}",
        },
    )
    assert exchange.status_code == 200
    payload = exchange.json()
    assert payload["token_type"] == "bearer"
    assert "access_token" in payload
    assert "refresh_token" in payload


@pytest.mark.asyncio
async def test_webhook_delivery_retry_backoff_and_logs(api_client: AsyncClient, monkeypatch: pytest.MonkeyPatch) -> None:
    headers = await _register(api_client, f"phase6-webhook-retry-{uuid4().hex}@example.com")
    _, simulation_id = await _create_project_with_prediction(api_client, headers)

    webhook_created = await api_client.post(
        "/api/v1/integrations/webhooks",
        json={"event_type": "report.completed", "target_url": "https://example.com/hooks/retry"},
        headers=headers,
    )
    assert webhook_created.status_code == 200
    webhook_id = webhook_created.json()["id"]

    state = {"count": 0}

    original_post = httpx.AsyncClient.post

    async def flaky_post(*args, **kwargs):  # type: ignore[no-untyped-def]
        url = ""
        if len(args) >= 2:
            url = str(args[1])
        elif "url" in kwargs:
            url = str(kwargs["url"])

        if "example.com/hooks/retry" not in url:
            return await original_post(*args, **kwargs)

        state["count"] += 1
        if state["count"] < 3:
            raise httpx.ConnectError("Transient network")
        request = httpx.Request("POST", "https://example.com/hooks/retry")
        return httpx.Response(status_code=200, request=request)

    monkeypatch.setattr(httpx.AsyncClient, "post", flaky_post)

    report_created = await api_client.post(
        "/api/v1/reports",
        json={
            "simulation_id": simulation_id,
            "report_uri": "s3://phase6/retry-report.pdf",
            "status": "generated",
            "version": 1,
        },
        headers=headers,
    )
    assert report_created.status_code == 201

    logs = await api_client.get(
        f"/api/v1/integrations/webhooks/deliveries?page=1&page_size=20&webhook_id={webhook_id}",
        headers=headers,
    )
    assert logs.status_code == 200
    payload = logs.json()
    assert payload["total"] >= 1
    item = payload["items"][0]
    assert item["attempt_count"] == 3
    assert item["success"] is True
    assert item["delivered_at"] is not None
