from datetime import datetime, timezone
from uuid import UUID

from pydantic import Field

from app.models.common import AuditMetadata, BaseDomainModel


class ReportBase(BaseDomainModel):
    simulation_id: UUID
    report_uri: str = Field(min_length=3)
    status: str = Field(default="pending", min_length=2, max_length=30)
    version: int = Field(default=1, gt=0)


class ReportCreate(ReportBase):
    pass


class ReportUpdate(BaseDomainModel):
    expected_version: int = Field(gt=0)
    report_uri: str | None = Field(default=None, min_length=3)
    status: str | None = Field(default=None, min_length=2, max_length=30)


class ReportRecordRead(ReportBase, AuditMetadata):
    pass


class ReportRead(BaseDomainModel):
    report_id: UUID
    simulation_id: UUID
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    report_uri: str = Field(description="Future object storage URI for generated report.")
    status: str = Field(default="pending")
