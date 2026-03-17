from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_audit_log_repository, get_consortium_repository
from app.api.security import require_roles
from app.models.auth import AuthPrincipal, UserRole
from app.models.governance import ConsortiumDashboardRead, ConsortiumMembershipRead, ConsortiumRequest
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.consortium_repository import ConsortiumRepository
from app.services.consortium_service import ConsortiumService

router = APIRouter(prefix="/consortium", tags=["consortium"])


def get_consortium_service(
    repository: ConsortiumRepository = Depends(get_consortium_repository),
) -> ConsortiumService:
    return ConsortiumService(repository=repository)


@router.post("/manage", response_model=ConsortiumMembershipRead)
async def manage_consortium_membership(
    payload: ConsortiumRequest,
    principal: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer)),
    service: ConsortiumService = Depends(get_consortium_service),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> ConsortiumMembershipRead:
    try:
        result = await service.manage_membership(principal=principal, payload=payload)
        await audit_logs.create(
            event_type="CONSORTIUM_UPDATED",
            tenant_id=payload.tenant_id,
            user_id=principal.user_id,
            user_email=principal.email,
            success=True,
            detail=f"action={payload.action};tier={result.tier};status={result.status}",
        )
        return result
    except ValueError as exc:
        await audit_logs.create(
            event_type="CONSORTIUM_UPDATED",
            tenant_id=payload.tenant_id,
            user_id=principal.user_id,
            user_email=principal.email,
            success=False,
            detail=f"action={payload.action};error={str(exc)}",
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/dashboard", response_model=ConsortiumDashboardRead)
async def get_consortium_dashboard(
    tenant_id: UUID,
    principal: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer, UserRole.viewer)),
    service: ConsortiumService = Depends(get_consortium_service),
) -> ConsortiumDashboardRead:
    try:
        return await service.get_dashboard(principal=principal, tenant_id=tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
