from __future__ import annotations

from app.models.common import BaseDomainModel


class AnalyticsSummary(BaseDomainModel):
    total_simulations: int
    total_reports: int
    high_risk_count: int


class UsageDatum(BaseDomainModel):
    name: str
    count: int


class RiskDistributionDatum(BaseDomainModel):
    risk_level: str
    count: int


class SimulationsOverTimeDatum(BaseDomainModel):
    bucket: str
    count: int
