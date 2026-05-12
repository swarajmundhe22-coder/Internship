from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from pydantic import Field, model_validator

from app.models.common import BaseDomainModel


class CountryCode(str, Enum):
    us = "US"
    in_ = "IN"
    cn = "CN"


class ExposureCategory(str, Enum):
    b = "B"
    c = "C"
    d = "D"


class MaterialSystem(str, Enum):
    steel = "steel"
    concrete = "concrete"


class DesignCodeFamily(str, Enum):
    asce7_22 = "ASCE7-22"
    eurocode_in_na = "EUROCODE-IN-NA"
    gb_500 = "GB-50009-50011-50017"


class InfrastructureLocation(BaseDomainModel):
    country_code: CountryCode
    state: str | None = Field(default=None, min_length=2, max_length=80)
    county: str | None = Field(default=None, min_length=2, max_length=80)
    city: str | None = Field(default=None, min_length=2, max_length=80)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class StructuralLoadCaseInput(BaseDomainModel):
    dead_load_kN: float = Field(ge=0)
    live_load_kN: float = Field(ge=0)
    wind_load_kN: float | None = Field(default=None, ge=0)
    seismic_load_kN: float | None = Field(default=None, ge=0)
    snow_load_kN: float = Field(default=0.0, ge=0)
    thermal_load_kN: float = Field(default=0.0, ge=0)


class StructuralCapacityInput(BaseDomainModel):
    ultimate_capacity_kN: float = Field(gt=0)
    serviceability_capacity_kN: float = Field(gt=0)
    member_area_mm2: float | None = Field(default=None, gt=0)
    allowable_stress_mpa: float | None = Field(default=None, gt=0)


class OfficialStationObservation(BaseDomainModel):
    station_id: str = Field(min_length=2, max_length=80)
    wind_speed_mph: float = Field(ge=0, le=200)
    precipitation_intensity_mm_hr: float = Field(ge=1, le=1000)
    pressure_hpa: float = Field(ge=850, le=1100)


class InfrastructureValidationRequest(BaseDomainModel):
    location: InfrastructureLocation
    loads: StructuralLoadCaseInput
    capacities: StructuralCapacityInput
    design_codes: list[DesignCodeFamily] = Field(
        default_factory=lambda: [
            DesignCodeFamily.asce7_22,
            DesignCodeFamily.eurocode_in_na,
            DesignCodeFamily.gb_500,
        ],
        min_length=1,
    )
    material_system: MaterialSystem = MaterialSystem.steel
    exposure_category: ExposureCategory = ExposureCategory.c
    structure_height_ft: float = Field(default=60.0, ge=5, le=1200)
    effective_projected_area_m2: float = Field(default=120.0, gt=0)
    basic_wind_speed_mph_override: float | None = Field(default=None, ge=0, le=200)
    precipitation_intensity_mm_hr_override: float | None = Field(default=None, ge=1, le=1000)
    reference_timestamp_utc: datetime | None = None
    official_station_observation: OfficialStationObservation | None = None

    @model_validator(mode="after")
    def validate_discrete_wind_increment(self) -> "InfrastructureValidationRequest":
        if self.basic_wind_speed_mph_override is not None:
            rounded = round(self.basic_wind_speed_mph_override)
            if abs(rounded - self.basic_wind_speed_mph_override) > 1e-9:
                raise ValueError("basic_wind_speed_mph_override must be in 1 mph increments")
        return self


class WeatherParameterSnapshot(BaseDomainModel):
    source_station_id: str
    fallback_station_id: str | None = None
    basic_wind_speed_mph: float = Field(ge=0, le=200)
    height_adjusted_wind_speed_mph: float = Field(ge=0, le=260)
    exposure_category: ExposureCategory
    seismic_zone: int = Field(ge=0, le=8)
    ss_g: float = Field(ge=0, le=5)
    s1_g: float = Field(ge=0, le=5)
    precipitation_intensity_mm_hr: float = Field(ge=1, le=1000)
    idf_100_year_mm_hr: float = Field(ge=1, le=1000)
    freeze_thaw_cycles: int = Field(ge=0)
    salt_spray_mg_m2_day: float = Field(ge=0)
    so2_deposition_ug_m3: float = Field(ge=0)
    pressure_hpa: float = Field(ge=850, le=1100)
    interpolation_steps: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_discrete_wind_increment(self) -> "WeatherParameterSnapshot":
        rounded = round(self.basic_wind_speed_mph)
        if abs(rounded - self.basic_wind_speed_mph) > 1e-9:
            raise ValueError("basic_wind_speed_mph must be in 1 mph increments")
        return self


class ValidationToleranceCheck(BaseDomainModel):
    station_id: str
    max_error_pct: float = Field(ge=0)
    threshold_pct: float = Field(default=5.0, gt=0)
    within_tolerance: bool
    parameter_error_pct: dict[str, float]


class LimitStateCheckResult(BaseDomainModel):
    limit_state_id: str
    expression: str
    code_reference: str
    design_intent: str
    demand_kN: float = Field(ge=0)
    capacity_kN: float = Field(gt=0)
    utilization_ratio: float = Field(ge=0)
    margin_of_safety: float
    passes: bool


class CodeValidationResult(BaseDomainModel):
    code_family: DesignCodeFamily
    material_system: MaterialSystem
    governing_limit_state_id: str
    passes: bool
    limit_states: list[LimitStateCheckResult] = Field(min_length=1)


class InfrastructureValidationResponse(BaseDomainModel):
    validation_id: UUID = Field(default_factory=uuid4)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    engine_version: str
    location: InfrastructureLocation
    weather: WeatherParameterSnapshot
    tolerance_check: ValidationToleranceCheck | None = None
    code_results: list[CodeValidationResult] = Field(min_length=1)
    overall_passes: bool


class HourlyWeatherUpdateRequest(BaseDomainModel):
    targets: list[InfrastructureLocation] = Field(min_length=1)
    exposure_category: ExposureCategory = ExposureCategory.c


class HourlyWeatherUpdateRecord(BaseDomainModel):
    location: InfrastructureLocation
    snapshot: WeatherParameterSnapshot


class HourlyWeatherUpdateResponse(BaseDomainModel):
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    record_count: int = Field(ge=0)
    audit_log_path: str
    records: list[HourlyWeatherUpdateRecord] = Field(default_factory=list)
