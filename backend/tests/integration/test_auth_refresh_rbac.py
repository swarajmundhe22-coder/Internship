import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_refresh_token_rotation_and_logout(api_client: AsyncClient) -> None:
    register = await api_client.post(
        "/api/v1/auth/register",
        json={"email": "refresh-flow@example.com", "password": "StrongPass123"},
    )
    assert register.status_code == 200
    tokens = register.json()
    assert "refresh_token" in tokens

    refresh = await api_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert refresh.status_code == 200
    rotated = refresh.json()
    assert rotated["access_token"] != tokens["access_token"]
    assert rotated["refresh_token"] != tokens["refresh_token"]

    logout = await api_client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": rotated["refresh_token"]},
    )
    assert logout.status_code == 200

    refresh_after_logout = await api_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": rotated["refresh_token"]},
    )
    assert refresh_after_logout.status_code == 401


@pytest.mark.asyncio
async def test_viewer_role_cannot_mutate_resources(api_client: AsyncClient) -> None:
    viewer_register = await api_client.post(
        "/api/v1/auth/register",
        json={"email": "viewer-role@example.com", "password": "StrongPass123", "role": "viewer"},
    )
    assert viewer_register.status_code == 200
    viewer_headers = {"Authorization": f"Bearer {viewer_register.json()['access_token']}"}

    denied_create = await api_client.post(
        "/api/v1/materials",
        json={
            "name": "Viewer Denied Material",
            "alloy_group": "Ferrous",
            "density_kg_m3": 7850.0,
            "electrochemical_potential_v": -0.61,
        },
        headers=viewer_headers,
    )
    assert denied_create.status_code == 403


@pytest.mark.asyncio
async def test_engineer_role_can_read_and_mutate_resources(api_client: AsyncClient) -> None:
    engineer_register = await api_client.post(
        "/api/v1/auth/register",
        json={"email": "engineer-role@example.com", "password": "StrongPass123", "role": "engineer"},
    )
    assert engineer_register.status_code == 200
    headers = {"Authorization": f"Bearer {engineer_register.json()['access_token']}"}

    created = await api_client.post(
        "/api/v1/materials",
        json={
            "name": "Engineer Allowed Material",
            "alloy_group": "Ferrous",
            "density_kg_m3": 7850.0,
            "electrochemical_potential_v": -0.61,
        },
        headers=headers,
    )
    assert created.status_code == 201

    listed = await api_client.get("/api/v1/materials", headers=headers)
    assert listed.status_code == 200
    assert listed.json()["total"] >= 1
