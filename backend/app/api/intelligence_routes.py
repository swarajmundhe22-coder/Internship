from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from app.api.dependencies import get_audit_log_repository, get_intelligence_repository
from app.api.security import require_roles
from app.models.auth import AuthPrincipal, UserRole
from app.models.intelligence import (
    AtlasExportJobRequest,
    AtlasExportJobResponse,
    AtlasExportResponse,
    AtlasGenerateResponse,
    AtlasLatestQuery,
    AtlasLatestResponse,
    AtlasRequest,
    IoTStreamIngestRequest,
    IoTStreamIngestResponse,
    IoTIngestRequest,
    IoTIngestResponse,
    MaintenanceScheduleRequest,
    MaintenanceScheduleResponse,
    OpsSloResponse,
    SatelliteProviderSyncRequest,
    SatelliteProviderSyncResponse,
    SatelliteIngestRequest,
    SatelliteIngestResponse,
)
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.intelligence_repository import IntelligenceRepository
from app.services.intelligence_service import IntelligenceService

router = APIRouter(prefix="/intelligence", tags=["intelligence"])


def get_intelligence_service(
    repository: IntelligenceRepository = Depends(get_intelligence_repository),
) -> IntelligenceService:
    return IntelligenceService(repository=repository)


async def _log_event(
    *,
    repository: AuditLogRepository,
    event_type: str,
    principal: AuthPrincipal,
    tenant_id,
    success: bool,
    detail: str,
) -> None:
    await repository.create(
        event_type=event_type,
        tenant_id=tenant_id,
        user_id=principal.user_id,
        user_email=principal.email,
        success=success,
        detail=detail,
    )


