from __future__ import annotations

import json
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import DossierEntity, TenantSimulationEntity, TenantUserEntity


class DossierRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

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

    async def create_dossier(
        self,
        *,
        tenant_id: UUID,
        simulation_id: UUID,
        format: str,
        industry_module: str,
        artifact_uri: str,
        metadata: dict[str, object],
    ) -> DossierEntity:
        entity = DossierEntity(
            tenant_id=tenant_id,
            simulation_id=simulation_id,
            format=format,
            industry_module=industry_module,
            artifact_uri=artifact_uri,
            metadata_json=json.dumps(metadata, separators=(",", ":"), sort_keys=True),
        )
        self.session.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        return entity
