from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    get_comparison_set_repository,
    get_prediction_repository,
    get_project_repository,
    get_tenant_repository,
)
from app.api.security import require_roles
from app.database.session import get_db_session
from app.models.auth import AuthPrincipal, UserRole
from app.models.comparison_set import ComparisonSetCreateRequest, ComparisonSetDetailResponse, ComparisonSetListItem
from app.models.project import (
    ProjectCreate,
    ProjectDetailResponse,
    ProjectReportSummary,
    ProjectRead,
    SaveSimulationToProjectRequest,
)
from app.models.pagination import PaginatedResponse, ProjectReportListQuery, ProjectSimulationListQuery
from app.models.prediction import ProjectPredictionCreateRequest, ProjectPredictionRead
from app.models.pagination import ProjectPredictionListQuery
from app.models.insight import ProjectInsightRead
from app.repositories.comparison_set_repository import ComparisonSetRepository
from app.repositories.prediction_repository import PredictionRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.tenant_repository import TenantRepository
from app.services.comparison_service import ComparisonService
from app.services.comparison_set_service import ComparisonSetService
from app.services.prediction_service import PredictionService
from app.services.insight_service import InsightService
from app.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])


def get_project_service(
    repository: ProjectRepository = Depends(get_project_repository),
    tenant_repository: TenantRepository = Depends(get_tenant_repository),
) -> ProjectService:
    return ProjectService(repository=repository, tenant_repository=tenant_repository)


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


def get_prediction_service(
    project_repository: ProjectRepository = Depends(get_project_repository),
    prediction_repository: PredictionRepository = Depends(get_prediction_repository),
) -> PredictionService:
    return PredictionService(
        project_repository=project_repository,
        prediction_repository=prediction_repository,
    )


def get_insight_service(
    project_repository: ProjectRepository = Depends(get_project_repository),
    prediction_repository: PredictionRepository = Depends(get_prediction_repository),
) -> InsightService:
    return InsightService(
        project_repository=project_repository,
        prediction_repository=prediction_repository,
    )


@router.get("", response_model=list[ProjectRead])
async def list_projects(
    user: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer, UserRole.viewer)),
    service: ProjectService = Depends(get_project_service),
) -> list[ProjectRead]:
    return await service.list_projects(user_id=user.user_id)


@router.post("", response_model=ProjectRead)
async def create_project(
    payload: ProjectCreate,
    user: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer)),
    service: ProjectService = Depends(get_project_service),
) -> ProjectRead:
    return await service.create_project(user_id=user.user_id, name=payload.name, metadata=payload.metadata)


@router.get("/{project_id}", response_model=ProjectDetailResponse)
async def get_project_detail(
    project_id: UUID,
    page: int = 1,
    page_size: int = 25,
    material_id: UUID | None = None,
    environment_id: UUID | None = None,
    risk_level: str | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    user: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer, UserRole.viewer)),
    service: ProjectService = Depends(get_project_service),
) -> ProjectDetailResponse:
    query = ProjectSimulationListQuery(
        page=page,
        page_size=page_size,
        material_id=material_id,
        environment_id=environment_id,
        risk_level=risk_level,
        created_from=created_from,
        created_to=created_to,
    )

    try:
        return await service.get_project_detail(user_id=user.user_id, project_id=project_id, query=query)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/{project_id}/simulations")
async def save_simulation_to_project(
    project_id: UUID,
    payload: SaveSimulationToProjectRequest,
    _user: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer)),
    service: ProjectService = Depends(get_project_service),
) -> dict[str, str]:
    await service.save_simulation(project_id=project_id, simulation_id=payload.simulation_id)
    return {"status": "saved"}


@router.post("/{project_id}/simulations/{simulation_id}")
async def attach_simulation_to_project(
    project_id: UUID,
    simulation_id: UUID,
    _user: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer)),
    service: ProjectService = Depends(get_project_service),
) -> dict[str, str]:
    await service.save_simulation(project_id=project_id, simulation_id=simulation_id)
    return {"status": "saved"}


