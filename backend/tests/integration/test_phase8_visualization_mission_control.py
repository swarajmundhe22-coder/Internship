import base64
import json
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import AuditLogEntity, VisualizationEntity


async def _register(api_client: AsyncClient, *, role: str, prefix: str) -> tuple[str, str]:
    email = f"{prefix}-{uuid4().hex}@example.com"
    response = await api_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "StrongPass123", "role": role},
    )
    assert response.status_code == 200
    return email, response.json()["access_token"]


def _decode_user_id(token: str) -> str:
    payload = token.split(".")[1]
    padded = payload + "=" * (-len(payload) % 4)
    return json.loads(base64.urlsafe_b64decode(padded.encode("utf-8")).decode("utf-8"))["sub"]


@pytest.mark.asyncio
async def test_phase8_visualization_flow_and_audit(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    _, admin_token = await _register(api_client, role="admin", prefix="phase8-admin")
    _, engineer_token = await _register(api_client, role="engineer", prefix="phase8-engineer")

    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    engineer_headers = {"Authorization": f"Bearer {engineer_token}"}

    create_tenant = await api_client.post(
        "/api/v1/tenants",
        json={"org_name": f"Phase8 Org {uuid4().hex[:8]}", "subscription_tier": "professional"},
        headers=admin_headers,
    )
    assert create_tenant.status_code == 200
    tenant_id = create_tenant.json()["id"]

    link_member = await api_client.post(
        f"/api/v1/tenants/{tenant_id}/users",
        json={"user_id": _decode_user_id(engineer_token), "role": "admin"},
        headers=admin_headers,
    )
    assert link_member.status_code == 200

    material = await api_client.post(
        "/api/v1/materials",
        json={
            "name": f"P8 Material {uuid4().hex[:8]}",
            "alloy_group": "Ferrous",
            "density_kg_m3": 7850.0,
            "electrochemical_potential_v": -0.61,
        },
        headers=engineer_headers,
    )
    environment = await api_client.post(
        "/api/v1/environment",
        json={
            "profile_name": f"P8 Env {uuid4().hex[:8]}",
            "temperature_c": 22.0,
            "relative_humidity_pct": 78.0,
            "chloride_ppm": 9000.0,
            "ph": 7.1,
            "dissolved_oxygen_mg_l": 6.5,
        },
        headers=engineer_headers,
    )

    create_simulation = await api_client.post(
        "/api/v1/simulation",
        json={
            "material_id": material.json()["id"],
            "environment_id": environment.json()["id"],
            "exposed_area_m2": 9.5,
            "exposure_time_hours": 720.0,
            "corrosion_rate_mm_per_year": 0.08,
            "estimated_lifespan_years": 15.0,
            "accuracy_score": 0.97,
            "risk_classification": "moderate",
        },
        headers=engineer_headers,
    )
    assert create_simulation.status_code == 201
    simulation_id = create_simulation.json()["id"]

    auto_twin_rows = (
        await db_session.execute(
            select(VisualizationEntity).where(
                VisualizationEntity.simulation_id == UUID(simulation_id),
                VisualizationEntity.mode == "twin",
            )
        )
    ).scalars().all()
    assert len(auto_twin_rows) >= 1

    manual_twin = await api_client.post(
        "/api/v1/visualization/twin",
        json={"simulation_id": simulation_id, "tenant_id": tenant_id, "mode": "twin"},
        headers=engineer_headers,
    )
    assert manual_twin.status_code == 200
    assert manual_twin.json()["overlay_accuracy"] >= 0.95

    playback = await api_client.post(
        "/api/v1/visualization/playback",
        json={"simulation_id": simulation_id, "tenant_id": tenant_id, "mode": "vr"},
        headers=engineer_headers,
    )
    assert playback.status_code == 200
    assert playback.json()["status"] == "playback_ready"

    export = await api_client.post(
        "/api/v1/visualization/export",
        json={
            "simulation_id": simulation_id,
            "tenant_id": tenant_id,
            "mode": "vr",
            "file_type": "mp4",
        },
        headers=engineer_headers,
    )
    assert export.status_code == 200
    assert export.json()["status"] == "exported"

    logs = (
        await db_session.execute(
            select(AuditLogEntity).where(
                AuditLogEntity.event_type.in_(
                    [
                        "VISUALIZATION_GENERATED",
                        "PLAYBACK_INITIATED",
                        "EXPORT_COMPLETED",
                    ]
                )
            )
        )
    ).scalars().all()

    expected_events = {
        "VISUALIZATION_GENERATED",
        "PLAYBACK_INITIATED",
        "EXPORT_COMPLETED",
    }
    matched_events: set[str] = set()
    for item in logs:
        detail = str(item.detail or "")
        if item.success and tenant_id in detail and simulation_id in detail:
            matched_events.add(item.event_type)

    assert expected_events.issubset(matched_events)


@pytest.mark.asyncio
async def test_phase8_visualization_tenant_isolation(api_client: AsyncClient) -> None:
    _, admin_token = await _register(api_client, role="admin", prefix="phase8-admin-iso")
    _, engineer_token = await _register(api_client, role="engineer", prefix="phase8-engineer-iso")

    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    engineer_headers = {"Authorization": f"Bearer {engineer_token}"}

    tenant_a = await api_client.post(
        "/api/v1/tenants",
        json={"org_name": f"Phase8 TenantA {uuid4().hex[:8]}", "subscription_tier": "professional"},
        headers=admin_headers,
    )
    tenant_b = await api_client.post(
        "/api/v1/tenants",
        json={"org_name": f"Phase8 TenantB {uuid4().hex[:8]}", "subscription_tier": "professional"},
        headers=admin_headers,
    )
    assert tenant_a.status_code == 200
    assert tenant_b.status_code == 200

    add_member = await api_client.post(
        f"/api/v1/tenants/{tenant_a.json()['id']}/users",
        json={"user_id": _decode_user_id(engineer_token), "role": "viewer"},
        headers=admin_headers,
    )
    assert add_member.status_code == 200

    material = await api_client.post(
        "/api/v1/materials",
        json={
            "name": f"Iso Material {uuid4().hex[:8]}",
            "alloy_group": "Ferrous",
            "density_kg_m3": 7850.0,
            "electrochemical_potential_v": -0.61,
        },
        headers=engineer_headers,
    )
    environment = await api_client.post(
        "/api/v1/environment",
        json={
            "profile_name": f"Iso Env {uuid4().hex[:8]}",
            "temperature_c": 23.0,
            "relative_humidity_pct": 80.0,
            "chloride_ppm": 9500.0,
            "ph": 7.0,
            "dissolved_oxygen_mg_l": 6.8,
        },
        headers=engineer_headers,
    )
    simulation = await api_client.post(
        "/api/v1/simulation",
        json={
            "material_id": material.json()["id"],
            "environment_id": environment.json()["id"],
            "exposed_area_m2": 10.0,
            "exposure_time_hours": 600.0,
            "corrosion_rate_mm_per_year": 0.07,
            "estimated_lifespan_years": 16.0,
            "accuracy_score": 0.98,
            "risk_classification": "low",
        },
        headers=engineer_headers,
    )
    assert simulation.status_code == 201

    blocked = await api_client.post(
        "/api/v1/visualization/playback",
        json={
            "simulation_id": simulation.json()["id"],
            "tenant_id": tenant_b.json()["id"],
            "mode": "ar",
        },
        headers=engineer_headers,
    )
    assert blocked.status_code == 400
    assert "not a member" in blocked.text.lower() or "not bound" in blocked.text.lower()
