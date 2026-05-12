from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.api.security import require_roles
from app.models.auth import AuthPrincipal, UserRole
from app.models.infrastructure import (
    HourlyWeatherUpdateRequest,
    HourlyWeatherUpdateResponse,
    InfrastructureValidationRequest,
    InfrastructureValidationResponse,
)
from app.services.infrastructure_compliance_pdf_service import InfrastructureCompliancePdfService
from app.services.infrastructure_validation_service import InfrastructureValidationService
from app.services.microclimate_pipeline_service import MicroClimatePipelineService

router = APIRouter(prefix="/infrastructure", tags=["infrastructure"])


@router.post("/validate", response_model=InfrastructureValidationResponse)
async def validate_infrastructure(
    payload: InfrastructureValidationRequest,
    _principal: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer, UserRole.viewer)),
) -> InfrastructureValidationResponse:
    try:
        return InfrastructureValidationService().validate(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc


@router.post("/hourly-update", response_model=HourlyWeatherUpdateResponse)
async def run_hourly_microclimate_update(
    payload: HourlyWeatherUpdateRequest,
    _principal: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer)),
) -> HourlyWeatherUpdateResponse:
    try:
        return MicroClimatePipelineService().run_hourly_update(payload)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc


@router.post("/validate/pdf")
async def validate_infrastructure_pdf(
    payload: InfrastructureValidationRequest,
    _principal: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer, UserRole.viewer)),
) -> Response:
    try:
        validation = InfrastructureValidationService().validate(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    pdf = InfrastructureCompliancePdfService().generate_pdf(validation)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="infrastructure-compliance-{validation.validation_id}.pdf"'
        },
    )
