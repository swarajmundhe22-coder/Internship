from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from app.core.config import get_settings
from app.models.auth import AuthPrincipal, UserRole
from app.models.governance import DossierFormat, DossierRequest, DossierResponse
from app.repositories.dossier_repository import DossierRepository


class DossierService:
    def __init__(self, repository: DossierRepository) -> None:
        self.repository = repository
        self.settings = get_settings()

    async def generate_dossier(self, *, principal: AuthPrincipal, payload: DossierRequest) -> DossierResponse:
        await self._assert_access(principal=principal, tenant_id=payload.tenant_id, simulation_id=payload.simulation_id)

        export_format = payload.format.lower()
        if export_format not in DossierFormat.ALL:
            raise ValueError("Unsupported dossier format")

        artifact_uri = (
            f"{self.settings.export_artifacts_dir}/dossiers/"
            f"{payload.tenant_id}/dossier_{payload.simulation_id}_{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}.{export_format}"
        )
        row = await self.repository.create_dossier(
            tenant_id=payload.tenant_id,
            simulation_id=payload.simulation_id,
            format=export_format,
            industry_module=payload.industry_module,
            artifact_uri=artifact_uri,
            metadata={
                "compliance_profile": payload.industry_module,
                "generated_by": str(principal.user_id),
                "audit_mode": "tenant-bound",
            },
        )
        return DossierResponse(
            dossier_id=row.id,
            tenant_id=row.tenant_id,
            simulation_id=row.simulation_id,
            format=row.format,
            industry_module=row.industry_module,
            artifact_uri=row.artifact_uri,
        )

    async def _assert_access(self, *, principal: AuthPrincipal, tenant_id: UUID, simulation_id: UUID) -> None:
        if principal.role != UserRole.admin:
            if not await self.repository.user_in_tenant(user_id=principal.user_id, tenant_id=tenant_id):
                raise ValueError("User is not a member of tenant")
        if not await self.repository.simulation_in_tenant(simulation_id=simulation_id, tenant_id=tenant_id):
            raise ValueError("Simulation is not bound to tenant")
