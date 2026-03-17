import pytest
from httpx import AsyncClient
from uuid import uuid4


async def _auth_headers(api_client: AsyncClient, prefix: str = "crud") -> dict[str, str]:
    response = await api_client.post(
        "/api/v1/auth/register",
        json={"email": f"{prefix}-{uuid4().hex}@example.com", "password": "StrongPass123"},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_materials_api_crud(api_client: AsyncClient) -> None:
    headers = await _auth_headers(api_client, "materials")
    create_payload = {
        "name": "API Carbon Steel",
        "alloy_group": "Ferrous",
        "density_kg_m3": 7850.0,
        "electrochemical_potential_v": -0.61,
    }
    create_response = await api_client.post("/api/v1/materials", json=create_payload, headers=headers)
    assert create_response.status_code == 201
    created = create_response.json()

    get_response = await api_client.get(f"/api/v1/materials/{created['id']}", headers=headers)
    assert get_response.status_code == 200

    list_response = await api_client.get("/api/v1/materials", headers=headers)
    assert list_response.status_code == 200
    list_payload = list_response.json()
    assert list_payload["total"] == 1
    assert len(list_payload["items"]) == 1

    update_response = await api_client.put(
        f"/api/v1/materials/{created['id']}",
        json={"electrochemical_potential_v": -0.55},
        headers=headers,
    )
    assert update_response.status_code == 200
    assert update_response.json()["electrochemical_potential_v"] == pytest.approx(-0.55)

    delete_response = await api_client.delete(f"/api/v1/materials/{created['id']}", headers=headers)
    assert delete_response.status_code == 204


@pytest.mark.asyncio
async def test_environment_api_crud(api_client: AsyncClient) -> None:
    headers = await _auth_headers(api_client, "environments")
    create_payload = {
        "profile_name": "Atmospheric Test",
        "temperature_c": 26.0,
        "relative_humidity_pct": 60.0,
        "chloride_ppm": 20.0,
        "ph": 7.0,
        "dissolved_oxygen_mg_l": 8.1,
    }
    create_response = await api_client.post("/api/v1/environment", json=create_payload, headers=headers)
    assert create_response.status_code == 201
    created = create_response.json()

    get_response = await api_client.get(f"/api/v1/environment/{created['id']}", headers=headers)
    assert get_response.status_code == 200

    list_response = await api_client.get("/api/v1/environment", headers=headers)
    assert list_response.status_code == 200
    list_payload = list_response.json()
    assert list_payload["total"] == 1
    assert len(list_payload["items"]) == 1

    update_response = await api_client.put(
        f"/api/v1/environment/{created['id']}",
        json={"ph": 6.8},
        headers=headers,
    )
    assert update_response.status_code == 200
    assert update_response.json()["ph"] == pytest.approx(6.8)

    delete_response = await api_client.delete(f"/api/v1/environment/{created['id']}", headers=headers)
    assert delete_response.status_code == 204


@pytest.mark.asyncio
async def test_simulation_and_report_apis(api_client: AsyncClient) -> None:
    headers = await _auth_headers(api_client, "sim-reports")
    material_response = await api_client.post(
        "/api/v1/materials",
        json={
            "name": "API Stainless",
            "alloy_group": "Ferrous",
            "density_kg_m3": 8000.0,
            "electrochemical_potential_v": -0.1,
        },
        headers=headers,
    )
    environment_response = await api_client.post(
        "/api/v1/environment",
        json={
            "profile_name": "Marine API",
            "temperature_c": 24.0,
            "relative_humidity_pct": 90.0,
            "chloride_ppm": 19000.0,
            "ph": 8.0,
            "dissolved_oxygen_mg_l": 7.6,
        },
        headers=headers,
    )

    material = material_response.json()
    environment = environment_response.json()

    simulation_create = await api_client.post(
        "/api/v1/simulation",
        json={
            "material_id": material["id"],
            "environment_id": environment["id"],
            "exposed_area_m2": 20.0,
            "exposure_time_hours": 1440.0,
            "corrosion_rate_mm_per_year": 0.11,
            "estimated_lifespan_years": 12.0,
            "risk_classification": "high",
        },
        headers=headers,
    )
    assert simulation_create.status_code == 201
    simulation = simulation_create.json()

    simulation_get = await api_client.get(f"/api/v1/simulation/{simulation['id']}", headers=headers)
    assert simulation_get.status_code == 200

    simulation_list = await api_client.get(
        f"/api/v1/simulation?material_id={material['id']}&environment_id={environment['id']}&risk_level=high&page=1&page_size=10",
        headers=headers,
    )
    assert simulation_list.status_code == 200
    simulation_list_payload = simulation_list.json()
    assert simulation_list_payload["total"] == 1

    simulation_predict = await api_client.post(
        "/api/v1/simulation/predict",
        json={
            "material": material,
            "environment": {
                "temperature_c": environment["temperature_c"],
                "relative_humidity_pct": environment["relative_humidity_pct"],
                "chloride_ppm": environment["chloride_ppm"],
                "ph": environment["ph"],
                "dissolved_oxygen_mg_l": environment["dissolved_oxygen_mg_l"],
            },
            "exposed_area_m2": 20.0,
            "exposure_time_hours": 1440.0,
        },
        headers=headers,
    )
    assert simulation_predict.status_code == 200
    prediction_payload = simulation_predict.json()
    assert prediction_payload["corrosion_rate_mm_per_year"] >= 0

    simulation_alias_predict = await api_client.post(
        "/api/v1/simulation/simulate",
        json={
            "material": material,
            "environment": {
                "temperature_c": environment["temperature_c"],
                "relative_humidity_pct": environment["relative_humidity_pct"],
                "chloride_ppm": environment["chloride_ppm"],
                "ph": environment["ph"],
                "dissolved_oxygen_mg_l": environment["dissolved_oxygen_mg_l"],
            },
            "exposed_area_m2": 25.0,
            "exposure_time_hours": 1000.0,
        },
        headers=headers,
    )
    assert simulation_alias_predict.status_code == 200

    report_create = await api_client.post(
        "/api/v1/reports",
        json={
            "simulation_id": simulation["id"],
            "report_uri": "s3://on-looker/reports/api-report.pdf",
            "status": "generated",
            "version": 1,
        },
        headers=headers,
    )
    assert report_create.status_code == 201
    report = report_create.json()

    report_get = await api_client.get(f"/api/v1/reports/{report['id']}", headers=headers)
    assert report_get.status_code == 200

    report_update = await api_client.put(
        f"/api/v1/reports/{report['id']}",
        json={"expected_version": report["version"], "status": "archived"},
        headers=headers,
    )
    assert report_update.status_code == 200
    assert report_update.json()["status"] == "archived"

    report_update_stale = await api_client.put(
        f"/api/v1/reports/{report['id']}",
        json={"expected_version": report["version"], "status": "generated"},
        headers=headers,
    )
    assert report_update_stale.status_code == 409

    simulation_update = await api_client.put(
        f"/api/v1/simulation/{simulation['id']}",
        json={"expected_version": simulation["version"], "risk_classification": "moderate"},
        headers=headers,
    )
    assert simulation_update.status_code == 200

    simulation_update_stale = await api_client.put(
        f"/api/v1/simulation/{simulation['id']}",
        json={"expected_version": simulation["version"], "risk_classification": "critical"},
        headers=headers,
    )
    assert simulation_update_stale.status_code == 409

    report_list = await api_client.get(f"/api/v1/reports?simulation_id={simulation['id']}&page=1&page_size=10", headers=headers)
    assert report_list.status_code == 200
    report_list_payload = report_list.json()
    assert report_list_payload["total"] == 1

    report_delete = await api_client.delete(f"/api/v1/reports/{report['id']}", headers=headers)
    assert report_delete.status_code == 204

    simulation_delete = await api_client.delete(f"/api/v1/simulation/{simulation['id']}", headers=headers)
    assert simulation_delete.status_code == 204
