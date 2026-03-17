from __future__ import annotations

import pytest
from httpx import AsyncClient


async def _register(api_client: AsyncClient, email: str, role: str) -> dict[str, str]:
    response = await api_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "StrongPass123", "role": role},
    )
    assert response.status_code == 200
    return {
        "access_token": response.json()["access_token"],
        "refresh_token": response.json()["refresh_token"],
    }


@pytest.mark.asyncio
async def test_admin_can_query_audit_logs_with_filters(api_client: AsyncClient) -> None:
    admin = await _register(api_client, "audit-admin@example.com", "admin")
    admin_headers = {"Authorization": f"Bearer {admin['access_token']}"}

    user = await _register(api_client, "audit-user@example.com", "engineer")

    # Produce additional audit events for filter checks.
    login = await api_client.post(
        "/api/v1/auth/login",
        json={"email": "audit-user@example.com", "password": "StrongPass123"},
    )
    assert login.status_code == 200

    refresh = await api_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": user["refresh_token"]},
    )
    assert refresh.status_code == 200

    all_logs = await api_client.get("/api/v1/audit-logs?page=1&page_size=100", headers=admin_headers)
    assert all_logs.status_code == 200
    payload = all_logs.json()
    assert payload["total"] >= 4
    assert len(payload["items"]) >= 4

    login_logs = await api_client.get(
        "/api/v1/audit-logs?event_type=auth.login&page=1&page_size=20",
        headers=admin_headers,
    )
    assert login_logs.status_code == 200
    assert all(item["event_type"] == "auth.login" for item in login_logs.json()["items"])

    user_logs = await api_client.get(
        "/api/v1/audit-logs?user_email=audit-user@example.com&page=1&page_size=50",
        headers=admin_headers,
    )
    assert user_logs.status_code == 200
    assert any(item["user_email"] == "audit-user@example.com" for item in user_logs.json()["items"])


@pytest.mark.asyncio
async def test_non_admin_cannot_query_audit_logs(api_client: AsyncClient) -> None:
    engineer = await _register(api_client, "audit-engineer@example.com", "engineer")
    engineer_headers = {"Authorization": f"Bearer {engineer['access_token']}"}

    forbidden = await api_client.get("/api/v1/audit-logs", headers=engineer_headers)
    assert forbidden.status_code == 403
