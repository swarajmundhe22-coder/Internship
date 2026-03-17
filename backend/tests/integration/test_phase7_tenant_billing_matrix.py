import hashlib
import hmac
import base64
import json
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.database.models import ProjectEntity, TenantSimulationEntity


async def _register(api_client: AsyncClient, *, role: str, prefix: str) -> tuple[str, str]:
    email = f"{prefix}-{uuid4().hex}@example.com"
    response = await api_client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "StrongPass123", "role": role},
    )
    assert response.status_code == 200
    token = response.json()["access_token"]
    return email, token


@pytest.mark.asyncio
async def test_tenant_admin_crud_and_auto_binding(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    _, admin_token = await _register(api_client, role="admin", prefix="tenant-admin")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    created_tenant = await api_client.post(
        "/api/v1/tenants",
        json={"org_name": f"North Field {uuid4().hex[:8]}", "subscription_tier": "professional"},
        headers=admin_headers,
    )
    assert created_tenant.status_code == 200
    tenant = created_tenant.json()

    _, engineer_token = await _register(api_client, role="engineer", prefix="tenant-engineer")
    engineer_headers = {"Authorization": f"Bearer {engineer_token}"}

    decode_payload = engineer_token.split(".")[1]
    padded = decode_payload + "=" * (-len(decode_payload) % 4)
    engineer_user_id = json.loads(base64.urlsafe_b64decode(padded.encode("utf-8")).decode("utf-8"))["sub"]

    add_member = await api_client.post(
        f"/api/v1/tenants/{tenant['id']}/users",
        json={"user_id": engineer_user_id, "role": "admin"},
        headers=admin_headers,
    )
    assert add_member.status_code == 200

    material = await api_client.post(
        "/api/v1/materials",
        json={
            "name": f"Tenant Material {uuid4().hex[:8]}",
            "alloy_group": "Ferrous",
            "density_kg_m3": 7850.0,
            "electrochemical_potential_v": -0.61,
        },
        headers=engineer_headers,
    )
    environment = await api_client.post(
        "/api/v1/environment",
        json={
            "profile_name": f"Tenant Env {uuid4().hex[:8]}",
            "temperature_c": 24.0,
            "relative_humidity_pct": 82.0,
            "chloride_ppm": 12000.0,
            "ph": 7.2,
            "dissolved_oxygen_mg_l": 7.0,
        },
        headers=engineer_headers,
    )
    simulation = await api_client.post(
        "/api/v1/simulation",
        json={
            "material_id": material.json()["id"],
            "environment_id": environment.json()["id"],
            "exposed_area_m2": 11.0,
            "exposure_time_hours": 850.0,
            "corrosion_rate_mm_per_year": 0.09,
            "estimated_lifespan_years": 12.5,
            "risk_classification": "moderate",
        },
        headers=engineer_headers,
    )
    assert simulation.status_code == 201

    project = await api_client.post(
        "/api/v1/projects",
        json={"name": "Tenant Bound Project"},
        headers=engineer_headers,
    )
    assert project.status_code == 200

    tenant_sim_links = (
        await db_session.execute(
            select(TenantSimulationEntity).where(
                TenantSimulationEntity.simulation_id == UUID(simulation.json()["id"])
            )
        )
    ).scalars().all()
    assert len(tenant_sim_links) == 1
    assert str(tenant_sim_links[0].tenant_id) == tenant["id"]

    project_row = (
        await db_session.execute(select(ProjectEntity).where(ProjectEntity.id == UUID(project.json()["id"])))
    ).scalar_one()
    assert project_row.tenant_id is not None
    assert str(project_row.tenant_id) == tenant["id"]


@pytest.mark.asyncio
async def test_paypal_event_matrix_with_audit_trails(api_client: AsyncClient) -> None:
    _, admin_token = await _register(api_client, role="admin", prefix="billing-admin")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    create_tenant = await api_client.post(
        "/api/v1/tenants",
        json={"org_name": f"Billing Matrix {uuid4().hex[:8]}", "subscription_tier": "professional"},
        headers=admin_headers,
    )
    assert create_tenant.status_code == 200
    tenant_id = create_tenant.json()["id"]

    settings = get_settings()
    previous_secret = settings.paypal_webhook_secret
    settings.paypal_webhook_secret = "phase7-matrix-secret"

    async def send_event(event_type: str, tier: str) -> None:
        event = {
            "event_type": event_type,
            "resource": {
                "custom_id": tenant_id,
                "subscription_tier": tier,
            },
        }
        body = json.dumps(event, separators=(",", ":"), sort_keys=True).encode("utf-8")
        signature = hmac.new(settings.paypal_webhook_secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
        response = await api_client.post(
            "/api/v1/billing/webhook",
            json=event,
            headers={"X-PayPal-Signature": signature},
        )
        assert response.status_code == 200

    try:
        await send_event("BILLING.SUBSCRIPTION.CREATED", "professional")
        await send_event("BILLING.SUBSCRIPTION.SUSPENDED", "professional")
        await send_event("BILLING.SUBSCRIPTION.ACTIVATED", "enterprise_elite")
        await send_event("BILLING.SUBSCRIPTION.CANCELLED", "enterprise_elite")

        logs_response = await api_client.get(
            "/api/v1/audit-logs?event_type=billing.paypal.billing.subscription.cancelled&page=1&page_size=50",
            headers=admin_headers,
        )
        assert logs_response.status_code == 200
        assert logs_response.json()["total"] >= 1

        all_logs = await api_client.get(
            "/api/v1/audit-logs?page=1&page_size=200",
            headers=admin_headers,
        )
        assert all_logs.status_code == 200
        event_types = {item["event_type"] for item in all_logs.json()["items"]}
        assert "billing.paypal.billing.subscription.created" in event_types
        assert "billing.paypal.billing.subscription.suspended" in event_types
        assert "billing.paypal.billing.subscription.activated" in event_types
        assert "billing.paypal.billing.subscription.cancelled" in event_types
    finally:
        settings.paypal_webhook_secret = previous_secret
