from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from pydantic import Field

from app.models.common import BaseDomainModel


class ReportGenerateRequest(BaseDomainModel):
    simulation_id: UUID


class ReportGenerateResponse(BaseDomainModel):
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    simulation_id: UUID
    material: dict[str, str | float]
    environment: dict[str, str | float]
    metrics: dict[str, str | float]
    recommendation_summary: str
    visual_summary: dict[str, list[dict[str, float | str]]]
