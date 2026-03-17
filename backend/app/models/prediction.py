from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import Field

from app.models.common import BaseDomainModel


class PredictionTimelinePoint(BaseDomainModel):
    offset_hours: int = Field(ge=0)
    corrosion_rate_mm_per_year: float = Field(ge=0)
    estimated_lifespan_years: float = Field(ge=0)
    risk_score: float = Field(ge=0, le=100)
    risk_classification: str = Field(min_length=2, max_length=40)


class ProjectPredictionCreateRequest(BaseDomainModel):
    simulation_id: UUID | None = None
    horizon_hours: int = Field(default=720, ge=24, le=24 * 365)
    step_hours: int = Field(default=24, ge=1, le=24 * 30)


class ProjectPredictionRead(BaseDomainModel):
    id: UUID = Field(default_factory=uuid4)
    project_id: UUID
    simulation_id: UUID | None = None
    model_name: str
    horizon_hours: int
    step_hours: int
    summary: str
    timeline: list[PredictionTimelinePoint]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
