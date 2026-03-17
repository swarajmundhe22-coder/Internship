from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from pydantic import Field

from app.models.common import BaseDomainModel


class InsightAnomaly(BaseDomainModel):
    code: str
    severity: str
    message: str


class ProjectInsightRead(BaseDomainModel):
    project_id: UUID
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    summary: str
    recommendations: list[str]
    anomalies: list[InsightAnomaly]


class ProjectInsightReportExport(BaseDomainModel):
    filename: str
    content: str
