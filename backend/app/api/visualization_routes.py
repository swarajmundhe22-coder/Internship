from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_audit_log_repository, get_visualization_repository
from app.api.security import require_roles
from app.models.auth import AuthPrincipal, UserRole
from app.models.visualization import (
    VisualizationExportRequest,
    VisualizationExportResponse,
    VisualizationPlaybackResponse,
    VisualizationRead,
    VisualizationRequest,
)
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.visualization_repository import VisualizationRepository
from app.services.visualization_service import VisualizationService

router = APIRouter(prefix="/visualization", tags=["visualization"])

CANONICAL_EVENTS = {
    "generated": "VISUALIZATION_GENERATED",
    "playback": "PLAYBACK_INITIATED",
    "export": "EXPORT_COMPLETED",
}

LEGACY_EVENTS = {
    "generated": "visualization.generated",
    "playback": "visualization.playback",
    "export": "visualization.export",
}


def get_visualization_service(
    repository: VisualizationRepository = Depends(get_visualization_repository),
) -> VisualizationService:
    return VisualizationService(repository=repository)


def _build_log_detail(*, tenant_id: object, simulation_id: object, mode: object, extra: str | None = None) -> str:
    base = f"tenant_id={tenant_id};simulation_id={simulation_id};mode={mode}"
    if extra:
        return f"{base};{extra}"
    return base


async def _log_with_alias(
    *,
    audit_logs: AuditLogRepository,
    event_key: str,
    success: bool,
    principal: AuthPrincipal,
    detail: str,
) -> None:
    canonical = CANONICAL_EVENTS[event_key]
    legacy = LEGACY_EVENTS[event_key]
    await audit_logs.create(
        event_type=canonical,
        success=success,
        user_id=principal.user_id,
        user_email=principal.email,
        detail=detail,
    )
    await audit_logs.create(
        event_type=legacy,
        success=success,
        user_id=principal.user_id,
        user_email=principal.email,
        detail=f"alias_of={canonical};{detail}",
    )


@router.post("/twin", response_model=VisualizationRead)
async def generate_digital_twin(
    payload: VisualizationRequest,
    principal: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer, UserRole.viewer)),
    service: VisualizationService = Depends(get_visualization_service),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> VisualizationRead:
    try:
        twin = await service.generate_twin(
            principal=principal,
            simulation_id=payload.simulation_id,
            tenant_id=payload.tenant_id,
        )
        await _log_with_alias(
            audit_logs=audit_logs,
            event_key="generated",
            success=True,
            principal=principal,
            detail=_build_log_detail(
                tenant_id=payload.tenant_id,
                simulation_id=payload.simulation_id,
                mode=payload.mode,
                extra=f"status={twin.status};overlay_accuracy={twin.overlay_accuracy}",
            ),
        )
        return twin
    except ValueError as exc:
        await _log_with_alias(
            audit_logs=audit_logs,
            event_key="generated",
            success=False,
            principal=principal,
            detail=_build_log_detail(
                tenant_id=payload.tenant_id,
                simulation_id=payload.simulation_id,
                mode=payload.mode,
                extra=f"error={str(exc)}",
            ),
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/playback", response_model=VisualizationPlaybackResponse)
async def foresight_playback(
    payload: VisualizationRequest,
    principal: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer, UserRole.viewer)),
    service: VisualizationService = Depends(get_visualization_service),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> VisualizationPlaybackResponse:
    try:
        playback = await service.playback(
            principal=principal,
            simulation_id=payload.simulation_id,
            tenant_id=payload.tenant_id,
            mode=payload.mode,
        )
        await _log_with_alias(
            audit_logs=audit_logs,
            event_key="playback",
            success=True,
            principal=principal,
            detail=_build_log_detail(
                tenant_id=payload.tenant_id,
                simulation_id=payload.simulation_id,
                mode=payload.mode,
                extra=f"status={playback.status}",
            ),
        )
        return playback
    except ValueError as exc:
        await _log_with_alias(
            audit_logs=audit_logs,
            event_key="playback",
            success=False,
            principal=principal,
            detail=_build_log_detail(
                tenant_id=payload.tenant_id,
                simulation_id=payload.simulation_id,
                mode=payload.mode,
                extra=f"error={str(exc)}",
            ),
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/export", response_model=VisualizationExportResponse)
async def export_visualization(
    payload: VisualizationExportRequest,
    principal: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer)),
    service: VisualizationService = Depends(get_visualization_service),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> VisualizationExportResponse:
    try:
        export_result = await service.export(
            principal=principal,
            simulation_id=payload.simulation_id,
            tenant_id=payload.tenant_id,
            mode=payload.mode,
            file_type=payload.file_type,
        )
        await _log_with_alias(
            audit_logs=audit_logs,
            event_key="export",
            success=True,
            principal=principal,
            detail=_build_log_detail(
                tenant_id=payload.tenant_id,
                simulation_id=payload.simulation_id,
                mode=payload.mode,
                extra=(
                    f"file_type={export_result.export.file_type};"
                    f"file_uri={export_result.export.file_uri}"
                ),
            ),
        )
        return export_result
    except ValueError as exc:
        await _log_with_alias(
            audit_logs=audit_logs,
            event_key="export",
            success=False,
            principal=principal,
            detail=_build_log_detail(
                tenant_id=payload.tenant_id,
                simulation_id=payload.simulation_id,
                mode=payload.mode,
                extra=f"file_type={payload.file_type};error={str(exc)}",
            ),
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
