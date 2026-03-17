from __future__ import annotations

from uuid import UUID

from app.models.tenant import (
    SubscriptionTier,
    TenantCreateRequest,
    TenantRead,
    TenantUpdateRequest,
    TenantUserLinkRequest,
    TenantUserRead,
)
from app.repositories.tenant_repository import TenantRepository
from app.repositories.user_repository import UserRepository


class TenantService:
    def __init__(self, tenant_repository: TenantRepository, user_repository: UserRepository) -> None:
        self.tenant_repository = tenant_repository
        self.user_repository = user_repository

    async def list_tenants(self) -> list[TenantRead]:
        items = await self.tenant_repository.list_all()
        return [TenantRead.model_validate(item) for item in items]

    async def create_tenant(self, payload: TenantCreateRequest) -> TenantRead:
        if payload.subscription_tier not in SubscriptionTier.ALL:
            raise ValueError("Unsupported subscription tier")
        entity = await self.tenant_repository.create(
            org_name=payload.org_name,
            subscription_tier=payload.subscription_tier,
        )
        return TenantRead.model_validate(entity)

    async def get_tenant(self, tenant_id: UUID) -> TenantRead:
        entity = await self.tenant_repository.get_by_id(tenant_id)
        if entity is None:
            raise ValueError("Tenant not found")
        return TenantRead.model_validate(entity)

    async def update_tenant(self, tenant_id: UUID, payload: TenantUpdateRequest) -> TenantRead:
        if payload.subscription_tier is not None and payload.subscription_tier not in SubscriptionTier.ALL:
            raise ValueError("Unsupported subscription tier")

        entity = await self.tenant_repository.update(
            tenant_id=tenant_id,
            org_name=payload.org_name,
            subscription_tier=payload.subscription_tier,
            subscription_status=payload.subscription_status,
        )
        if entity is None:
            raise ValueError("Tenant not found")
        return TenantRead.model_validate(entity)

    async def delete_tenant(self, tenant_id: UUID) -> None:
        if not await self.tenant_repository.delete(tenant_id=tenant_id):
            raise ValueError("Tenant not found")

    async def list_tenant_users(self, tenant_id: UUID) -> list[TenantUserRead]:
        tenant = await self.tenant_repository.get_by_id(tenant_id)
        if tenant is None:
            raise ValueError("Tenant not found")
        rows = await self.tenant_repository.list_users(tenant_id=tenant_id)
        return [TenantUserRead.model_validate(item) for item in rows]

    async def add_tenant_user(self, tenant_id: UUID, payload: TenantUserLinkRequest) -> TenantUserRead:
        tenant = await self.tenant_repository.get_by_id(tenant_id)
        if tenant is None:
            raise ValueError("Tenant not found")

        user = await self.user_repository.get_by_id(payload.user_id)
        if user is None:
            raise ValueError("User not found")

        row = await self.tenant_repository.add_user(
            tenant_id=tenant_id,
            user_id=payload.user_id,
            role=payload.role,
        )
        return TenantUserRead.model_validate(row)

    async def remove_tenant_user(self, tenant_id: UUID, user_id: UUID) -> None:
        if not await self.tenant_repository.remove_user(tenant_id=tenant_id, user_id=user_id):
            raise ValueError("Tenant membership not found")
