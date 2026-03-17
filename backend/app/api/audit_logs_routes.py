from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.dependencies import get_audit_log_repository
from app.api.security import require_roles
from app.models.audit import AuditLogRead
from app.models.auth import AuthPrincipal, UserRole
from app.models.pagination import AuditLogListQuery, PaginatedResponse
from app.repositories.audit_log_repository import AuditLogRepository
from app.services.audit_log_service import AuditLogService

router = APIRouter(prefix="/audit-logs", tags=["audit-logs"])


def get_audit_log_service(
    repository: AuditLogRepository = Depends(get_audit_log_repository),
) -> AuditLogService:
    return AuditLogService(repository=repository)


@router.get("", response_model=PaginatedResponse[AuditLogRead])
async def list_audit_logs(
    page: int = 1,
    page_size: int = 50,
    event_type: str | None = None,
    tenant_id: UUID | None = None,
    user_id: UUID | None = None,
    user_email: str | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    _principal: AuthPrincipal = Depends(require_roles(UserRole.admin)),
    service: AuditLogService = Depends(get_audit_log_service),
) -> PaginatedResponse[AuditLogRead]:
    query = AuditLogListQuery(
        page=page,
        page_size=page_size,
        event_type=event_type,
        tenant_id=tenant_id,
        user_id=user_id,
        user_email=user_email,
        created_from=created_from,
        created_to=created_to,
    )
    return await service.list_logs(query)
