from __future__ import annotations

import time
from uuid import uuid4

import pytest
from httpx import AsyncClient


async def _headers(api_client: AsyncClient) -> dict[str, str]:
    email = f"analytics-{uuid4().hex}@example.com"
    register = await api_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "StrongPass123", "role": "engineer"},
    )
    assert register.status_code == 200
    return {"Authorization": f"Bearer {register.json()['access_token']}"}


@pytest.mark.asyncio
async def test_analytics_endpoints_and_query_performance(api_client: AsyncClient) -> None:
    headers = await _headers(api_client)

    materials = []
    environments = []
    for i in range(4):
        material = await api_client.post(
            "/api/v1/materials",
            json={
                "name": f"Analytics Material {i}",
                "alloy_group": "Ferrous",
                "density_kg_m3": 7800.0 + i,
                "electrochemical_potential_v": -0.6,
            },
            headers=headers,
        )
        assert material.status_code == 201
        materials.append(material.json())

        environment = await api_client.post(
            "/api/v1/environment",
            json={
                "profile_name": f"Analytics Env {i}",
                "temperature_c": 20 + i,
                "relative_humidity_pct": 55 + i,
                "chloride_ppm": 100 + i,
                "ph": 7.0,
                "dissolved_oxygen_mg_l": 6.0,
            },
            headers=headers,
        )
        assert environment.status_code == 201
        environments.append(environment.json())

    for i in range(120):
        material = materials[i % len(materials)]
        environment = environments[i % len(environments)]
        risk = "high" if i % 5 == 0 else "moderate"
        simulation = await api_client.post(
            "/api/v1/simulation",
            json={
                "material_id": material["id"],
                "environment_id": environment["id"],
                "exposed_area_m2": 8.0 + i,
                "exposure_time_hours": 100.0 + i,
                "corrosion_rate_mm_per_year": 0.02 + (i * 0.0005),
                "estimated_lifespan_years": 8.0,
                "risk_classification": risk,
            },
            headers=headers,
        )
        assert simulation.status_code == 201

        if i % 3 == 0:
            report = await api_client.post(
                "/api/v1/reports",
                json={
                    "simulation_id": simulation.json()["id"],
                    "report_uri": f"s3://analytics/reports/{i}.pdf",
                    "status": "generated",
                    "version": 1,
                },
                headers=headers,
            )
            assert report.status_code == 201

    start = time.perf_counter()
    summary = await api_client.get("/api/v1/analytics/summary", headers=headers)
    material_usage = await api_client.get("/api/v1/analytics/material-usage", headers=headers)
    environment_usage = await api_client.get("/api/v1/analytics/environment-usage", headers=headers)
    risk_distribution = await api_client.get("/api/v1/analytics/risk-distribution", headers=headers)
    over_time = await api_client.get("/api/v1/analytics/simulations-over-time", headers=headers)
    elapsed = time.perf_counter() - start

    assert summary.status_code == 200
    assert material_usage.status_code == 200
    assert environment_usage.status_code == 200
    assert risk_distribution.status_code == 200
    assert over_time.status_code == 200

    assert summary.json()["total_simulations"] >= 120
    assert summary.json()["total_reports"] >= 40
    assert len(material_usage.json()) >= 1
    assert len(environment_usage.json()) >= 1
    assert len(risk_distribution.json()) >= 1
    assert len(over_time.json()) >= 1

    # Performance guardrail for indexed aggregate calls in local test DB.
    assert elapsed < 1.5
