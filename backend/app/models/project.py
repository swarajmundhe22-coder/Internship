from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.models.common import AuditMetadata, BaseDomainModel
from app.models.pagination import PaginatedResponse


class ProjectBase(BaseDomainModel):
    name: str = Field(min_length=2, max_length=120)


class ProjectCreate(ProjectBase):
    metadata: dict[str, object] | None = None


class ProjectRead(ProjectBase, AuditMetadata):
    user_id: UUID
    metadata: dict[str, object] = Field(default_factory=dict)


class ProjectSimulationSummary(BaseDomainModel):
    simulation_id: UUID
    material: str
    environment: str
    risk_level: str
    lifespan_years: float
    created_at: datetime


class ProjectReportSummary(BaseDomainModel):
    report_id: UUID
    report_uri: str
    simulation_id: UUID
    material: str
    environment: str
    simulation_risk_level: str
    risk_level: str
    lifespan_years: float
    created_at: datetime


class ProjectDetailResponse(BaseDomainModel):
    id: UUID
    name: str
    created_at: datetime
    simulations: PaginatedResponse[ProjectSimulationSummary]


class SaveSimulationToProjectRequest(BaseDomainModel):
    simulation_id: UUID
