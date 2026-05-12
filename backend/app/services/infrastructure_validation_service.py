from __future__ import annotations

from app.algorithms.microclimate_engine import (
    MICROCLIMATE_ENGINE_VERSION,
    interpolate_weather_snapshot,
    out_of_range_parameters,
    tolerance_against_official,
)
from app.algorithms.structural_validation_engine import (
    STRUCTURAL_VALIDATION_ENGINE_VERSION,
    validate_all_codes,
)
from app.models.infrastructure import (
    InfrastructureValidationRequest,
    InfrastructureValidationResponse,
)

INFRASTRUCTURE_VALIDATION_ENGINE_VERSION = (
    f"{STRUCTURAL_VALIDATION_ENGINE_VERSION}+{MICROCLIMATE_ENGINE_VERSION}"
)


class InfrastructureValidationService:
    def validate(self, payload: InfrastructureValidationRequest) -> InfrastructureValidationResponse:
        weather_snapshot = interpolate_weather_snapshot(
            location=payload.location,
            exposure_category=payload.exposure_category,
            structure_height_ft=payload.structure_height_ft,
            basic_wind_speed_mph_override=payload.basic_wind_speed_mph_override,
            precipitation_intensity_mm_hr_override=payload.precipitation_intensity_mm_hr_override,
            reference_timestamp_utc=payload.reference_timestamp_utc,
        )

        range_violations = out_of_range_parameters(weather_snapshot)
        if range_violations:
            raise ValueError(
                "Out-of-range weather parameters detected: "
                + ", ".join(sorted(range_violations))
            )

        tolerance_check = None
        if payload.official_station_observation is not None:
            tolerance_check = tolerance_against_official(
                weather_snapshot,
                payload.official_station_observation,
                threshold_pct=5.0,
            )

        code_results = validate_all_codes(payload, weather_snapshot)
        overall_passes = all(item.passes for item in code_results)
        if tolerance_check is not None:
            overall_passes = overall_passes and tolerance_check.within_tolerance

        return InfrastructureValidationResponse(
            engine_version=INFRASTRUCTURE_VALIDATION_ENGINE_VERSION,
            location=payload.location,
            weather=weather_snapshot,
            tolerance_check=tolerance_check,
            code_results=code_results,
            overall_passes=overall_passes,
        )