@router.post("/iot/ingest", response_model=IoTIngestResponse)
async def ingest_iot(
    payload: IoTIngestRequest,
    principal: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer)),
    service: IntelligenceService = Depends(get_intelligence_service),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> IoTIngestResponse:
    try:
        result = await service.ingest_iot(principal=principal, payload=payload)
        await _log_event(
            repository=audit_logs,
            event_type="IOT_INGESTED",
            principal=principal,
            tenant_id=payload.tenant_id,
            success=True,
            detail=f"sensor_id={payload.sensor_id}",
        )
        return result
    except ValueError as exc:
        await _log_event(
            repository=audit_logs,
            event_type="IOT_INGESTED",
            principal=principal,
            tenant_id=payload.tenant_id,
            success=False,
            detail=f"sensor_id={payload.sensor_id};error={str(exc)}",
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/iot/connectors/ingest", response_model=IoTStreamIngestResponse)
async def ingest_iot_connector_stream(
    payload: IoTStreamIngestRequest,
    principal: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer)),
    service: IntelligenceService = Depends(get_intelligence_service),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> IoTStreamIngestResponse:
    try:
        result = await service.ingest_iot_stream(principal=principal, payload=payload)
        await _log_event(
            repository=audit_logs,
            event_type="IOT_CONNECTOR_STREAM_INGESTED",
            principal=principal,
            tenant_id=payload.tenant_id,
            success=True,
            detail=(
                f"connector_type={payload.connector_type};"
                f"accepted_events={result.accepted_events};dead_lettered_events={result.dead_lettered_events}"
            ),
        )
        return result
    except ValueError as exc:
        await _log_event(
            repository=audit_logs,
            event_type="IOT_CONNECTOR_STREAM_INGESTED",
            principal=principal,
            tenant_id=payload.tenant_id,
            success=False,
            detail=f"connector_type={payload.connector_type};error={str(exc)}",
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/satellite/ingest", response_model=SatelliteIngestResponse)
async def ingest_satellite(
    payload: SatelliteIngestRequest,
    principal: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer)),
    service: IntelligenceService = Depends(get_intelligence_service),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> SatelliteIngestResponse:
    try:
        result = await service.ingest_satellite(principal=principal, payload=payload)
        await _log_event(
            repository=audit_logs,
            event_type="SATELLITE_INGESTED",
            principal=principal,
            tenant_id=payload.tenant_id,
            success=True,
            detail=f"region={payload.region};source={payload.imagery_source}",
        )
        return result
    except ValueError as exc:
        await _log_event(
            repository=audit_logs,
            event_type="SATELLITE_INGESTED",
            principal=principal,
            tenant_id=payload.tenant_id,
            success=False,
            detail=f"region={payload.region};source={payload.imagery_source};error={str(exc)}",
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/satellite/providers/sync", response_model=SatelliteProviderSyncResponse)
async def sync_satellite_provider(
    payload: SatelliteProviderSyncRequest,
    principal: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer)),
    service: IntelligenceService = Depends(get_intelligence_service),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> SatelliteProviderSyncResponse:
    try:
        result = await service.sync_satellite_provider(principal=principal, payload=payload)
        await _log_event(
            repository=audit_logs,
            event_type="SATELLITE_PROVIDER_SYNCED",
            principal=principal,
            tenant_id=payload.tenant_id,
            success=True,
            detail=f"provider={payload.provider};region={payload.region};frames={result.frames_ingested}",
        )
        return result
    except ValueError as exc:
        await _log_event(
            repository=audit_logs,
            event_type="SATELLITE_PROVIDER_SYNCED",
            principal=principal,
            tenant_id=payload.tenant_id,
            success=False,
            detail=f"provider={payload.provider};region={payload.region};error={str(exc)}",
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/atlas/generate", response_model=AtlasGenerateResponse)
async def generate_atlas(
    payload: AtlasRequest,
    principal: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer, UserRole.viewer)),
    service: IntelligenceService = Depends(get_intelligence_service),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> AtlasGenerateResponse:
    try:
        result = await service.generate_atlas(principal=principal, payload=payload)
        await _log_event(
            repository=audit_logs,
            event_type="ATLAS_GENERATED",
            principal=principal,
            tenant_id=payload.tenant_id,
            success=True,
            detail=f"region={payload.region};export_type={payload.export_type}",
        )
        return result
    except ValueError as exc:
        await _log_event(
            repository=audit_logs,
            event_type="ATLAS_GENERATED",
            principal=principal,
            tenant_id=payload.tenant_id,
            success=False,
            detail=f"region={payload.region};export_type={payload.export_type};error={str(exc)}",
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/atlas/export", response_model=AtlasExportResponse)
async def export_atlas(
    payload: AtlasRequest,
    principal: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer)),
    service: IntelligenceService = Depends(get_intelligence_service),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> AtlasExportResponse:
    try:
        result = await service.export_atlas(principal=principal, payload=payload)
        await _log_event(
            repository=audit_logs,
            event_type="ATLAS_EXPORTED",
            principal=principal,
            tenant_id=payload.tenant_id,
            success=True,
            detail=f"region={payload.region};export_type={payload.export_type}",
        )
        return result
    except ValueError as exc:
        await _log_event(
            repository=audit_logs,
            event_type="ATLAS_EXPORTED",
            principal=principal,
            tenant_id=payload.tenant_id,
            success=False,
            detail=f"region={payload.region};export_type={payload.export_type};error={str(exc)}",
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/atlas/export/jobs", response_model=AtlasExportJobResponse)
async def enqueue_atlas_export_job(
    payload: AtlasExportJobRequest,
    background_tasks: BackgroundTasks,
    principal: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer)),
    service: IntelligenceService = Depends(get_intelligence_service),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> AtlasExportJobResponse:
    try:
        job = await service.enqueue_export_job(principal=principal, payload=payload)
        background_tasks.add_task(service.process_export_job, job_id=job.job_id)
        await _log_event(
            repository=audit_logs,
            event_type="ATLAS_EXPORT_JOB_ENQUEUED",
            principal=principal,
            tenant_id=payload.tenant_id,
            success=True,
            detail=f"job_id={job.job_id};region={payload.region};export_type={payload.export_type}",
        )
        return job
    except ValueError as exc:
        await _log_event(
            repository=audit_logs,
            event_type="ATLAS_EXPORT_JOB_ENQUEUED",
            principal=principal,
            tenant_id=payload.tenant_id,
            success=False,
            detail=f"region={payload.region};export_type={payload.export_type};error={str(exc)}",
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/atlas/export/jobs/{job_id}", response_model=AtlasExportJobResponse)
async def get_atlas_export_job(
    job_id: UUID,
    principal: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer, UserRole.viewer)),
    service: IntelligenceService = Depends(get_intelligence_service),
) -> AtlasExportJobResponse:
    try:
        return await service.get_export_job(principal=principal, job_id=job_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/atlas/latest", response_model=AtlasLatestResponse)
async def get_latest_atlas(
    tenant_id: UUID,
    region: str,
    principal: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer, UserRole.viewer)),
    service: IntelligenceService = Depends(get_intelligence_service),
) -> AtlasLatestResponse:
    try:
        query = AtlasLatestQuery(tenant_id=tenant_id, region=region)
        return await service.get_latest_atlas(principal=principal, query=query)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/ops/slo", response_model=OpsSloResponse)
async def get_ops_slo_dashboard(
    tenant_id: UUID,
    window_hours: int = 24,
    principal: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer, UserRole.viewer)),
    service: IntelligenceService = Depends(get_intelligence_service),
) -> OpsSloResponse:
    try:
        return await service.get_ops_slo(principal=principal, tenant_id=tenant_id, window_hours=window_hours)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/maintenance/schedule", response_model=MaintenanceScheduleResponse)
async def schedule_maintenance(
    payload: MaintenanceScheduleRequest,
    principal: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer)),
    service: IntelligenceService = Depends(get_intelligence_service),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> MaintenanceScheduleResponse:
    try:
        result = await service.schedule_maintenance(principal=principal, payload=payload)
        await _log_event(
            repository=audit_logs,
            event_type="MAINTENANCE_SCHEDULED",
            principal=principal,
            tenant_id=payload.tenant_id,
            success=True,
            detail=(
                f"asset_id={payload.asset_id};risk_score={payload.risk_score};"
                f"recommendation={result.recommendation}"
            ),
        )
        return result
    except ValueError as exc:
        await _log_event(
            repository=audit_logs,
            event_type="MAINTENANCE_SCHEDULED",
            principal=principal,
            tenant_id=payload.tenant_id,
            success=False,
            detail=f"asset_id={payload.asset_id};risk_score={payload.risk_score};error={str(exc)}",
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
