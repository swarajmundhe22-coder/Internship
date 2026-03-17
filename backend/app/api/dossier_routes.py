from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_audit_log_repository, get_dossier_repository
from app.api.security import require_roles
from app.models.auth import AuthPrincipal, UserRole
from app.models.governance import DossierRequest, DossierResponse
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.dossier_repository import DossierRepository
from app.services.dossier_service import DossierService

router = APIRouter(prefix="/dossier", tags=["dossier"])


def get_dossier_service(
    repository: DossierRepository = Depends(get_dossier_repository),
) -> DossierService:
    return DossierService(repository=repository)


@router.post("/generate", response_model=DossierResponse)
async def generate_dossier(
    payload: DossierRequest,
    principal: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer)),
    service: DossierService = Depends(get_dossier_service),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> DossierResponse:
    try:
        result = await service.generate_dossier(principal=principal, payload=payload)
        await audit_logs.create(
            event_type="DOSSIER_GENERATED",
            tenant_id=payload.tenant_id,
            user_id=principal.user_id,
            user_email=principal.email,
            success=True,
            detail=(
                f"simulation_id={payload.simulation_id};format={payload.format};"
                f"industry_module={payload.industry_module};artifact_uri={result.artifact_uri}"
            ),
        )
        return result
    except ValueError as exc:
        await audit_logs.create(
            event_type="DOSSIER_GENERATED",
            tenant_id=payload.tenant_id,
            user_id=principal.user_id,
            user_email=principal.email,
            success=False,
            detail=(
                f"simulation_id={payload.simulation_id};format={payload.format};"
                f"industry_module={payload.industry_module};error={str(exc)}"
            ),
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
