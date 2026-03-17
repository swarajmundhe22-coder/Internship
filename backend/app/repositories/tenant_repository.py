from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import TenantEntity, TenantSimulationEntity, TenantUserEntity


class TenantRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, tenant_id: UUID) -> TenantEntity | None:
        return await self.session.get(TenantEntity, tenant_id)

    async def create(self, *, org_name: str, subscription_tier: str) -> TenantEntity:
        entity = TenantEntity(org_name=org_name, subscription_tier=subscription_tier, subscription_status="active")
        self.session.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        return entity

    async def update(
        self,
        *,
        tenant_id: UUID,
        org_name: str | None = None,
        subscription_tier: str | None = None,
        subscription_status: str | None = None,
    ) -> TenantEntity | None:
        entity = await self.session.get(TenantEntity, tenant_id)
        if entity is None:
            return None
        if org_name is not None:
            entity.org_name = org_name
        if subscription_tier is not None:
            entity.subscription_tier = subscription_tier
        if subscription_status is not None:
            entity.subscription_status = subscription_status
        entity.updated_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(entity)
        return entity

    async def delete(self, *, tenant_id: UUID) -> bool:
        entity = await self.session.get(TenantEntity, tenant_id)
        if entity is None:
            return False
        await self.session.delete(entity)
        await self.session.commit()
        return True

    async def update_subscription_tier(
        self,
        *,
        tenant_id: UUID,
        subscription_tier: str,
        subscription_status: str,
    ) -> TenantEntity | None:
        return await self.update(
            tenant_id=tenant_id,
            subscription_tier=subscription_tier,
            subscription_status=subscription_status,
        )

    async def list_all(self) -> list[TenantEntity]:
        result = await self.session.execute(select(TenantEntity).order_by(TenantEntity.created_at.desc()))
        return result.scalars().all()

    async def add_user(self, *, tenant_id: UUID, user_id: UUID, role: str) -> TenantUserEntity:
        entity = TenantUserEntity(tenant_id=tenant_id, user_id=user_id, role=role)
        self.session.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        return entity

    async def list_users(self, *, tenant_id: UUID) -> list[TenantUserEntity]:
        result = await self.session.execute(
            select(TenantUserEntity)
            .where(TenantUserEntity.tenant_id == tenant_id)
            .order_by(TenantUserEntity.created_at.asc())
        )
        return result.scalars().all()

    async def remove_user(self, *, tenant_id: UUID, user_id: UUID) -> bool:
        result = await self.session.execute(
            select(TenantUserEntity).where(
                TenantUserEntity.tenant_id == tenant_id,
                TenantUserEntity.user_id == user_id,
            )
        )
        entity = result.scalar_one_or_none()
        if entity is None:
            return False
        await self.session.delete(entity)
        await self.session.commit()
        return True

    async def get_primary_tenant_for_user(self, *, user_id: UUID) -> TenantEntity | None:
        statement = (
            select(TenantEntity)
            .join(TenantUserEntity, TenantUserEntity.tenant_id == TenantEntity.id)
            .where(TenantUserEntity.user_id == user_id)
            .order_by(TenantUserEntity.created_at.asc())
            .limit(1)
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def bind_simulation_to_tenant(self, *, tenant_id: UUID, simulation_id: UUID) -> TenantSimulationEntity:
        entity = TenantSimulationEntity(tenant_id=tenant_id, simulation_id=simulation_id)
        self.session.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        return entity
