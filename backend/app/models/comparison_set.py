from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from pydantic import Field

from app.models.common import BaseDomainModel
from app.models.comparison import SimulationComparisonResponse


class ComparisonSetCreateRequest(BaseDomainModel):
    name: str = Field(min_length=2, max_length=140)
    simulation_ids: list[UUID] = Field(min_length=2, max_length=4)


class ComparisonSetUpdateRequest(BaseDomainModel):
    name: str | None = Field(default=None, min_length=2, max_length=140)
    simulation_ids: list[UUID] | None = Field(default=None, min_length=2, max_length=4)


class ComparisonSetListItem(BaseDomainModel):
    id: UUID
    project_id: UUID
    name: str
    created_by: UUID
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    simulation_count: int


class ComparisonSetDetailResponse(BaseDomainModel):
    id: UUID
    project_id: UUID
    name: str
    created_by: UUID
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    simulation_ids: list[UUID]
    comparisons: list[SimulationComparisonResponse]
