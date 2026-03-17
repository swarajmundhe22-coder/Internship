from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import AuditLogEntity


@pytest.mark.asyncio
async def test_auth_audit_logs_register_login_refresh_logout(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    register = await api_client.post(
        "/api/v1/auth/register",
        json={"email": "audit-log@example.com", "password": "StrongPass123", "role": "engineer"},
    )
    assert register.status_code == 200
    refresh_token = register.json()["refresh_token"]

    login = await api_client.post(
        "/api/v1/auth/login",
        json={"email": "audit-log@example.com", "password": "StrongPass123"},
    )
    assert login.status_code == 200

    refreshed = await api_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refreshed.status_code == 200

    logout = await api_client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refreshed.json()["refresh_token"]},
    )
    assert logout.status_code == 200

    events = (
        await db_session.execute(select(AuditLogEntity).order_by(AuditLogEntity.created_at.asc()))
    ).scalars().all()
    event_types = [event.event_type for event in events]

    assert "auth.register" in event_types
    assert "auth.login" in event_types
    assert "auth.refresh" in event_types
    assert "auth.logout" in event_types
    assert all(event.success for event in events)


@pytest.mark.asyncio
async def test_auth_audit_logs_failed_login(api_client: AsyncClient, db_session: AsyncSession) -> None:
    failed = await api_client.post(
        "/api/v1/auth/login",
        json={"email": "missing-user@example.com", "password": "StrongPass123"},
    )
    assert failed.status_code == 401

    events = (
        await db_session.execute(
            select(AuditLogEntity).where(AuditLogEntity.event_type == "auth.login").order_by(AuditLogEntity.created_at.desc())
        )
    ).scalars().all()

    assert len(events) >= 1
    assert events[0].success is False
    assert events[0].detail is not None
