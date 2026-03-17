from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_audit_log_repository, get_deck_repository
from app.api.security import require_roles
from app.models.auth import AuthPrincipal, UserRole
from app.models.governance import DeckRequest, DeckResponse
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.deck_repository import DeckRepository
from app.services.deck_service import DeckService

router = APIRouter(prefix="/deck", tags=["deck"])


def get_deck_service(
    repository: DeckRepository = Depends(get_deck_repository),
) -> DeckService:
    return DeckService(repository=repository)


@router.post("/export", response_model=DeckResponse)
async def export_deck(
    payload: DeckRequest,
    principal: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer)),
    service: DeckService = Depends(get_deck_service),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> DeckResponse:
    try:
        result = await service.export_deck(principal=principal, payload=payload)
        await audit_logs.create(
            event_type="DECK_EXPORTED",
            tenant_id=payload.tenant_id,
            user_id=principal.user_id,
            user_email=principal.email,
            success=True,
            detail=f"project_id={payload.project_id};export_type={payload.export_type};artifact_uri={result.artifact_uri}",
        )
        return result
    except ValueError as exc:
        await audit_logs.create(
            event_type="DECK_EXPORTED",
            tenant_id=payload.tenant_id,
            user_id=principal.user_id,
            user_email=principal.email,
            success=False,
            detail=f"project_id={payload.project_id};export_type={payload.export_type};error={str(exc)}",
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
