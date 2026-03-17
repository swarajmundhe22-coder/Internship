from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.api.security import require_roles
from app.models.auth import AuthPrincipal, UserRole
from app.api.dependencies import get_material_repository
from app.models.material import MaterialCreate, MaterialRead, MaterialUpdate
from app.models.pagination import MaterialListQuery, PaginatedResponse
from app.repositories.exceptions import ConflictError, EntityNotFoundError, PersistenceError
from app.services.material_service import MaterialService

router = APIRouter(prefix="/materials", tags=["materials"])


def get_material_service(
    repository=Depends(get_material_repository),
) -> MaterialService:
    return MaterialService(repository=repository)


@router.post("", response_model=MaterialRead, status_code=status.HTTP_201_CREATED)
async def create_material(
    payload: MaterialCreate,
    _principal: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer)),
    service: MaterialService = Depends(get_material_service),
) -> MaterialRead:
    try:
        return await service.create_material(payload)
    except ConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except PersistenceError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get("/{material_id}", response_model=MaterialRead)
async def get_material(
    material_id: UUID,
    _principal: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer, UserRole.viewer)),
    service: MaterialService = Depends(get_material_service),
) -> MaterialRead:
    try:
        return await service.get_material(material_id)
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("", response_model=PaginatedResponse[MaterialRead])
async def list_materials(
    page: int = 1,
    page_size: int = 25,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    _principal: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer, UserRole.viewer)),
    service: MaterialService = Depends(get_material_service),
) -> PaginatedResponse[MaterialRead]:
    query = MaterialListQuery(
        page=page,
        page_size=page_size,
        created_from=created_from,
        created_to=created_to,
    )
    return await service.list_materials(query)


@router.put("/{material_id}", response_model=MaterialRead)
async def update_material(
    material_id: UUID,
    payload: MaterialUpdate,
    _principal: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer)),
    service: MaterialService = Depends(get_material_service),
) -> MaterialRead:
    try:
        return await service.update_material(material_id, payload)
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.delete("/{material_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_material(
    material_id: UUID,
    _principal: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer)),
    service: MaterialService = Depends(get_material_service),
) -> Response:
    try:
        await service.delete_material(material_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
