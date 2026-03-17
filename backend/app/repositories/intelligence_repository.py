from __future__ import annotations

from datetime import datetime
import json
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import (
    AtlasEntity,
    AtlasExportJobEntity,
    DeadLetterEventEntity,
    IoTDataEntity,
    MaintenanceScheduleEntity,
    SatelliteDataEntity,
    TenantEntity,
    TenantUserEntity,
)


class IntelligenceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def tenant_exists(self, tenant_id: UUID) -> bool:
        tenant = await self.session.get(TenantEntity, tenant_id)
        return tenant is not None

    async def user_in_tenant(self, *, user_id: UUID, tenant_id: UUID) -> bool:
        result = await self.session.execute(
            select(TenantUserEntity.id).where(
                TenantUserEntity.user_id == user_id,
                TenantUserEntity.tenant_id == tenant_id,
            )
        )
        return result.scalar_one_or_none() is not None

    async def create_iot_data(self, *, tenant_id: UUID, sensor_id: str, payload: dict[str, Any]) -> IoTDataEntity:
        entity = IoTDataEntity(
            tenant_id=tenant_id,
            sensor_id=sensor_id,
            payload_json=json.dumps(payload, separators=(",", ":"), sort_keys=True),
        )
        self.session.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        return entity

    async def list_recent_iot(self, *, tenant_id: UUID, limit: int = 50) -> list[IoTDataEntity]:
        result = await self.session.execute(
            select(IoTDataEntity)
            .where(IoTDataEntity.tenant_id == tenant_id)
            .order_by(IoTDataEntity.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def list_recent_satellite(self, *, tenant_id: UUID, region: str, limit: int = 20) -> list[SatelliteDataEntity]:
        result = await self.session.execute(
            select(SatelliteDataEntity)
            .where(
                SatelliteDataEntity.tenant_id == tenant_id,
                SatelliteDataEntity.region == region,
            )
            .order_by(SatelliteDataEntity.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()

    async def create_export_job(
        self,
        *,
        tenant_id: UUID,
        region: str,
        export_type: str,
        max_attempts: int,
        metadata: dict[str, Any],
    ) -> AtlasExportJobEntity:
        entity = AtlasExportJobEntity(
            tenant_id=tenant_id,
            region=region,
            export_type=export_type,
            status="queued",
            max_attempts=max_attempts,
            metadata_json=json.dumps(metadata, separators=(",", ":"), sort_keys=True),
        )
        self.session.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        return entity

    async def get_export_job(self, *, job_id: UUID) -> AtlasExportJobEntity | None:
        return await self.session.get(AtlasExportJobEntity, job_id)

    async def update_export_job(
        self,
        *,
        job_id: UUID,
        status: str,
        attempt_count: int,
        output_uri: str | None,
        last_error: str | None,
        last_attempt_at: datetime | None,
        completed_at: datetime | None,
    ) -> AtlasExportJobEntity | None:
        entity = await self.session.get(AtlasExportJobEntity, job_id)
        if entity is None:
            return None
        entity.status = status
        entity.attempt_count = attempt_count
        entity.output_uri = output_uri
        entity.last_error = last_error
        entity.last_attempt_at = last_attempt_at
        entity.completed_at = completed_at
        await self.session.commit()
        await self.session.refresh(entity)
        return entity

    async def create_dead_letter(
        self,
        *,
        tenant_id: UUID | None,
        event_source: str,
        payload: dict[str, Any],
        error_message: str,
        retry_count: int,
    ) -> DeadLetterEventEntity:
        entity = DeadLetterEventEntity(
            tenant_id=tenant_id,
            event_source=event_source,
            payload_json=json.dumps(payload, separators=(",", ":"), sort_keys=True),
            error_message=error_message,
            retry_count=retry_count,
        )
        self.session.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        return entity

    async def count_iot_since(self, *, tenant_id: UUID, since: datetime) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(IoTDataEntity).where(
                IoTDataEntity.tenant_id == tenant_id,
                IoTDataEntity.created_at >= since,
            )
        )
        return int(result.scalar_one())

    async def count_satellite_since(self, *, tenant_id: UUID, since: datetime) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(SatelliteDataEntity).where(
                SatelliteDataEntity.tenant_id == tenant_id,
                SatelliteDataEntity.created_at >= since,
            )
        )
        return int(result.scalar_one())

    async def count_dead_letters_since(self, *, tenant_id: UUID, since: datetime) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(DeadLetterEventEntity).where(
                DeadLetterEventEntity.tenant_id == tenant_id,
                DeadLetterEventEntity.created_at >= since,
            )
        )
        return int(result.scalar_one())

    async def count_export_jobs_since(self, *, tenant_id: UUID, since: datetime, status: str) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(AtlasExportJobEntity).where(
                AtlasExportJobEntity.tenant_id == tenant_id,
                AtlasExportJobEntity.created_at >= since,
                AtlasExportJobEntity.status == status,
            )
        )
        return int(result.scalar_one())

    async def create_satellite_data(
        self,
        *,
        tenant_id: UUID,
        region: str,
        imagery_source: str,
        metadata: dict[str, Any],
    ) -> SatelliteDataEntity:
        entity = SatelliteDataEntity(
            tenant_id=tenant_id,
            region=region,
            imagery_source=imagery_source,
            metadata_json=json.dumps(metadata, separators=(",", ":"), sort_keys=True),
        )
        self.session.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        return entity

    async def create_atlas(
        self,
        *,
        tenant_id: UUID,
        region: str,
        atlas_key: str,
        export_type: str,
        metadata: dict[str, Any],
    ) -> AtlasEntity:
        entity = AtlasEntity(
            tenant_id=tenant_id,
            region=region,
            atlas_key=atlas_key,
            export_type=export_type,
            metadata_json=json.dumps(metadata, separators=(",", ":"), sort_keys=True),
        )
        self.session.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        return entity

    async def create_maintenance_schedule(
        self,
        *,
        tenant_id: UUID,
        asset_id: str,
        risk_score: float,
        recommendation: str,
        metadata: dict[str, Any],
    ) -> MaintenanceScheduleEntity:
        entity = MaintenanceScheduleEntity(
            tenant_id=tenant_id,
            asset_id=asset_id,
            risk_score=risk_score,
            recommendation=recommendation,
            metadata_json=json.dumps(metadata, separators=(",", ":"), sort_keys=True),
        )
        self.session.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        return entity

    async def get_latest_atlas(self, *, tenant_id: UUID, region: str) -> AtlasEntity | None:
        result = await self.session.execute(
            select(AtlasEntity)
            .where(
                AtlasEntity.tenant_id == tenant_id,
                AtlasEntity.region == region,
            )
            .order_by(AtlasEntity.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
