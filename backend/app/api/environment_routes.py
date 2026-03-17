from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.algorithms.environmental_risk import calculate_environmental_risk
from app.api.dependencies import get_environment_repository
from app.api.security import require_roles
from app.models.auth import AuthPrincipal, UserRole
from app.models.environment import (
    EnvironmentCreate,
    EnvironmentInput,
    EnvironmentRead,
    EnvironmentRiskResult,
    EnvironmentUpdate,
)
from app.models.pagination import EnvironmentListQuery, PaginatedResponse
from app.repositories.exceptions import ConflictError, EntityNotFoundError, PersistenceError
from app.services.environment_service import EnvironmentService

router = APIRouter(prefix="/environment", tags=["environment"])


def get_environment_service(
    repository=Depends(get_environment_repository),
) -> EnvironmentService:
    return EnvironmentService(repository=repository)


@router.post("", response_model=EnvironmentRead, status_code=status.HTTP_201_CREATED)
async def create_environment(
    payload: EnvironmentCreate,
    _principal: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer)),
    service: EnvironmentService = Depends(get_environment_service),
) -> EnvironmentRead:
    try:
        return await service.create_environment(payload)
    except ConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except PersistenceError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get("/{environment_id}", response_model=EnvironmentRead)
async def get_environment(
    environment_id: UUID,
    _principal: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer, UserRole.viewer)),
    service: EnvironmentService = Depends(get_environment_service),
) -> EnvironmentRead:
    try:
        return await service.get_environment(environment_id)
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("", response_model=PaginatedResponse[EnvironmentRead])
async def list_environments(
    page: int = 1,
    page_size: int = 25,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    _principal: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer, UserRole.viewer)),
    service: EnvironmentService = Depends(get_environment_service),
) -> PaginatedResponse[EnvironmentRead]:
    query = EnvironmentListQuery(
        page=page,
        page_size=page_size,
        created_from=created_from,
        created_to=created_to,
    )
    return await service.list_environments(query)


@router.put("/{environment_id}", response_model=EnvironmentRead)
async def update_environment(
    environment_id: UUID,
    payload: EnvironmentUpdate,
    _principal: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer)),
    service: EnvironmentService = Depends(get_environment_service),
) -> EnvironmentRead:
    try:
        return await service.update_environment(environment_id, payload)
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.delete("/{environment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_environment(
    environment_id: UUID,
    _principal: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer)),
    service: EnvironmentService = Depends(get_environment_service),
) -> Response:
    try:
        await service.delete_environment(environment_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/risk-score", response_model=EnvironmentRiskResult)
async def score_environment(
    payload: EnvironmentInput,
    _principal: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer, UserRole.viewer)),
) -> EnvironmentRiskResult:
    return calculate_environmental_risk(payload)
