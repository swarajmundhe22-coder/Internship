from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_api_token_repository, get_webhook_repository
from app.api.security import require_roles
from app.models.auth import AuthPrincipal, UserRole
from app.models.integration import (
    ApiTokenCreateRequest,
    ApiTokenCreateResponse,
    ApiTokenRead,
    WebhookCreateRequest,
    WebhookDeliveryLogRead,
    WebhookRead,
)
from app.models.pagination import PaginatedResponse
from app.repositories.api_token_repository import ApiTokenRepository
from app.repositories.webhook_repository import WebhookRepository
from app.services.api_token_service import ApiTokenService
from app.services.webhook_service import WebhookService

router = APIRouter(prefix="/integrations", tags=["integrations"])


def get_api_token_service(
    repository: ApiTokenRepository = Depends(get_api_token_repository),
) -> ApiTokenService:
    return ApiTokenService(repository=repository)


def get_webhook_service(
    repository: WebhookRepository = Depends(get_webhook_repository),
) -> WebhookService:
    return WebhookService(repository=repository)


@router.post("/api-tokens", response_model=ApiTokenCreateResponse)
async def create_api_token(
    payload: ApiTokenCreateRequest,
    user: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer)),
    service: ApiTokenService = Depends(get_api_token_service),
) -> ApiTokenCreateResponse:
    return await service.create_token(user_id=user.user_id, payload=payload)


@router.get("/api-tokens", response_model=list[ApiTokenRead])
async def list_api_tokens(
    user: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer)),
    service: ApiTokenService = Depends(get_api_token_service),
) -> list[ApiTokenRead]:
    return await service.list_tokens(user_id=user.user_id)


@router.delete("/api-tokens/{token_id}")
async def revoke_api_token(
    token_id: UUID,
    user: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer)),
    service: ApiTokenService = Depends(get_api_token_service),
) -> dict[str, str]:
    try:
        await service.revoke_token(user_id=user.user_id, token_id=token_id)
        return {"status": "revoked"}
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/webhooks", response_model=WebhookRead)
async def create_webhook(
    payload: WebhookCreateRequest,
    user: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer)),
    service: WebhookService = Depends(get_webhook_service),
) -> WebhookRead:
    return await service.create_webhook(user_id=user.user_id, payload=payload)


@router.get("/webhooks", response_model=list[WebhookRead])
async def list_webhooks(
    user: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer)),
    service: WebhookService = Depends(get_webhook_service),
) -> list[WebhookRead]:
    return await service.list_webhooks(user_id=user.user_id)


@router.delete("/webhooks/{webhook_id}")
async def deactivate_webhook(
    webhook_id: UUID,
    user: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer)),
    service: WebhookService = Depends(get_webhook_service),
) -> dict[str, str]:
    try:
        await service.delete_webhook(user_id=user.user_id, webhook_id=webhook_id)
        return {"status": "deactivated"}
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/webhooks/deliveries", response_model=PaginatedResponse[WebhookDeliveryLogRead])
async def list_webhook_delivery_logs(
    page: int = 1,
    page_size: int = 25,
    webhook_id: UUID | None = None,
    success: bool | None = None,
    user: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer)),
    service: WebhookService = Depends(get_webhook_service),
) -> PaginatedResponse[WebhookDeliveryLogRead]:
    return await service.list_delivery_logs(
        user_id=user.user_id,
        page=page,
        page_size=page_size,
        webhook_id=webhook_id,
        success=success,
    )