from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from app.core.config import get_settings
from app.models.auth import AuthPrincipal, UserRole
from app.models.governance import DeckExportType, DeckRequest, DeckResponse
from app.repositories.deck_repository import DeckRepository


class DeckService:
    def __init__(self, repository: DeckRepository) -> None:
        self.repository = repository
        self.settings = get_settings()

    async def export_deck(self, *, principal: AuthPrincipal, payload: DeckRequest) -> DeckResponse:
        await self._assert_access(principal=principal, tenant_id=payload.tenant_id, project_id=payload.project_id)

        export_type = payload.export_type.lower()
        if export_type not in DeckExportType.ALL:
            raise ValueError("Unsupported deck export_type")

        artifact_uri = (
            f"{self.settings.export_artifacts_dir}/decks/"
            f"{payload.tenant_id}/deck_{payload.project_id}_{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}.{export_type}"
        )
        row = await self.repository.create_deck(
            tenant_id=payload.tenant_id,
            project_id=payload.project_id,
            export_type=export_type,
            artifact_uri=artifact_uri,
            narrative={
                "headline": "Planetary foresight risk narrative",
                "voiceover": "Automated boardroom mode enabled",
                "generated_by": str(principal.user_id),
            },
        )
        return DeckResponse(
            deck_id=row.id,
            tenant_id=row.tenant_id,
            project_id=row.project_id,
            export_type=row.export_type,
            artifact_uri=row.artifact_uri,
        )

    async def _assert_access(self, *, principal: AuthPrincipal, tenant_id: UUID, project_id: UUID) -> None:
        if principal.role != UserRole.admin:
            if not await self.repository.user_in_tenant(user_id=principal.user_id, tenant_id=tenant_id):
                raise ValueError("User is not a member of tenant")
        if not await self.repository.project_in_tenant(project_id=project_id, tenant_id=tenant_id):
            raise ValueError("Project is not bound to tenant")
