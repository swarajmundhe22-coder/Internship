from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from app.models.auth import AuthPrincipal, UserRole
from app.models.governance import (
    ConsortiumAction,
    ConsortiumDashboardRead,
    ConsortiumMembershipRead,
    ConsortiumRequest,
    ConsortiumTier,
)
from app.repositories.consortium_repository import ConsortiumRepository


class ConsortiumService:
    def __init__(self, repository: ConsortiumRepository) -> None:
        self.repository = repository

    async def manage_membership(
        self,
        *,
        principal: AuthPrincipal,
        payload: ConsortiumRequest,
    ) -> ConsortiumMembershipRead:
        await self._assert_tenant_access(principal=principal, tenant_id=payload.tenant_id)

        action = payload.action.lower()
        if action not in ConsortiumAction.ALL:
            raise ValueError("Unsupported consortium action")

        current = await self.repository.get_membership(tenant_id=payload.tenant_id)
        if current is None:
            if action != ConsortiumAction.JOIN:
                raise ValueError("Membership does not exist. Use join first")
            created = await self.repository.create_membership(
                tenant_id=payload.tenant_id,
                tier=ConsortiumTier.GLOBAL_UTILITY,
                status="active",
            )
            return ConsortiumMembershipRead.model_validate(created)

        if action == ConsortiumAction.JOIN:
            return ConsortiumMembershipRead.model_validate(current)

        next_tier = self._resolve_tier_transition(current.tier, action)
        updated = await self.repository.update_membership(
            membership_id=current.id,
            tier=next_tier,
            status="active",
        )
        if updated is None:
            raise ValueError("Membership update failed")
        return ConsortiumMembershipRead.model_validate(updated)

    async def get_dashboard(
        self,
        *,
        principal: AuthPrincipal,
        tenant_id: UUID,
    ) -> ConsortiumDashboardRead:
        await self._assert_tenant_access(principal=principal, tenant_id=tenant_id)

        membership = await self.repository.get_membership(tenant_id=tenant_id)
        if membership is None:
            raise ValueError("Membership does not exist")

        dossiers_30d = await self.repository.count_recent_dossiers(tenant_id=tenant_id)
        decks_30d = await self.repository.count_recent_decks(tenant_id=tenant_id)

        foresight_index = min(100.0, round((dossiers_30d * 4.0) + (decks_30d * 6.0) + 35.0, 2))
        compliance_status = "trusted" if dossiers_30d > 0 else "monitoring"

        return ConsortiumDashboardRead(
            tenant_id=tenant_id,
            tier=membership.tier,
            compliance_status=compliance_status,
            foresight_index=foresight_index,
            consortium_voting_enabled=membership.tier == ConsortiumTier.PLANETARY_CLUB,
            active_dossiers_30d=dossiers_30d,
            active_decks_30d=decks_30d,
            generated_at=datetime.now(UTC),
        )

    async def _assert_tenant_access(self, *, principal: AuthPrincipal, tenant_id: UUID) -> None:
        if not await self.repository.tenant_exists(tenant_id):
            raise ValueError("Tenant not found")
        if principal.role != UserRole.admin:
            if not await self.repository.user_in_tenant(user_id=principal.user_id, tenant_id=tenant_id):
                raise ValueError("User is not a member of tenant")

    @staticmethod
    def _resolve_tier_transition(current_tier: str, action: str) -> str:
        tiers = ConsortiumTier.ORDERED
        if current_tier not in tiers:
            return ConsortiumTier.GLOBAL_UTILITY

        index = tiers.index(current_tier)
        if action == ConsortiumAction.UPGRADE:
            return tiers[min(index + 1, len(tiers) - 1)]
        if action == ConsortiumAction.DOWNGRADE:
            return tiers[max(index - 1, 0)]
        return current_tier
