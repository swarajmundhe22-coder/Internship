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
    asset_type: str | None = Field(default=None, min_length=2, max_length=120)
    compliance_standard: str | None = Field(default=None, min_length=2, max_length=80)
    criticality: str | None = Field(default=None, min_length=2, max_length=40)
    region: str | None = Field(default=None, min_length=2, max_length=80)
    uv_index: float | None = Field(default=None, ge=0, le=20)
    mic_activity: str | None = Field(default=None, min_length=2, max_length=20)
    soil_resistivity_ohm_cm: float | None = Field(default=None, gt=0)


class MetricConfidenceInterval(BaseDomainModel):
    lower: float = Field(ge=0)
    upper: float = Field(ge=0)
    confidence_level: float = Field(default=0.9, gt=0, lt=1)


class SimulationUncertaintyBands(BaseDomainModel):
    corrosion_rate_mm_per_year: MetricConfidenceInterval
    design_corrosion_rate_mm_per_year: MetricConfidenceInterval
    estimated_lifespan_years: MetricConfidenceInterval
    composite_risk_score: MetricConfidenceInterval


class SimulationResult(BaseDomainModel):
    simulation_id: UUID = Field(default_factory=uuid4)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    environment_risk: EnvironmentRiskResult
    corrosion_rate_mm_per_year: float = Field(ge=0)
    design_corrosion_rate_mm_per_year: float | None = Field(default=None, ge=0)
    composite_risk_score: float | None = Field(default=None, ge=0, le=100)
    estimated_lifespan_years: float = Field(ge=0)
    risk_classification: str
    recommendation_summary: str
    model_version: str | None = None
    asset_profile: str | None = None
    region_key: str | None = None
    region_name: str | None = None
    initial_thickness_mm: float | None = Field(default=None, gt=0)
    minimum_safe_thickness_mm: float | None = Field(default=None, gt=0)
    service_age_years: float | None = Field(default=None, ge=0)
    service_utilization: float | None = Field(default=None, ge=0)
    calibration_confidence: float | None = Field(default=None, ge=0, le=1)
    uncertainty_bands: SimulationUncertaintyBands | None = None
    operator_guidance: list[str] = Field(default_factory=list)
    fallback_applied: bool = False
    fallback_reason: str | None = None
    recalibration_due_by: datetime | None = None
