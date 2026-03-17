from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.services.report_builder_service import ReportBuilderService


async def _register_headers(api_client: AsyncClient, email: str = "report-hardening@example.com") -> dict[str, str]:
    register = await api_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "StrongPass123", "role": "engineer"},
    )
    assert register.status_code == 200
    return {"Authorization": f"Bearer {register.json()['access_token']}"}


async def _create_simulation(api_client: AsyncClient, headers: dict[str, str]) -> str:
    material = await api_client.post(
        "/api/v1/materials",
        json={
            "name": "Cache Material",
            "alloy_group": "Ferrous",
            "density_kg_m3": 7850.0,
            "electrochemical_potential_v": -0.62,
        },
        headers=headers,
    )
    assert material.status_code == 201

    environment = await api_client.post(
        "/api/v1/environment",
        json={
            "profile_name": "Cache Environment",
            "temperature_c": 30.0,
            "relative_humidity_pct": 80.0,
            "chloride_ppm": 300.0,
            "ph": 7.1,
            "dissolved_oxygen_mg_l": 6.2,
        },
        headers=headers,
    )
    assert environment.status_code == 201

    sim = await api_client.post(
        "/api/v1/simulation",
        json={
            "material_id": material.json()["id"],
            "environment_id": environment.json()["id"],
            "exposed_area_m2": 9.0,
            "exposure_time_hours": 400.0,
            "corrosion_rate_mm_per_year": 0.09,
            "estimated_lifespan_years": 10.4,
            "risk_classification": "moderate",
        },
        headers=headers,
    )
    assert sim.status_code == 201
    return sim.json()["id"]


@pytest.mark.asyncio
async def test_generate_report_response_is_cached(api_client: AsyncClient) -> None:
    ReportBuilderService.clear_cache()
    headers = await _register_headers(api_client, "report-cache@example.com")
    simulation_id = await _create_simulation(api_client, headers)

    first = await api_client.post("/api/v1/reports/generate", json={"simulation_id": simulation_id}, headers=headers)
    assert first.status_code == 200

    second = await api_client.post("/api/v1/reports/generate", json={"simulation_id": simulation_id}, headers=headers)
    assert second.status_code == 200

    # Cached response should preserve generated_at while TTL is active.
    assert first.json()["generated_at"] == second.json()["generated_at"]


@pytest.mark.asyncio
async def test_pdf_export_endpoint_returns_pdf_bytes(api_client: AsyncClient) -> None:
    headers = await _register_headers(api_client, "report-pdf@example.com")
    simulation_id = await _create_simulation(api_client, headers)

    report = await api_client.post(
        "/api/v1/reports",
        json={
            "simulation_id": simulation_id,
            "report_uri": "s3://on-looker/reports/hardening.pdf",
            "status": "generated",
            "version": 1,
        },
        headers=headers,
    )
    assert report.status_code == 201

    pdf_response = await api_client.get(f"/api/v1/reports/{report.json()['id']}/pdf", headers=headers)
    assert pdf_response.status_code == 200
    assert pdf_response.headers["content-type"].startswith("application/pdf")
    assert pdf_response.content.startswith(b"%PDF")
