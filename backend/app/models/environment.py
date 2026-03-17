from pydantic import Field

from app.models.common import AuditMetadata, BaseDomainModel


class EnvironmentInput(BaseDomainModel):
    temperature_c: float = Field(ge=-60, le=150)
    relative_humidity_pct: float = Field(ge=0, le=100)
    chloride_ppm: float = Field(ge=0)
    ph: float = Field(ge=0, le=14)
    dissolved_oxygen_mg_l: float = Field(ge=0)


class EnvironmentBase(BaseDomainModel):
    profile_name: str = Field(min_length=2, max_length=80)
    temperature_c: float = Field(ge=-60, le=150)
    relative_humidity_pct: float = Field(ge=0, le=100)
    chloride_ppm: float = Field(ge=0)
    ph: float = Field(ge=0, le=14)
    dissolved_oxygen_mg_l: float = Field(ge=0)


class EnvironmentCreate(EnvironmentBase):
    pass


class EnvironmentUpdate(BaseDomainModel):
    profile_name: str | None = Field(default=None, min_length=2, max_length=80)
    temperature_c: float | None = Field(default=None, ge=-60, le=150)
    relative_humidity_pct: float | None = Field(default=None, ge=0, le=100)
    chloride_ppm: float | None = Field(default=None, ge=0)
    ph: float | None = Field(default=None, ge=0, le=14)
    dissolved_oxygen_mg_l: float | None = Field(default=None, ge=0)


class EnvironmentRead(EnvironmentBase, AuditMetadata):
    pass


class EnvironmentRiskResult(BaseDomainModel):
    risk_score: float = Field(ge=0, le=100)
    risk_band: str
    rationale: str
