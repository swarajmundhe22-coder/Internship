from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import Field

from app.models.common import AuditMetadata, BaseDomainModel
from app.models.environment import EnvironmentInput, EnvironmentRiskResult
from app.models.material import MaterialRead


class SimulationRecordBase(BaseDomainModel):
    material_id: UUID
    environment_id: UUID
    exposed_area_m2: float = Field(gt=0)
    exposure_time_hours: float = Field(gt=0)
    corrosion_rate_mm_per_year: float = Field(ge=0)
    estimated_lifespan_years: float = Field(ge=0)
    accuracy_score: float | None = Field(default=None, ge=0, le=1)
    risk_classification: str = Field(min_length=2, max_length=40)
    version: int = Field(default=1, gt=0)


class SimulationCreate(SimulationRecordBase):
    pass


class SimulationUpdate(BaseDomainModel):
    expected_version: int = Field(gt=0)
    exposed_area_m2: float | None = Field(default=None, gt=0)
    exposure_time_hours: float | None = Field(default=None, gt=0)
    corrosion_rate_mm_per_year: float | None = Field(default=None, ge=0)
    estimated_lifespan_years: float | None = Field(default=None, ge=0)
    accuracy_score: float | None = Field(default=None, ge=0, le=1)
    risk_classification: str | None = Field(default=None, min_length=2, max_length=40)


class SimulationRead(SimulationRecordBase, AuditMetadata):
    pass


class SimulationRequest(BaseDomainModel):
    tenant_id: UUID | None = None
    material: MaterialRead
    environment: EnvironmentInput
    exposed_area_m2: float = Field(gt=0)
    exposure_time_hours: float = Field(gt=0)


class SimulationResult(BaseDomainModel):
    simulation_id: UUID = Field(default_factory=uuid4)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    environment_risk: EnvironmentRiskResult
    corrosion_rate_mm_per_year: float = Field(ge=0)
    estimated_lifespan_years: float = Field(ge=0)
    risk_classification: str
    recommendation_summary: str
