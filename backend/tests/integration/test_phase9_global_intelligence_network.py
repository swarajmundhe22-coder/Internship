import base64
import json
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import (
    AtlasEntity,
    AuditLogEntity,
    IoTDataEntity,
    MaintenanceScheduleEntity,
    SatelliteDataEntity,
)


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
async def test_phase9_intelligence_flow_with_tenant_bound_audit(
    api_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    _, admin_token = await _register(api_client, role="admin", prefix="phase9-admin")
    _, engineer_token = await _register(api_client, role="engineer", prefix="phase9-engineer")

    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    engineer_headers = {"Authorization": f"Bearer {engineer_token}"}

    create_tenant = await api_client.post(
        "/api/v1/tenants",
        json={"org_name": f"Phase9 Org {uuid4().hex[:8]}", "subscription_tier": "professional"},
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

    iot = await api_client.post(
        "/api/v1/intelligence/iot/ingest",
        json={
            "tenant_id": tenant_id,
            "sensor_id": "sensor-alpha",
            "payload": {"temperature_c": 31.2, "humidity_pct": 82.5},
        },
        headers=engineer_headers,
    )
    assert iot.status_code == 200
    assert iot.json()["status"] == "ingested"

    satellite = await api_client.post(
        "/api/v1/intelligence/satellite/ingest",
        json={"tenant_id": tenant_id, "region": "north-sea", "imagery_source": "sentinel-2"},
        headers=engineer_headers,
    )
    assert satellite.status_code == 200
    assert satellite.json()["status"] == "imagery_ingested"

    atlas_generate = await api_client.post(
        "/api/v1/intelligence/atlas/generate",
        json={"tenant_id": tenant_id, "region": "north-sea", "export_type": "map_snapshot"},
        headers=engineer_headers,
    )
    assert atlas_generate.status_code == 200
    assert atlas_generate.json()["status"] == "generated"
    generate_metadata = atlas_generate.json()["metadata"]
    assert isinstance(generate_metadata.get("overlay_points"), list)
    assert len(generate_metadata["overlay_points"]) >= 1

    atlas_export = await api_client.post(
        "/api/v1/intelligence/atlas/export",
        json={"tenant_id": tenant_id, "region": "north-sea", "export_type": "pdf"},
        headers=engineer_headers,
    )
    assert atlas_export.status_code == 200
    assert atlas_export.json()["status"] == "exported"
    assert atlas_export.json()["metadata"].get("overlay_points") == generate_metadata["overlay_points"]

    latest_atlas = await api_client.get(
        "/api/v1/intelligence/atlas/latest",
        params={"tenant_id": tenant_id, "region": "north-sea"},
        headers=engineer_headers,
    )
    assert latest_atlas.status_code == 200
    latest_payload = latest_atlas.json()
    assert latest_payload["region"] == "north-sea"
    assert latest_payload["metadata"].get("overlay_points") == generate_metadata["overlay_points"]

    maintenance = await api_client.post(
        "/api/v1/intelligence/maintenance/schedule",
        json={"tenant_id": tenant_id, "asset_id": "asset-77", "risk_score": 0.91},
        headers=engineer_headers,
    )
    assert maintenance.status_code == 200
    assert maintenance.json()["recommendation"] == "Immediate inspection"

    iot_rows = (
        await db_session.execute(
            select(IoTDataEntity).where(
                IoTDataEntity.tenant_id == UUID(tenant_id),
                IoTDataEntity.sensor_id == "sensor-alpha",
            )
        )
    ).scalars().all()
    assert len(iot_rows) == 1

    satellite_rows = (
        await db_session.execute(
            select(SatelliteDataEntity).where(SatelliteDataEntity.tenant_id == UUID(tenant_id))
        )
    ).scalars().all()
    assert len(satellite_rows) == 1

    atlas_rows = (
        await db_session.execute(select(AtlasEntity).where(AtlasEntity.tenant_id == UUID(tenant_id)))
    ).scalars().all()
    assert len(atlas_rows) == 2

    maintenance_rows = (
        await db_session.execute(
            select(MaintenanceScheduleEntity).where(MaintenanceScheduleEntity.tenant_id == UUID(tenant_id))
        )
    ).scalars().all()
    assert len(maintenance_rows) == 1

    logs = (
        await db_session.execute(
            select(AuditLogEntity).where(
                AuditLogEntity.event_type.in_(
                    [
                        "IOT_INGESTED",
                        "SATELLITE_INGESTED",
                        "ATLAS_GENERATED",
                        "ATLAS_EXPORTED",
                        "MAINTENANCE_SCHEDULED",
                    ]
                ),
                AuditLogEntity.tenant_id == UUID(tenant_id),
            )
        )
    ).scalars().all()

    assert {item.event_type for item in logs} == {
        "IOT_INGESTED",
        "SATELLITE_INGESTED",
        "ATLAS_GENERATED",
        "ATLAS_EXPORTED",
        "MAINTENANCE_SCHEDULED",
    }
    assert all(item.success for item in logs)


@pytest.mark.asyncio
async def test_phase9_intelligence_endpoint_tenant_isolation(api_client: AsyncClient) -> None:
    _, admin_token = await _register(api_client, role="admin", prefix="phase9-admin-iso")
    _, engineer_token = await _register(api_client, role="engineer", prefix="phase9-engineer-iso")

    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    engineer_headers = {"Authorization": f"Bearer {engineer_token}"}

    tenant_a = await api_client.post(
        "/api/v1/tenants",
        json={"org_name": f"Phase9 TenantA {uuid4().hex[:8]}", "subscription_tier": "professional"},
        headers=admin_headers,
    )
    tenant_b = await api_client.post(
        "/api/v1/tenants",
        json={"org_name": f"Phase9 TenantB {uuid4().hex[:8]}", "subscription_tier": "professional"},
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

    blocked = await api_client.post(
        "/api/v1/intelligence/iot/ingest",
        json={
            "tenant_id": tenant_b.json()["id"],
            "sensor_id": "sensor-iso",
            "payload": {"temperature_c": 24.0},
        },
        headers=engineer_headers,
    )
    assert blocked.status_code == 400
    assert "not a member" in blocked.text.lower()


@pytest.mark.asyncio
async def test_phase9_ops_pipeline_connectors_exports_and_slo(
    api_client: AsyncClient,
) -> None:
    _, admin_token = await _register(api_client, role="admin", prefix="phase9-admin-ops")
    _, engineer_token = await _register(api_client, role="engineer", prefix="phase9-engineer-ops")

    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    engineer_headers = {"Authorization": f"Bearer {engineer_token}"}

    create_tenant = await api_client.post(
        "/api/v1/tenants",
        json={"org_name": f"Phase9 Ops Org {uuid4().hex[:8]}", "subscription_tier": "professional"},
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

    stream = await api_client.post(
        "/api/v1/intelligence/iot/connectors/ingest",
        json={
            "tenant_id": tenant_id,
            "connector_type": "mqtt",
            "events": [
                {
                    "sensor_id": "mqtt-sensor-1",
                    "payload": {
                        "temperature_c": 33.2,
                        "humidity_pct": 81.4,
                        "chloride_ppm": 10120,
                        "region": "north-sea",
                    },
                }
            ],
        },
        headers=engineer_headers,
    )
    assert stream.status_code == 200
    assert stream.json()["accepted_events"] == 1

    provider_sync = await api_client.post(
        "/api/v1/intelligence/satellite/providers/sync",
        json={"tenant_id": tenant_id, "region": "north-sea", "provider": "sentinel"},
        headers=engineer_headers,
    )
    assert provider_sync.status_code == 200, provider_sync.text
    assert provider_sync.json()["frames_ingested"] >= 1

    generate = await api_client.post(
        "/api/v1/intelligence/atlas/generate",
        json={"tenant_id": tenant_id, "region": "north-sea", "export_type": "map_snapshot"},
        headers=engineer_headers,
    )
    assert generate.status_code == 200

    enqueue = await api_client.post(
        "/api/v1/intelligence/atlas/export/jobs",
        json={"tenant_id": tenant_id, "region": "north-sea", "export_type": "pdf"},
        headers=engineer_headers,
    )
    assert enqueue.status_code == 200
    job_id = enqueue.json()["job_id"]

    job_state = await api_client.get(
        f"/api/v1/intelligence/atlas/export/jobs/{job_id}",
        headers=engineer_headers,
    )
    assert job_state.status_code == 200
    assert job_state.json()["status"] in {"queued", "retrying", "completed"}

    slo = await api_client.get(
        "/api/v1/intelligence/ops/slo",
        params={"tenant_id": tenant_id, "window_hours": 24},
        headers=engineer_headers,
    )
    assert slo.status_code == 200
    slo_payload = slo.json()
    assert slo_payload["iot_ingestion_events"] >= 1
    assert slo_payload["satellite_ingestion_events"] >= 1
    assert 0 <= slo_payload["success_ratio"] <= 1
