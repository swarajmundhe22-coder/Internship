import pytest
from httpx import AsyncClient
from uuid import uuid4


async def _register_headers(api_client: AsyncClient, prefix: str, role: str = "engineer") -> dict[str, str]:
    response = await api_client.post(
        "/api/v1/auth/register",
        json={
            "email": f"{prefix}-{uuid4().hex}@example.com",
            "password": "StrongPass123",
            "role": role,
        },
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def _create_project_with_simulation(api_client: AsyncClient, headers: dict[str, str]) -> tuple[str, str]:
    project_response = await api_client.post(
        "/api/v1/projects",
        json={"name": "Prediction Workspace"},
        headers=headers,
    )
    assert project_response.status_code == 200
    project_id = project_response.json()["id"]

    material_response = await api_client.post(
        "/api/v1/materials",
        json={
            "name": f"Prediction Steel {uuid4().hex[:8]}",
            "alloy_group": "Ferrous",
            "density_kg_m3": 7850.0,
            "electrochemical_potential_v": -0.61,
        },
        headers=headers,
    )
    assert material_response.status_code == 201

    environment_response = await api_client.post(
        "/api/v1/environment",
        json={
            "profile_name": f"Prediction Marine {uuid4().hex[:8]}",
            "temperature_c": 26.0,
            "relative_humidity_pct": 87.0,
            "chloride_ppm": 18000.0,
            "ph": 7.8,
            "dissolved_oxygen_mg_l": 7.2,
        },
        headers=headers,
    )
    assert environment_response.status_code == 201

    simulation_response = await api_client.post(
        "/api/v1/simulation",
        json={
            "material_id": material_response.json()["id"],
            "environment_id": environment_response.json()["id"],
            "exposed_area_m2": 14.0,
            "exposure_time_hours": 1600.0,
            "corrosion_rate_mm_per_year": 0.13,
            "estimated_lifespan_years": 7.5,
            "risk_classification": "high",
        },
        headers=headers,
    )
    assert simulation_response.status_code == 201
    simulation_id = simulation_response.json()["id"]

    attach_response = await api_client.post(
        f"/api/v1/projects/{project_id}/simulations/{simulation_id}",
        headers=headers,
    )
    assert attach_response.status_code == 200

    return project_id, simulation_id


@pytest.mark.asyncio
async def test_project_prediction_generate_and_list(api_client: AsyncClient) -> None:
    headers = await _register_headers(api_client, "prediction-owner")
    project_id, simulation_id = await _create_project_with_simulation(api_client, headers)

    generate = await api_client.post(
        f"/api/v1/projects/{project_id}/predict",
        json={"simulation_id": simulation_id, "horizon_hours": 240, "step_hours": 24},
        headers=headers,
    )
    assert generate.status_code == 200
    generated_payload = generate.json()
    assert generated_payload["project_id"] == project_id
    assert generated_payload["simulation_id"] == simulation_id
    assert generated_payload["model_name"] == "trend-v1"
    assert len(generated_payload["timeline"]) == 11

    listing = await api_client.get(
        f"/api/v1/projects/{project_id}/predictions?page=1&page_size=10&simulation_id={simulation_id}",
        headers=headers,
    )
    assert listing.status_code == 200
    payload = listing.json()
    assert payload["total"] == 1
    assert len(payload["items"]) == 1
    assert payload["items"][0]["id"] == generated_payload["id"]


@pytest.mark.asyncio
async def test_project_prediction_requires_project_simulation_association(api_client: AsyncClient) -> None:
    headers = await _register_headers(api_client, "prediction-association")
    project_id, _ = await _create_project_with_simulation(api_client, headers)

    material_response = await api_client.post(
        "/api/v1/materials",
        json={
            "name": f"Detached Steel {uuid4().hex[:8]}",
            "alloy_group": "Ferrous",
            "density_kg_m3": 7850.0,
            "electrochemical_potential_v": -0.61,
        },
        headers=headers,
    )
    environment_response = await api_client.post(
        "/api/v1/environment",
        json={
            "profile_name": f"Detached Env {uuid4().hex[:8]}",
            "temperature_c": 25.0,
            "relative_humidity_pct": 70.0,
            "chloride_ppm": 250.0,
            "ph": 6.8,
            "dissolved_oxygen_mg_l": 6.5,
        },
        headers=headers,
    )
    detached_simulation = await api_client.post(
        "/api/v1/simulation",
        json={
            "material_id": material_response.json()["id"],
            "environment_id": environment_response.json()["id"],
            "exposed_area_m2": 12.0,
            "exposure_time_hours": 900.0,
            "corrosion_rate_mm_per_year": 0.05,
            "estimated_lifespan_years": 18.0,
            "risk_classification": "moderate",
        },
        headers=headers,
    )
    assert detached_simulation.status_code == 201

    generate = await api_client.post(
        f"/api/v1/projects/{project_id}/predict",
        json={"simulation_id": detached_simulation.json()["id"]},
        headers=headers,
    )
    assert generate.status_code == 404


@pytest.mark.asyncio
async def test_project_prediction_non_owner_cannot_list(api_client: AsyncClient) -> None:
    owner_headers = await _register_headers(api_client, "prediction-owner-only")
    project_id, _ = await _create_project_with_simulation(api_client, owner_headers)

    viewer_headers = await _register_headers(api_client, "prediction-viewer", role="viewer")
    unauthorized = await api_client.get(f"/api/v1/projects/{project_id}/predictions", headers=viewer_headers)
    assert unauthorized.status_code == 404
