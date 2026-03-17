from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_comparison_set_repository, get_project_repository
from app.api.security import require_roles
from app.database.session import get_db_session
from app.models.auth import AuthPrincipal, UserRole
from app.models.comparison_set import ComparisonSetDetailResponse, ComparisonSetUpdateRequest
from app.repositories.comparison_set_repository import ComparisonSetRepository
from app.repositories.exceptions import EntityNotFoundError
from app.repositories.project_repository import ProjectRepository
from app.services.comparison_service import ComparisonService
from app.services.comparison_set_service import ComparisonSetService

router = APIRouter(prefix="/comparison-sets", tags=["comparison-sets"])


def get_comparison_set_service(
    session: AsyncSession = Depends(get_db_session),
    project_repository: ProjectRepository = Depends(get_project_repository),
    comparison_set_repository: ComparisonSetRepository = Depends(get_comparison_set_repository),
) -> ComparisonSetService:
    return ComparisonSetService(
        comparison_set_repository=comparison_set_repository,
        project_repository=project_repository,
        comparison_service=ComparisonService(session=session),
    )


@router.get("/{comparison_set_id}", response_model=ComparisonSetDetailResponse)
async def get_comparison_set(
    comparison_set_id: UUID,
    user: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer, UserRole.viewer)),
    service: ComparisonSetService = Depends(get_comparison_set_service),
) -> ComparisonSetDetailResponse:
    try:
        return await service.get_set(user_id=user.user_id, comparison_set_id=comparison_set_id)
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.patch("/{comparison_set_id}", response_model=ComparisonSetDetailResponse)
async def update_comparison_set(
    comparison_set_id: UUID,
    payload: ComparisonSetUpdateRequest,
    user: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer)),
    service: ComparisonSetService = Depends(get_comparison_set_service),
) -> ComparisonSetDetailResponse:
    try:
        return await service.update_set(
            user_id=user.user_id,
            comparison_set_id=comparison_set_id,
            payload=payload,
        )
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        status_code = status.HTTP_404_NOT_FOUND if "not found" in str(exc).lower() else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.delete("/{comparison_set_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_comparison_set(
    comparison_set_id: UUID,
    user: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer)),
    service: ComparisonSetService = Depends(get_comparison_set_service),
) -> Response:
    try:
        await service.delete_set(user_id=user.user_id, comparison_set_id=comparison_set_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
