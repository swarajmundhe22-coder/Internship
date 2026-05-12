from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.algorithms.microclimate_engine import out_of_range_parameters
from app.services.infrastructure_validation_service import InfrastructureValidationService
from app.models.infrastructure import (
    CountryCode,
    DesignCodeFamily,
    ExposureCategory,
    InfrastructureLocation,
    InfrastructureValidationRequest,
    MaterialSystem,
    StructuralCapacityInput,
    StructuralLoadCaseInput,
)


def _sample_request(country: CountryCode, city: str, state: str, county: str, lat: float, lon: float) -> InfrastructureValidationRequest:
    return InfrastructureValidationRequest(
        location=InfrastructureLocation(
            country_code=country,
            city=city,
            state=state,
            county=county,
            latitude=lat,
            longitude=lon,
        ),
        loads=StructuralLoadCaseInput(
            dead_load_kN=520,
            live_load_kN=170,
            snow_load_kN=8,
            thermal_load_kN=24,
        ),
        capacities=StructuralCapacityInput(
            ultimate_capacity_kN=2300,
            serviceability_capacity_kN=1800,
            member_area_mm2=22000,
            allowable_stress_mpa=225,
        ),
        design_codes=[
            DesignCodeFamily.asce7_22,
            DesignCodeFamily.eurocode_in_na,
            DesignCodeFamily.gb_500,
        ],
        material_system=MaterialSystem.steel,
        exposure_category=ExposureCategory.c,
        structure_height_ft=100,
        effective_projected_area_m2=120,
    )


def run_coverage_gate() -> tuple[bool, dict[str, object]]:
    service = InfrastructureValidationService()
    samples = [
        _sample_request(CountryCode.us, "Miami", "Florida", "Miami-Dade", 25.7617, -80.1918),
        _sample_request(CountryCode.us, "Houston", "Texas", "Harris", 29.7604, -95.3698),
        _sample_request(CountryCode.in_, "Chennai", "Tamil Nadu", "Chennai", 13.0827, 80.2707),
        _sample_request(CountryCode.in_, "Delhi", "Delhi", "New Delhi", 28.6139, 77.2090),
    ]

    required_weather_fields = {
        "basic_wind_speed_mph",
        "height_adjusted_wind_speed_mph",
        "seismic_zone",
        "ss_g",
        "s1_g",
        "precipitation_intensity_mm_hr",
        "idf_100_year_mm_hr",
        "freeze_thaw_cycles",
        "salt_spray_mg_m2_day",
        "so2_deposition_ug_m3",
        "pressure_hpa",
        "interpolation_steps",
    }

    results: list[dict[str, object]] = []
    passed = True

    for sample in samples:
        response = service.validate(sample)
        weather_payload = response.weather.model_dump()
        missing = sorted(field for field in required_weather_fields if field not in weather_payload)
        range_violations = out_of_range_parameters(response.weather)

        sample_pass = len(missing) == 0 and len(range_violations) == 0
        passed = passed and sample_pass

        results.append(
            {
                "country": sample.location.country_code.value,
                "city": sample.location.city,
                "overall_passes": response.overall_passes,
                "missing_weather_fields": missing,
                "range_violations": range_violations,
                "code_result_count": len(response.code_results),
            }
        )

    payload = {
        "passed": passed,
        "sample_count": len(samples),
        "results": results,
    }
    return passed, payload


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fail when infrastructure validation has out-of-range weather values or missing coverage fields.",
    )
    parser.add_argument(
        "--output",
        default="artifacts/security_reports/infrastructure_parameter_coverage.json",
        help="Path to JSON report output.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with code 1 if validation fails.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    passed, payload = run_coverage_gate()

    out_path = Path(args.output)
    if not out_path.is_absolute():
        out_path = (Path(__file__).resolve().parents[1] / out_path).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"Infrastructure parameter coverage gate: {'PASS' if passed else 'FAIL'}")
    print(f"Report: {out_path}")

    if args.strict and not passed:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