@router.get("/{project_id}/reports", response_model=PaginatedResponse[ProjectReportSummary])
async def list_project_reports(
    project_id: UUID,
    page: int = 1,
    page_size: int = 25,
    simulation_id: UUID | None = None,
    risk_level: str | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    user: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer, UserRole.viewer)),
    service: ProjectService = Depends(get_project_service),
) -> PaginatedResponse[ProjectReportSummary]:
    query = ProjectReportListQuery(
        page=page,
        page_size=page_size,
        simulation_id=simulation_id,
        risk_level=risk_level,
        created_from=created_from,
        created_to=created_to,
    )
    try:
        return await service.list_project_reports(user_id=user.user_id, project_id=project_id, query=query)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{project_id}/comparison-sets", response_model=list[ComparisonSetListItem])
async def list_project_comparison_sets(
    project_id: UUID,
    user: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer, UserRole.viewer)),
    service: ComparisonSetService = Depends(get_comparison_set_service),
) -> list[ComparisonSetListItem]:
    try:
        return await service.list_sets(user_id=user.user_id, project_id=project_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post("/{project_id}/comparison-sets", response_model=ComparisonSetDetailResponse)
async def create_project_comparison_set(
    project_id: UUID,
    payload: ComparisonSetCreateRequest,
    user: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer)),
    service: ComparisonSetService = Depends(get_comparison_set_service),
) -> ComparisonSetDetailResponse:
    try:
        return await service.create_set(
            user_id=user.user_id,
            project_id=project_id,
            name=payload.name,
            simulation_ids=payload.simulation_ids,
        )
    except ValueError as exc:
        status_code = status.HTTP_404_NOT_FOUND if "not found" in str(exc).lower() else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.post("/{project_id}/predict", response_model=ProjectPredictionRead)
async def generate_project_prediction(
    project_id: UUID,
    payload: ProjectPredictionCreateRequest,
    user: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer)),
    service: PredictionService = Depends(get_prediction_service),
) -> ProjectPredictionRead:
    try:
        return await service.generate_prediction(user_id=user.user_id, project_id=project_id, payload=payload)
    except ValueError as exc:
        status_code = status.HTTP_404_NOT_FOUND if "not found" in str(exc).lower() else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.get("/{project_id}/predictions", response_model=PaginatedResponse[ProjectPredictionRead])
async def list_project_predictions(
    project_id: UUID,
    page: int = 1,
    page_size: int = 25,
    simulation_id: UUID | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    user: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer, UserRole.viewer)),
    service: PredictionService = Depends(get_prediction_service),
) -> PaginatedResponse[ProjectPredictionRead]:
    query = ProjectPredictionListQuery(
        page=page,
        page_size=page_size,
        simulation_id=simulation_id,
        created_from=created_from,
        created_to=created_to,
    )
    try:
        return await service.list_predictions(user_id=user.user_id, project_id=project_id, query=query)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{project_id}/predictions/export")
async def export_project_predictions(
    project_id: UUID,
    format: str = "csv",
    user: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer, UserRole.viewer)),
    service: PredictionService = Depends(get_prediction_service),
) -> Response:
    try:
        filename, media_type, payload = await service.export_predictions(
            user_id=user.user_id,
            project_id=project_id,
            format=format,
        )
        return Response(
            content=payload,
            media_type=media_type,
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
    except ValueError as exc:
        status_code = status.HTTP_404_NOT_FOUND if "not found" in str(exc).lower() else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.get("/{project_id}/insights", response_model=ProjectInsightRead)
async def get_project_insights(
    project_id: UUID,
    user: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer, UserRole.viewer)),
    service: InsightService = Depends(get_insight_service),
) -> ProjectInsightRead:
    try:
        return await service.get_project_insights(user_id=user.user_id, project_id=project_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{project_id}/insights/report")
async def export_project_insights_report(
    project_id: UUID,
    user: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer, UserRole.viewer)),
    service: InsightService = Depends(get_insight_service),
) -> Response:
    try:
        report = await service.export_insight_report(user_id=user.user_id, project_id=project_id)
        return Response(
            content=report.content,
            media_type="text/plain",
            headers={"Content-Disposition": f'attachment; filename="{report.filename}"'},
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
