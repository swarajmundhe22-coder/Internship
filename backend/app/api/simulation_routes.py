from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.api.dependencies import (
    get_audit_log_repository,
    get_simulation_repository,
    get_tenant_repository,
    get_visualization_repository,
)
from app.api.security import require_roles
from app.models.auth import AuthPrincipal, UserRole
from app.models.pagination import PaginatedResponse, SimulationListQuery
from app.models.simulation import (
    SimulationCreate,
    SimulationRead,
    SimulationRequest,
    SimulationResult,
    SimulationUpdate,
)
from app.repositories.exceptions import (
    ConcurrencyError,
    ConflictError,
    EntityNotFoundError,
    PersistenceError,
)
from app.services.simulation_record_service import SimulationRecordService
from app.services.simulation_service import SimulationService
from app.repositories.tenant_repository import TenantRepository
from app.repositories.visualization_repository import VisualizationRepository
from app.repositories.audit_log_repository import AuditLogRepository

router = APIRouter(prefix="/simulation", tags=["simulation"])


def get_simulation_record_service(
    repository=Depends(get_simulation_repository),
    tenant_repository: TenantRepository = Depends(get_tenant_repository),
    visualization_repository: VisualizationRepository = Depends(get_visualization_repository),
) -> SimulationRecordService:
    return SimulationRecordService(
        repository=repository,
        tenant_repository=tenant_repository,
        visualization_repository=visualization_repository,
    )


@router.post("", response_model=SimulationRead, status_code=status.HTTP_201_CREATED)
async def create_simulation(
    payload: SimulationCreate,
    principal: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer)),
    service: SimulationRecordService = Depends(get_simulation_record_service),
) -> SimulationRead:
    try:
        return await service.create_simulation(payload, user_id=principal.user_id)
    except ConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except PersistenceError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.get("/{simulation_id}", response_model=SimulationRead)
async def get_simulation(
    simulation_id: UUID,
    _principal: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer, UserRole.viewer)),
    service: SimulationRecordService = Depends(get_simulation_record_service),
) -> SimulationRead:
    try:
        return await service.get_simulation(simulation_id)
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("", response_model=PaginatedResponse[SimulationRead])
async def list_simulations(
    page: int = 1,
    page_size: int = 25,
    material_id: UUID | None = None,
    environment_id: UUID | None = None,
    risk_level: str | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    _principal: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer, UserRole.viewer)),
    service: SimulationRecordService = Depends(get_simulation_record_service),
) -> PaginatedResponse[SimulationRead]:
    query = SimulationListQuery(
        page=page,
        page_size=page_size,
        material_id=material_id,
        environment_id=environment_id,
        risk_level=risk_level,
        created_from=created_from,
        created_to=created_to,
    )
    return await service.list_simulations(query)


@router.put("/{simulation_id}", response_model=SimulationRead)
async def update_simulation(
    simulation_id: UUID,
    payload: SimulationUpdate,
    _principal: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer)),
    service: SimulationRecordService = Depends(get_simulation_record_service),
) -> SimulationRead:
    try:
        return await service.update_simulation(simulation_id, payload)
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ConcurrencyError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.delete("/{simulation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_simulation(
    simulation_id: UUID,
    _principal: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer)),
    service: SimulationRecordService = Depends(get_simulation_record_service),
) -> Response:
    try:
        await service.delete_simulation(simulation_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/predict", response_model=SimulationResult)
async def predict_simulation(
    payload: SimulationRequest,
    principal: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer)),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> SimulationResult:
    result = SimulationService().run_simulation(payload)
    await audit_logs.create(
        event_type="SIMULATION_RUN",
        tenant_id=payload.tenant_id,
        user_id=principal.user_id,
        user_email=principal.email,
        success=True,
        detail=f"endpoint=predict;simulation_id={result.simulation_id}",
    )
    return result


@router.post("/simulate", response_model=SimulationResult)
async def simulate(
    payload: SimulationRequest,
    principal: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer)),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> SimulationResult:
    result = SimulationService().run_simulation(payload)
    await audit_logs.create(
        event_type="SIMULATION_RUN",
        tenant_id=payload.tenant_id,
        user_id=principal.user_id,
        user_email=principal.email,
        success=True,
        detail=f"endpoint=simulate;simulation_id={result.simulation_id}",
    )
    return result
