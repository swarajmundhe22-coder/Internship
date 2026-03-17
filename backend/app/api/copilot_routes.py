from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies import get_audit_log_repository
from app.api.security import require_roles
from app.models.auth import AuthPrincipal, UserRole
from app.models.copilot import CopilotRequest, CopilotResponse
from app.repositories.audit_log_repository import AuditLogRepository
from app.services.copilot_service import CopilotService

router = APIRouter(prefix="/copilot", tags=["copilot"])


def get_copilot_service() -> CopilotService:
    return CopilotService()


@router.post("/query", response_model=CopilotResponse)
async def query_copilot(
    payload: CopilotRequest,
    principal: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer)),
    service: CopilotService = Depends(get_copilot_service),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> CopilotResponse:
    response, model = service.query(payload.user_input)
    await audit_logs.create(
        event_type="COPILOT_QUERY",
        tenant_id=payload.tenant_id,
        user_id=principal.user_id,
        user_email=principal.email,
        success=True,
        detail=f"model={model}",
    )
    return CopilotResponse(response=response, model=model)


@router.post("/doc", response_model=CopilotResponse)
async def doc_copilot(
    payload: CopilotRequest,
    principal: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer)),
    service: CopilotService = Depends(get_copilot_service),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> CopilotResponse:
    response, model = service.doc(payload.user_input)
    await audit_logs.create(
        event_type="COPILOT_DOC",
        tenant_id=payload.tenant_id,
        user_id=principal.user_id,
        user_email=principal.email,
        success=True,
        detail=f"model={model}",
    )
    return CopilotResponse(response=response, model=model)


@router.post("/search", response_model=CopilotResponse)
async def search_copilot(
    payload: CopilotRequest,
    principal: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer)),
    service: CopilotService = Depends(get_copilot_service),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> CopilotResponse:
    response, model = service.search(payload.user_input)
    await audit_logs.create(
        event_type="COPILOT_SEARCH",
        tenant_id=payload.tenant_id,
        user_id=principal.user_id,
        user_email=principal.email,
        success=True,
        detail=f"model={model}",
    )
    return CopilotResponse(response=response, model=model)
