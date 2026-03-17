from __future__ import annotations

from app.models.analytics import (
    AnalyticsSummary,
    RiskDistributionDatum,
    SimulationsOverTimeDatum,
    UsageDatum,
)
from app.repositories.analytics_repository import AnalyticsRepository


class AnalyticsService:
    def __init__(self, repository: AnalyticsRepository) -> None:
        self.repository = repository

    async def summary(self) -> AnalyticsSummary:
        return await self.repository.summary()

    async def material_usage(self) -> list[UsageDatum]:
        return await self.repository.material_usage()

    async def environment_usage(self) -> list[UsageDatum]:
        return await self.repository.environment_usage()

    async def risk_distribution(self) -> list[RiskDistributionDatum]:
        return await self.repository.risk_distribution()

    async def simulations_over_time(self) -> list[SimulationsOverTimeDatum]:
        return await self.repository.simulations_over_time()
