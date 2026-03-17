from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies import get_analytics_repository
from app.api.security import require_roles
from app.models.analytics import (
    AnalyticsSummary,
    RiskDistributionDatum,
    SimulationsOverTimeDatum,
    UsageDatum,
)
from app.models.auth import AuthPrincipal, UserRole
from app.repositories.analytics_repository import AnalyticsRepository
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])


def get_analytics_service(repository: AnalyticsRepository = Depends(get_analytics_repository)) -> AnalyticsService:
    return AnalyticsService(repository=repository)


@router.get("/summary", response_model=AnalyticsSummary)
async def get_summary(
    _principal: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer, UserRole.viewer)),
    service: AnalyticsService = Depends(get_analytics_service),
) -> AnalyticsSummary:
    return await service.summary()


@router.get("/material-usage", response_model=list[UsageDatum])
async def get_material_usage(
    _principal: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer, UserRole.viewer)),
    service: AnalyticsService = Depends(get_analytics_service),
) -> list[UsageDatum]:
    return await service.material_usage()


@router.get("/environment-usage", response_model=list[UsageDatum])
async def get_environment_usage(
    _principal: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer, UserRole.viewer)),
    service: AnalyticsService = Depends(get_analytics_service),
) -> list[UsageDatum]:
    return await service.environment_usage()


@router.get("/risk-distribution", response_model=list[RiskDistributionDatum])
async def get_risk_distribution(
    _principal: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer, UserRole.viewer)),
    service: AnalyticsService = Depends(get_analytics_service),
) -> list[RiskDistributionDatum]:
    return await service.risk_distribution()


@router.get("/simulations-over-time", response_model=list[SimulationsOverTimeDatum])
async def get_simulations_over_time(
    _principal: AuthPrincipal = Depends(require_roles(UserRole.admin, UserRole.engineer, UserRole.viewer)),
    service: AnalyticsService = Depends(get_analytics_service),
) -> list[SimulationsOverTimeDatum]:
    return await service.simulations_over_time()
