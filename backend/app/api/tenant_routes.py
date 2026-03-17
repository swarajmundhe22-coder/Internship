from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_audit_log_repository, get_tenant_repository, get_user_repository
from app.api.security import require_roles
from app.models.auth import AuthPrincipal, UserRole
from app.models.tenant import (
    TenantCreateRequest,
    TenantRead,
    TenantUpdateRequest,
    TenantUserLinkRequest,
    TenantUserRead,
)
from app.repositories.tenant_repository import TenantRepository
from app.repositories.user_repository import UserRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.services.tenant_service import TenantService

router = APIRouter(prefix="/tenants", tags=["tenants"])


def get_tenant_service(
    tenant_repository: TenantRepository = Depends(get_tenant_repository),
    user_repository: UserRepository = Depends(get_user_repository),
) -> TenantService:
    return TenantService(tenant_repository=tenant_repository, user_repository=user_repository)


@router.get("", response_model=list[TenantRead])
async def list_tenants(
    _principal: AuthPrincipal = Depends(require_roles(UserRole.admin)),
    service: TenantService = Depends(get_tenant_service),
) -> list[TenantRead]:
    return await service.list_tenants()


@router.post("", response_model=TenantRead)
async def create_tenant(
    payload: TenantCreateRequest,
    principal: AuthPrincipal = Depends(require_roles(UserRole.admin)),
    service: TenantService = Depends(get_tenant_service),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> TenantRead:
    try:
        tenant = await service.create_tenant(payload)
        await audit_logs.create(
            event_type="TENANT_MANAGED",
            tenant_id=tenant.id,
            user_id=principal.user_id,
            user_email=principal.email,
            success=True,
            detail="action=create",
        )
        return tenant
    except ValueError as exc:
        await audit_logs.create(
            event_type="TENANT_MANAGED",
            user_id=principal.user_id,
            user_email=principal.email,
            success=False,
            detail=f"action=create;error={str(exc)}",
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/{tenant_id}", response_model=TenantRead)
async def get_tenant(
    tenant_id: UUID,
    _principal: AuthPrincipal = Depends(require_roles(UserRole.admin)),
    service: TenantService = Depends(get_tenant_service),
) -> TenantRead:
    try:
        return await service.get_tenant(tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch("/{tenant_id}", response_model=TenantRead)
async def update_tenant(
    tenant_id: UUID,
    payload: TenantUpdateRequest,
    principal: AuthPrincipal = Depends(require_roles(UserRole.admin)),
    service: TenantService = Depends(get_tenant_service),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> TenantRead:
    try:
        tenant = await service.update_tenant(tenant_id, payload)
        await audit_logs.create(
            event_type="TENANT_MANAGED",
            tenant_id=tenant_id,
            user_id=principal.user_id,
            user_email=principal.email,
            success=True,
            detail="action=update",
        )
        return tenant
    except ValueError as exc:
        await audit_logs.create(
            event_type="TENANT_MANAGED",
            tenant_id=tenant_id,
            user_id=principal.user_id,
            user_email=principal.email,
            success=False,
            detail=f"action=update;error={str(exc)}",
        )
        status_code = status.HTTP_404_NOT_FOUND if "not found" in str(exc).lower() else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.delete("/{tenant_id}")
async def delete_tenant(
    tenant_id: UUID,
    principal: AuthPrincipal = Depends(require_roles(UserRole.admin)),
    service: TenantService = Depends(get_tenant_service),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> dict[str, str]:
    try:
        await service.delete_tenant(tenant_id)
        await audit_logs.create(
            event_type="TENANT_MANAGED",
            tenant_id=tenant_id,
            user_id=principal.user_id,
            user_email=principal.email,
            success=True,
            detail="action=delete",
        )
        return {"status": "deleted"}
    except ValueError as exc:
        await audit_logs.create(
            event_type="TENANT_MANAGED",
            tenant_id=tenant_id,
            user_id=principal.user_id,
            user_email=principal.email,
            success=False,
            detail=f"action=delete;error={str(exc)}",
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{tenant_id}/users", response_model=list[TenantUserRead])
async def list_tenant_users(
    tenant_id: UUID,
    _principal: AuthPrincipal = Depends(require_roles(UserRole.admin)),
    service: TenantService = Depends(get_tenant_service),
) -> list[TenantUserRead]:
    try:
        return await service.list_tenant_users(tenant_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/{tenant_id}/users", response_model=TenantUserRead)
async def add_tenant_user(
    tenant_id: UUID,
    payload: TenantUserLinkRequest,
    principal: AuthPrincipal = Depends(require_roles(UserRole.admin)),
    service: TenantService = Depends(get_tenant_service),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> TenantUserRead:
    try:
        tenant_user = await service.add_tenant_user(tenant_id, payload)
        await audit_logs.create(
            event_type="TENANT_MANAGED",
            tenant_id=tenant_id,
            user_id=principal.user_id,
            user_email=principal.email,
            success=True,
            detail=f"action=add_user;target_user_id={payload.user_id};role={payload.role}",
        )
        return tenant_user
    except ValueError as exc:
        await audit_logs.create(
            event_type="TENANT_MANAGED",
            tenant_id=tenant_id,
            user_id=principal.user_id,
            user_email=principal.email,
            success=False,
            detail=f"action=add_user;target_user_id={payload.user_id};role={payload.role};error={str(exc)}",
        )
        status_code = status.HTTP_404_NOT_FOUND if "not found" in str(exc).lower() else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.delete("/{tenant_id}/users/{user_id}")
async def remove_tenant_user(
    tenant_id: UUID,
    user_id: UUID,
    principal: AuthPrincipal = Depends(require_roles(UserRole.admin)),
    service: TenantService = Depends(get_tenant_service),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> dict[str, str]:
    try:
        await service.remove_tenant_user(tenant_id, user_id)
        await audit_logs.create(
            event_type="TENANT_MANAGED",
            tenant_id=tenant_id,
            user_id=principal.user_id,
            user_email=principal.email,
            success=True,
            detail=f"action=remove_user;target_user_id={user_id}",
        )
        return {"status": "removed"}
    except ValueError as exc:
        await audit_logs.create(
            event_type="TENANT_MANAGED",
            tenant_id=tenant_id,
            user_id=principal.user_id,
            user_email=principal.email,
            success=False,
            detail=f"action=remove_user;target_user_id={user_id};error={str(exc)}",
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
