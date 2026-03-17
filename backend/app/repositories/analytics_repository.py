from __future__ import annotations

from collections import Counter

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import EnvironmentEntity, MaterialEntity, ReportEntity, SimulationEntity
from app.models.analytics import (
    AnalyticsSummary,
    RiskDistributionDatum,
    SimulationsOverTimeDatum,
    UsageDatum,
)


class AnalyticsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def summary(self) -> AnalyticsSummary:
        total_simulations = int((await self.session.execute(select(func.count()).select_from(SimulationEntity))).scalar_one())
        total_reports = int((await self.session.execute(select(func.count()).select_from(ReportEntity))).scalar_one())
        high_risk_count = int(
            (
                await self.session.execute(
                    select(func.count()).select_from(SimulationEntity).where(
                        SimulationEntity.risk_classification.in_(["high", "critical"])
                    )
                )
            ).scalar_one()
        )
        return AnalyticsSummary(
            total_simulations=total_simulations,
            total_reports=total_reports,
            high_risk_count=high_risk_count,
        )

    async def material_usage(self) -> list[UsageDatum]:
        statement = (
            select(MaterialEntity.name, func.count(SimulationEntity.id).label("count"))
            .join(SimulationEntity, SimulationEntity.material_id == MaterialEntity.id)
            .group_by(MaterialEntity.name)
            .order_by(func.count(SimulationEntity.id).desc())
        )
        rows = (await self.session.execute(statement)).all()
        return [UsageDatum(name=str(row[0]), count=int(row[1])) for row in rows]

    async def environment_usage(self) -> list[UsageDatum]:
        statement = (
            select(EnvironmentEntity.profile_name, func.count(SimulationEntity.id).label("count"))
            .join(SimulationEntity, SimulationEntity.environment_id == EnvironmentEntity.id)
            .group_by(EnvironmentEntity.profile_name)
            .order_by(func.count(SimulationEntity.id).desc())
        )
        rows = (await self.session.execute(statement)).all()
        return [UsageDatum(name=str(row[0]), count=int(row[1])) for row in rows]

    async def risk_distribution(self) -> list[RiskDistributionDatum]:
        statement = (
            select(SimulationEntity.risk_classification, func.count(SimulationEntity.id).label("count"))
            .group_by(SimulationEntity.risk_classification)
            .order_by(func.count(SimulationEntity.id).desc())
        )
        rows = (await self.session.execute(statement)).all()
        return [RiskDistributionDatum(risk_level=str(row[0]), count=int(row[1])) for row in rows]

    async def simulations_over_time(self) -> list[SimulationsOverTimeDatum]:
        rows = (await self.session.execute(select(SimulationEntity.created_at))).scalars().all()
        bucket_counts = Counter(dt.strftime("%Y-%m") for dt in rows)
        return [
            SimulationsOverTimeDatum(bucket=bucket, count=count)
            for bucket, count in sorted(bucket_counts.items())
        ]
