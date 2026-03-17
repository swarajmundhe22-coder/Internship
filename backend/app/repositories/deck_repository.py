from __future__ import annotations

import json
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import DeckEntity, ProjectEntity, TenantUserEntity


class DeckRepository:
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

    async def project_in_tenant(self, *, project_id: UUID, tenant_id: UUID) -> bool:
        result = await self.session.execute(
            select(ProjectEntity.id).where(
                ProjectEntity.id == project_id,
                ProjectEntity.tenant_id == tenant_id,
            )
        )
        return result.scalar_one_or_none() is not None

    async def create_deck(
        self,
        *,
        tenant_id: UUID,
        project_id: UUID,
        export_type: str,
        artifact_uri: str,
        narrative: dict[str, object],
    ) -> DeckEntity:
        entity = DeckEntity(
            tenant_id=tenant_id,
            project_id=project_id,
            export_type=export_type,
            artifact_uri=artifact_uri,
            narrative_json=json.dumps(narrative, separators=(",", ":"), sort_keys=True),
        )
        self.session.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        return entity
