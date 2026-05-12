from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.models.infrastructure import CountryCode, ExposureCategory, HourlyWeatherUpdateRequest, InfrastructureLocation
from app.services.microclimate_pipeline_service import MicroClimatePipelineService


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run hourly microclimate update pipeline and write auditable output.")
    parser.add_argument(
        "--output",
        default="artifacts/security_reports/hourly_microclimate_update.json",
        help="Path to JSON output file.",
    )
    parser.add_argument(
        "--exposure",
        default="C",
        choices=["B", "C", "D"],
        help="ASCE exposure category for wind-height adjustment.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    exposure = ExposureCategory(args.exposure)

    request = HourlyWeatherUpdateRequest(
        exposure_category=exposure,
        targets=[
            InfrastructureLocation(
                country_code=CountryCode.us,
                city="Miami",
                state="Florida",
                county="Miami-Dade",
                latitude=25.7617,
                longitude=-80.1918,
            ),
            InfrastructureLocation(
                country_code=CountryCode.in_,
                city="Chennai",
                state="Tamil Nadu",
                county="Chennai",
                latitude=13.0827,
                longitude=80.2707,
            ),
        ],
    )

    response = MicroClimatePipelineService().run_hourly_update(request)

    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = (Path(__file__).resolve().parents[1] / output_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(response.model_dump_json(indent=2), encoding="utf-8")

    print(f"Hourly update records: {response.record_count}")
    print(f"Audit log: {response.audit_log_path}")
    print(f"JSON output: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
