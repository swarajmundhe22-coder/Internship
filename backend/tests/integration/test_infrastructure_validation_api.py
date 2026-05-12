from __future__ import annotations

from uuid import uuid4

from httpx import AsyncClient


def _request_payload(country: str, city: str, state: str, county: str, lat: float, lon: float) -> dict[str, object]:
    return {
        "location": {
            "country_code": country,
            "city": city,
            "state": state,
            "county": county,
            "latitude": lat,
            "longitude": lon,
        },
        "loads": {
            "dead_load_kN": 550,
            "live_load_kN": 180,
            "snow_load_kN": 10,
            "thermal_load_kN": 28,
        },
        "capacities": {
            "ultimate_capacity_kN": 2400,
            "serviceability_capacity_kN": 1900,
            "member_area_mm2": 24000,
            "allowable_stress_mpa": 230,
        },
        "design_codes": ["ASCE7-22", "EUROCODE-IN-NA", "GB-50009-50011-50017"],
        "material_system": "steel",
        "exposure_category": "C",
        "structure_height_ft": 120,
        "effective_projected_area_m2": 140,
    }


async def _register_engineer_headers(api_client: AsyncClient) -> dict[str, str]:
    register = await api_client.post(
        "/api/v1/auth/register",
        json={
            "email": f"infra-{uuid4().hex[:8]}@example.com",
            "password": "StrongPass123",
            "role": "engineer",
        },
    )
    assert register.status_code == 200
    return {"Authorization": f"Bearer {register.json()['access_token']}"}


async def test_infrastructure_validate_miami(api_client: AsyncClient) -> None:
    headers = await _register_engineer_headers(api_client)
    response = await api_client.post(
        "/api/v1/infrastructure/validate",
        headers=headers,
        json=_request_payload("US", "Miami", "Florida", "Miami-Dade", 25.7617, -80.1918),
    )
    assert response.status_code == 200

    payload = response.json()
    assert payload["overall_passes"] in (True, False)
    assert payload["weather"]["basic_wind_speed_mph"] == 175
    assert len(payload["code_results"]) == 3


async def test_infrastructure_validate_chennai(api_client: AsyncClient) -> None:
    headers = await _register_engineer_headers(api_client)
    response = await api_client.post(
        "/api/v1/infrastructure/validate",
        headers=headers,
        json=_request_payload("IN", "Chennai", "Tamil Nadu", "Chennai", 13.0827, 80.2707),
    )
    assert response.status_code == 200

    payload = response.json()
    assert payload["weather"]["seismic_zone"] in [2, 3, 4, 5]
    assert payload["weather"]["precipitation_intensity_mm_hr"] >= 1


async def test_infrastructure_validate_pdf(api_client: AsyncClient) -> None:
    headers = await _register_engineer_headers(api_client)
    response = await api_client.post(
        "/api/v1/infrastructure/validate/pdf",
        headers=headers,
        json=_request_payload("US", "Miami", "Florida", "Miami-Dade", 25.7617, -80.1918),
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/pdf")
    assert b"%PDF-1.4" in response.content


async def test_infrastructure_hourly_update(api_client: AsyncClient) -> None:
    headers = await _register_engineer_headers(api_client)
    response = await api_client.post(
        "/api/v1/infrastructure/hourly-update",
        headers=headers,
        json={
            "targets": [
                {
                    "country_code": "US",
                    "city": "Miami",
                    "state": "Florida",
                    "county": "Miami-Dade",
                    "latitude": 25.7617,
                    "longitude": -80.1918,
                },
                {
                    "country_code": "IN",
                    "city": "Chennai",
                    "state": "Tamil Nadu",
                    "county": "Chennai",
                    "latitude": 13.0827,
                    "longitude": 80.2707,
                },
            ],
            "exposure_category": "C",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["record_count"] == 2
    assert len(payload["records"]) == 2
