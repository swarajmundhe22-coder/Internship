from __future__ import annotations

import json
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import SimulationEntity, TenantSimulationEntity, TenantUserEntity, VisualizationEntity, VisualizationExportEntity


class VisualizationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_simulation(self, simulation_id: UUID) -> SimulationEntity | None:
        return await self.session.get(SimulationEntity, simulation_id)

    async def user_in_tenant(self, *, user_id: UUID, tenant_id: UUID) -> bool:
        result = await self.session.execute(
            select(TenantUserEntity.id).where(
                TenantUserEntity.user_id == user_id,
                TenantUserEntity.tenant_id == tenant_id,
            )
        )
        return result.scalar_one_or_none() is not None

    async def simulation_in_tenant(self, *, simulation_id: UUID, tenant_id: UUID) -> bool:
        result = await self.session.execute(
            select(TenantSimulationEntity.id).where(
                TenantSimulationEntity.simulation_id == simulation_id,
                TenantSimulationEntity.tenant_id == tenant_id,
            )
        )
        return result.scalar_one_or_none() is not None

    async def create_visualization(
        self,
        *,
        simulation_id: UUID,
        tenant_id: UUID | None,
        mode: str,
        metadata: dict[str, object],
        status: str,
        overlay_accuracy: float,
    ) -> VisualizationEntity:
        entity = VisualizationEntity(
            simulation_id=simulation_id,
            tenant_id=tenant_id,
            mode=mode,
            metadata_json=json.dumps(metadata, separators=(",", ":"), sort_keys=True),
            status=status,
            overlay_accuracy=overlay_accuracy,
        )
        self.session.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        return entity

    async def get_latest_visualization(
        self,
        *,
        simulation_id: UUID,
        tenant_id: UUID,
        mode: str,
    ) -> VisualizationEntity | None:
        result = await self.session.execute(
            select(VisualizationEntity)
            .where(
                VisualizationEntity.simulation_id == simulation_id,
                VisualizationEntity.tenant_id == tenant_id,
                VisualizationEntity.mode == mode,
            )
            .order_by(VisualizationEntity.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def create_export(
        self,
        *,
        visualization_id: UUID,
        tenant_id: UUID | None,
        file_type: str,
        file_uri: str,
    ) -> VisualizationExportEntity:
        entity = VisualizationExportEntity(
            visualization_id=visualization_id,
            tenant_id=tenant_id,
            file_type=file_type,
            file_uri=file_uri,
        )
        self.session.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        return entity
