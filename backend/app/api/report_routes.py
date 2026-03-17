from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_report_repository, get_webhook_repository
from app.api.security import require_roles
from app.models.auth import AuthPrincipal, UserRole
from app.database.session import get_db_session
from app.models.generated_report import ReportGenerateRequest, ReportGenerateResponse
from app.models.pagination import PaginatedResponse, ReportListQuery
from app.models.report import ReportCreate, ReportRecordRead, ReportUpdate
from app.repositories.exceptions import (
    ConcurrencyError,
    ConflictError,
    EntityNotFoundError,
    PersistenceError,
)
from app.services.report_record_service import ReportRecordService
from app.services.report_builder_service import ReportBuilderService
from app.services.report_pdf_service import ReportPdfService
from app.services.webhook_service import WebhookService

router = APIRouter(prefix="/reports", tags=["reports"])


def get_report_service(
    repository=Depends(get_report_repository),
) -> ReportRecordService:
    return ReportRecordService(repository=repository)


def get_webhook_service(
    repository=Depends(get_webhook_repository),
) -> WebhookService:
    return WebhookService(repository=repository)


@router.post("", response_model=ReportRecordRead, status_code=status.HTTP_201_CREATED)
async def create_report(
    payload: ReportCreate,
    _principal: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer)),
    service: ReportRecordService = Depends(get_report_service),
    webhook_service: WebhookService = Depends(get_webhook_service),
) -> ReportRecordRead:
    try:
        report = await service.create_report(payload)
        if report.status.lower() in {"generated", "completed"}:
            await webhook_service.trigger_event(
                event_type="report.completed",
                payload={
                    "report_id": str(report.id),
                    "simulation_id": str(report.simulation_id),
                    "status": report.status,
                    "generated_at": report.created_at.isoformat(),
                },
            )
        return report
    except ConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except PersistenceError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc


@router.post("/generate", response_model=ReportGenerateResponse)
async def generate_report_payload(
    payload: ReportGenerateRequest,
    _principal: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer)),
    session: AsyncSession = Depends(get_db_session),
) -> ReportGenerateResponse:
    service = ReportBuilderService(session=session)
    try:
        return await service.build(payload.simulation_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{report_id}", response_model=ReportRecordRead)
async def get_report(
    report_id: UUID,
    _principal: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer, UserRole.viewer)),
    service: ReportRecordService = Depends(get_report_service),
) -> ReportRecordRead:
    try:
        return await service.get_report(report_id)
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("", response_model=PaginatedResponse[ReportRecordRead])
async def list_reports(
    page: int = 1,
    page_size: int = 25,
    simulation_id: UUID | None = None,
    created_from: datetime | None = None,
    created_to: datetime | None = None,
    _principal: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer, UserRole.viewer)),
    service: ReportRecordService = Depends(get_report_service),
) -> PaginatedResponse[ReportRecordRead]:
    query = ReportListQuery(
        page=page,
        page_size=page_size,
        simulation_id=simulation_id,
        created_from=created_from,
        created_to=created_to,
    )
    return await service.list_reports(query)


@router.put("/{report_id}", response_model=ReportRecordRead)
async def update_report(
    report_id: UUID,
    payload: ReportUpdate,
    _principal: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer)),
    service: ReportRecordService = Depends(get_report_service),
    webhook_service: WebhookService = Depends(get_webhook_service),
) -> ReportRecordRead:
    try:
        report = await service.update_report(report_id, payload)
        if report.status.lower() in {"generated", "completed"}:
            await webhook_service.trigger_event(
                event_type="report.completed",
                payload={
                    "report_id": str(report.id),
                    "simulation_id": str(report.simulation_id),
                    "status": report.status,
                    "generated_at": report.created_at.isoformat(),
                },
            )
        return report
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ConcurrencyError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except ConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.delete("/{report_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_report(
    report_id: UUID,
    _principal: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer)),
    service: ReportRecordService = Depends(get_report_service),
) -> Response:
    try:
        await service.delete_report(report_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/{report_id}/pdf")
async def export_report_pdf(
    report_id: UUID,
    _principal: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer, UserRole.viewer)),
    service: ReportRecordService = Depends(get_report_service),
) -> Response:
    try:
        report = await service.get_report(report_id)
        pdf_bytes = ReportPdfService().generate_pdf(report)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="report-{report_id}.pdf"'},
        )
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
