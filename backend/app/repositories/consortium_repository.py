from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import ConsortiumMembershipEntity, DeckEntity, DossierEntity, TenantEntity, TenantUserEntity


class ConsortiumRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def tenant_exists(self, tenant_id: UUID) -> bool:
        return await self.session.get(TenantEntity, tenant_id) is not None

    async def user_in_tenant(self, *, user_id: UUID, tenant_id: UUID) -> bool:
        result = await self.session.execute(
            select(TenantUserEntity.id).where(
                TenantUserEntity.user_id == user_id,
                TenantUserEntity.tenant_id == tenant_id,
            )
        )
        return result.scalar_one_or_none() is not None

    async def get_membership(self, *, tenant_id: UUID) -> ConsortiumMembershipEntity | None:
        result = await self.session.execute(
            select(ConsortiumMembershipEntity).where(ConsortiumMembershipEntity.tenant_id == tenant_id)
        )
        return result.scalar_one_or_none()

    async def create_membership(self, *, tenant_id: UUID, tier: str, status: str = "active") -> ConsortiumMembershipEntity:
        entity = ConsortiumMembershipEntity(tenant_id=tenant_id, tier=tier, status=status)
        self.session.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        return entity

    async def update_membership(self, *, membership_id: UUID, tier: str, status: str) -> ConsortiumMembershipEntity | None:
        entity = await self.session.get(ConsortiumMembershipEntity, membership_id)
        if entity is None:
            return None
        entity.tier = tier
        entity.status = status
        entity.updated_at = datetime.now(UTC)
        await self.session.commit()
        await self.session.refresh(entity)
        return entity

    async def count_recent_dossiers(self, *, tenant_id: UUID, window_days: int = 30) -> int:
        since = datetime.now(UTC) - timedelta(days=window_days)
        result = await self.session.execute(
            select(func.count()).select_from(DossierEntity).where(
                DossierEntity.tenant_id == tenant_id,
                DossierEntity.created_at >= since,
            )
        )
        return int(result.scalar_one())

    async def count_recent_decks(self, *, tenant_id: UUID, window_days: int = 30) -> int:
        since = datetime.now(UTC) - timedelta(days=window_days)
        result = await self.session.execute(
            select(func.count()).select_from(DeckEntity).where(
                DeckEntity.tenant_id == tenant_id,
                DeckEntity.created_at >= since,
            )
        )
        return int(result.scalar_one())
