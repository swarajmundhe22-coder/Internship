import base64
import json
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import AuditLogEntity, ConsortiumMembershipEntity, DeckEntity, DossierEntity


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
async def test_phase10_governance_endpoints_and_audit(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    _, admin_token = await _register(api_client, role="admin", prefix="phase10-admin")
    _, engineer_token = await _register(api_client, role="engineer", prefix="phase10-engineer")

    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    engineer_headers = {"Authorization": f"Bearer {engineer_token}"}

    tenant = await api_client.post(
        "/api/v1/tenants",
        json={"org_name": f"Phase10 Org {uuid4().hex[:8]}", "subscription_tier": "professional"},
        headers=admin_headers,
    )
    assert tenant.status_code == 200
    tenant_id = tenant.json()["id"]

    add_user = await api_client.post(
        f"/api/v1/tenants/{tenant_id}/users",
        json={"user_id": _decode_user_id(engineer_token), "role": "admin"},
        headers=admin_headers,
    )
    assert add_user.status_code == 200

    material = await api_client.post(
        "/api/v1/materials",
        json={
            "name": f"P10 Material {uuid4().hex[:8]}",
            "alloy_group": "Ferrous",
            "density_kg_m3": 7850.0,
            "electrochemical_potential_v": -0.61,
        },
        headers=engineer_headers,
    )
    environment = await api_client.post(
        "/api/v1/environment",
        json={
            "profile_name": f"P10 Env {uuid4().hex[:8]}",
            "temperature_c": 25.0,
            "relative_humidity_pct": 79.0,
            "chloride_ppm": 10000.0,
            "ph": 7.3,
            "dissolved_oxygen_mg_l": 6.8,
        },
        headers=engineer_headers,
    )
    simulation = await api_client.post(
        "/api/v1/simulation",
        json={
            "material_id": material.json()["id"],
            "environment_id": environment.json()["id"],
            "exposed_area_m2": 8.5,
            "exposure_time_hours": 650.0,
            "corrosion_rate_mm_per_year": 0.09,
            "estimated_lifespan_years": 13.0,
            "risk_classification": "moderate",
        },
        headers=engineer_headers,
    )
    assert simulation.status_code == 201

    project = await api_client.post(
        "/api/v1/projects",
        json={"name": f"Phase10 Governance Project {uuid4().hex[:6]}"},
        headers=engineer_headers,
    )
    assert project.status_code == 200

    dossier = await api_client.post(
        "/api/v1/dossier/generate",
        json={
            "tenant_id": tenant_id,
            "simulation_id": simulation.json()["id"],
            "format": "json",
            "industry_module": "energy_grid",
        },
        headers=engineer_headers,
    )
    assert dossier.status_code == 200
    assert dossier.json()["status"] == "generated"

    deck = await api_client.post(
        "/api/v1/deck/export",
        json={
            "tenant_id": tenant_id,
            "project_id": project.json()["id"],
            "export_type": "pptx",
        },
        headers=engineer_headers,
    )
    assert deck.status_code == 200
    assert deck.json()["status"] == "exported"

    join = await api_client.post(
        "/api/v1/consortium/manage",
        json={"tenant_id": tenant_id, "action": "join"},
        headers=engineer_headers,
    )
    assert join.status_code == 200
    assert join.json()["tier"] == "global_utility"

    upgrade = await api_client.post(
        "/api/v1/consortium/manage",
        json={"tenant_id": tenant_id, "action": "upgrade"},
        headers=engineer_headers,
    )
    assert upgrade.status_code == 200
    assert upgrade.json()["tier"] == "elite_intelligence_order"

    dashboard = await api_client.get(
        "/api/v1/consortium/dashboard",
        params={"tenant_id": tenant_id},
        headers=engineer_headers,
    )
    assert dashboard.status_code == 200
    assert dashboard.json()["active_dossiers_30d"] >= 1
    assert dashboard.json()["active_decks_30d"] >= 1

    dossier_rows = (
        await db_session.execute(select(DossierEntity).where(DossierEntity.tenant_id == UUID(tenant_id)))
    ).scalars().all()
    assert len(dossier_rows) == 1

    deck_rows = (
        await db_session.execute(select(DeckEntity).where(DeckEntity.tenant_id == UUID(tenant_id)))
    ).scalars().all()
    assert len(deck_rows) == 1

    membership_rows = (
        await db_session.execute(
            select(ConsortiumMembershipEntity).where(ConsortiumMembershipEntity.tenant_id == UUID(tenant_id))
        )
    ).scalars().all()
    assert len(membership_rows) == 1
    assert membership_rows[0].tier == "elite_intelligence_order"

    logs = (
        await db_session.execute(
            select(AuditLogEntity).where(
                AuditLogEntity.tenant_id == UUID(tenant_id),
                AuditLogEntity.event_type.in_(["DOSSIER_GENERATED", "DECK_EXPORTED", "CONSORTIUM_UPDATED"]),
            )
        )
    ).scalars().all()
    assert len(logs) >= 4
    assert all(item.success for item in logs)


@pytest.mark.asyncio
async def test_phase10_tenant_isolation_on_governance_routes(api_client: AsyncClient) -> None:
    _, admin_token = await _register(api_client, role="admin", prefix="phase10-admin-iso")
    _, engineer_token = await _register(api_client, role="engineer", prefix="phase10-engineer-iso")

    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    engineer_headers = {"Authorization": f"Bearer {engineer_token}"}

    tenant_a = await api_client.post(
        "/api/v1/tenants",
        json={"org_name": f"P10 TenantA {uuid4().hex[:8]}", "subscription_tier": "professional"},
        headers=admin_headers,
    )
    tenant_b = await api_client.post(
        "/api/v1/tenants",
        json={"org_name": f"P10 TenantB {uuid4().hex[:8]}", "subscription_tier": "professional"},
        headers=admin_headers,
    )
    assert tenant_a.status_code == 200
    assert tenant_b.status_code == 200

    add_user = await api_client.post(
        f"/api/v1/tenants/{tenant_a.json()['id']}/users",
        json={"user_id": _decode_user_id(engineer_token), "role": "viewer"},
        headers=admin_headers,
    )
    assert add_user.status_code == 200

    blocked = await api_client.post(
        "/api/v1/consortium/manage",
        json={"tenant_id": tenant_b.json()["id"], "action": "join"},
        headers=engineer_headers,
    )
    assert blocked.status_code == 400
    assert "not a member" in blocked.text.lower()


@pytest.mark.asyncio
async def test_phase10_viewer_role_blocked_on_governance_manage_actions(api_client: AsyncClient) -> None:
    _, admin_token = await _register(api_client, role="admin", prefix="phase10-admin-viewer")
    _, viewer_token = await _register(api_client, role="viewer", prefix="phase10-viewer")

    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    viewer_headers = {"Authorization": f"Bearer {viewer_token}"}

    tenant = await api_client.post(
        "/api/v1/tenants",
        json={"org_name": f"P10 ViewerBlock {uuid4().hex[:8]}", "subscription_tier": "professional"},
        headers=admin_headers,
    )
    assert tenant.status_code == 200
    tenant_id = tenant.json()["id"]

    add_user = await api_client.post(
        f"/api/v1/tenants/{tenant_id}/users",
        json={"user_id": _decode_user_id(viewer_token), "role": "viewer"},
        headers=admin_headers,
    )
    assert add_user.status_code == 200

    dossier_blocked = await api_client.post(
        "/api/v1/dossier/generate",
        json={
            "tenant_id": tenant_id,
            "simulation_id": str(uuid4()),
            "format": "pdf",
            "industry_module": "energy_grid",
        },
        headers=viewer_headers,
    )
    assert dossier_blocked.status_code == 403

    deck_blocked = await api_client.post(
        "/api/v1/deck/export",
        json={"tenant_id": tenant_id, "project_id": str(uuid4()), "export_type": "pptx"},
        headers=viewer_headers,
    )
    assert deck_blocked.status_code == 403

    consortium_blocked = await api_client.post(
        "/api/v1/consortium/manage",
        json={"tenant_id": tenant_id, "action": "join"},
        headers=viewer_headers,
    )
    assert consortium_blocked.status_code == 403
