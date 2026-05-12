from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

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
from app.services.infrastructure_compliance_pdf_service import InfrastructureCompliancePdfService
from app.services.infrastructure_validation_service import InfrastructureValidationService


def _base_request(location: InfrastructureLocation) -> InfrastructureValidationRequest:
    return InfrastructureValidationRequest(
        location=location,
        loads=StructuralLoadCaseInput(
            dead_load_kN=620,
            live_load_kN=210,
            snow_load_kN=5,
            thermal_load_kN=30,
        ),
        capacities=StructuralCapacityInput(
            ultimate_capacity_kN=2600,
            serviceability_capacity_kN=2100,
            member_area_mm2=26000,
            allowable_stress_mpa=235,
        ),
        design_codes=[
            DesignCodeFamily.asce7_22,
            DesignCodeFamily.eurocode_in_na,
            DesignCodeFamily.gb_500,
        ],
        material_system=MaterialSystem.steel,
        exposure_category=ExposureCategory.c,
        structure_height_ft=140,
        effective_projected_area_m2=150,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate infrastructure validation demo outputs for Miami (US) and Chennai (IN).",
    )
    parser.add_argument(
        "--output-dir",
        default="artifacts/performance_reports",
        help="Output directory for demo JSON and PDF artifacts.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = (Path(__file__).resolve().parents[1] / output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    service = InfrastructureValidationService()
    pdf_service = InfrastructureCompliancePdfService()

    miami = InfrastructureLocation(
        country_code=CountryCode.us,
        city="Miami",
        state="Florida",
        county="Miami-Dade",
        latitude=25.7617,
        longitude=-80.1918,
    )
    chennai = InfrastructureLocation(
        country_code=CountryCode.in_,
        city="Chennai",
        state="Tamil Nadu",
        county="Chennai",
        latitude=13.0827,
        longitude=80.2707,
    )

    miami_result = service.validate(_base_request(miami))
    chennai_result = service.validate(_base_request(chennai))

    miami_pdf = pdf_service.generate_pdf(miami_result)
    chennai_pdf = pdf_service.generate_pdf(chennai_result)

    miami_pdf_path = output_dir / "infrastructure_demo_miami.pdf"
    chennai_pdf_path = output_dir / "infrastructure_demo_chennai.pdf"
    miami_pdf_path.write_bytes(miami_pdf)
    chennai_pdf_path.write_bytes(chennai_pdf)

    summary = {
        "miami": miami_result.model_dump(mode="json"),
        "chennai": chennai_result.model_dump(mode="json"),
        "artifacts": {
            "miami_pdf": str(miami_pdf_path),
            "chennai_pdf": str(chennai_pdf_path),
        },
    }

    summary_path = output_dir / "infrastructure_demo_miami_chennai.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print("Infrastructure demo completed")
    print(f"Summary: {summary_path}")
    print(f"Miami PDF: {miami_pdf_path}")
    print(f"Chennai PDF: {chennai_pdf_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
