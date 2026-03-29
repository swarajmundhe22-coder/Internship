from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.models.environment import EnvironmentInput
from app.models.material import MaterialRead
from app.models.simulation import SimulationRequest
from app.services.simulation_service import SimulationService


@dataclass(frozen=True)
class NumericRange:
    minimum: float
    maximum: float

    def contains(self, value: float) -> bool:
        return self.minimum <= value <= self.maximum


@dataclass(frozen=True)
class CalibrationScenario:
    key: str
    title: str
    material_name: str
    alloy_group: str
    asset_type: str
    region: str | None
    expected_region_key: str | None
    environment: EnvironmentInput
    compliance_standard: str
    criticality: str
    uv_index: float
    mic_activity: str
    soil_resistivity_ohm_cm: float
    expected_risk: NumericRange
    expected_design_rate: NumericRange
    expected_lifespan: NumericRange


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def estimate_exposed_area_m2(asset_type: str) -> float:
    normalized = asset_type.strip().lower()
    if "pipeline" in normalized:
        return 180.0
    if "bridge" in normalized:
        return 260.0
    if "offshore" in normalized or "platform" in normalized:
        return 420.0
    if "tank" in normalized:
        return 320.0
    return 140.0


def build_material_profile(material_name: str, alloy_group: str) -> MaterialRead:
    normalized = material_name.strip().lower()
    group = alloy_group.strip()

    if "carbon steel" in normalized or "a516" in normalized:
        return MaterialRead(
            name=material_name,
            alloy_group=group,
            density_kg_m3=7850.0,
            electrochemical_potential_v=-0.65,
        )
    if "316" in normalized:
        return MaterialRead(
            name=material_name,
            alloy_group=group,
            density_kg_m3=8000.0,
            electrochemical_potential_v=-0.15,
        )
    if "duplex" in normalized or "2205" in normalized:
        return MaterialRead(
            name=material_name,
            alloy_group=group,
            density_kg_m3=7800.0,
            electrochemical_potential_v=-0.10,
        )
    if "galvanized" in normalized:
        return MaterialRead(
            name=material_name,
            alloy_group=group,
            density_kg_m3=7850.0,
            electrochemical_potential_v=-0.72,
        )

    return MaterialRead(
        name=material_name,
        alloy_group=group,
        density_kg_m3=7800.0,
        electrochemical_potential_v=-0.25,
    )


def interval_contains(value: float, lower: float, upper: float) -> bool:
    return lower <= value <= upper


def validate_result(scenario: CalibrationScenario, result) -> list[str]:
    issues: list[str] = []

    design_rate = float(result.design_corrosion_rate_mm_per_year or 0.0)
    risk_score = float(result.composite_risk_score or 0.0)
    lifespan = float(result.estimated_lifespan_years)
    corrosion_rate = float(result.corrosion_rate_mm_per_year)

    if not scenario.expected_risk.contains(risk_score):
        issues.append(
            f"Risk score {risk_score:.2f} outside expected range {scenario.expected_risk.minimum:.2f}-{scenario.expected_risk.maximum:.2f}."
        )
    if not scenario.expected_design_rate.contains(design_rate):
        issues.append(
            "Design corrosion rate "
            f"{design_rate:.4f} outside expected range {scenario.expected_design_rate.minimum:.4f}-{scenario.expected_design_rate.maximum:.4f}."
        )
    if not scenario.expected_lifespan.contains(lifespan):
        issues.append(
            f"Lifespan {lifespan:.2f} outside expected range {scenario.expected_lifespan.minimum:.2f}-{scenario.expected_lifespan.maximum:.2f}."
        )

    if scenario.expected_region_key and result.region_key != scenario.expected_region_key:
        issues.append(
            f"Resolved region '{result.region_key}' does not match expected '{scenario.expected_region_key}'."
        )

    if design_rate < corrosion_rate:
        issues.append("Design corrosion rate should be greater than or equal to uniform corrosion rate.")

    if result.uncertainty_bands is None:
        issues.append("Uncertainty bands missing from simulation response.")
        return issues

    intervals = {
        "corrosion_rate": (
            result.uncertainty_bands.corrosion_rate_mm_per_year.lower,
            result.uncertainty_bands.corrosion_rate_mm_per_year.upper,
            result.uncertainty_bands.corrosion_rate_mm_per_year.confidence_level,
            corrosion_rate,
        ),
        "design_rate": (
            result.uncertainty_bands.design_corrosion_rate_mm_per_year.lower,
            result.uncertainty_bands.design_corrosion_rate_mm_per_year.upper,
            result.uncertainty_bands.design_corrosion_rate_mm_per_year.confidence_level,
            design_rate,
        ),
        "lifespan": (
            result.uncertainty_bands.estimated_lifespan_years.lower,
            result.uncertainty_bands.estimated_lifespan_years.upper,
            result.uncertainty_bands.estimated_lifespan_years.confidence_level,
            lifespan,
        ),
        "risk_score": (
            result.uncertainty_bands.composite_risk_score.lower,
            result.uncertainty_bands.composite_risk_score.upper,
            result.uncertainty_bands.composite_risk_score.confidence_level,
            risk_score,
        ),
    }

    for metric, (lower, upper, confidence, value) in intervals.items():
        if lower > upper:
            issues.append(f"{metric} interval is invalid: lower {lower:.4f} > upper {upper:.4f}.")
            continue
        if not interval_contains(value, lower, upper):
            issues.append(
                f"{metric} estimate {value:.4f} is outside interval {lower:.4f}-{upper:.4f}."
            )
        if confidence < 0.80 or confidence >= 1.0:
            issues.append(f"{metric} confidence level {confidence:.3f} outside expected (0.80, 1.0).")

    return issues


def scenario_set() -> list[CalibrationScenario]:
    return [
        CalibrationScenario(
            key="north_sea_offshore_carbon",
            title="North Sea offshore fixed platform - carbon steel",
            material_name="Carbon Steel A516",
            alloy_group="Ferrous",
            asset_type="Offshore Platform (Fixed)",
            region="North Sea Offshore",
            expected_region_key="north_sea_offshore",
            environment=EnvironmentInput(
                temperature_c=6.0,
                relative_humidity_pct=86.0,
                chloride_ppm=26000.0,
                ph=7.6,
                dissolved_oxygen_mg_l=7.5,
            ),
            compliance_standard="NORSOK M-501",
            criticality="Mission Critical",
            uv_index=2.0,
            mic_activity="Medium",
            soil_resistivity_ohm_cm=2500.0,
            expected_risk=NumericRange(50.0, 100.0),
            expected_design_rate=NumericRange(0.12, 1.60),
            expected_lifespan=NumericRange(1.0, 50.0),
        ),
        CalibrationScenario(
            key="gulf_tropical_marine_hull",
            title="Gulf tropical marine vessel hull - carbon steel",
            material_name="Carbon Steel A36",
            alloy_group="Ferrous",
            asset_type="Marine Vessel (Hull)",
            region="Gulf Tropical Marine",
            expected_region_key="gulf_tropical_marine",
            environment=EnvironmentInput(
                temperature_c=34.0,
                relative_humidity_pct=82.0,
                chloride_ppm=30000.0,
                ph=8.1,
                dissolved_oxygen_mg_l=6.4,
            ),
            compliance_standard="ISO 12944",
            criticality="High",
            uv_index=10.0,
            mic_activity="Medium",
            soil_resistivity_ohm_cm=4200.0,
            expected_risk=NumericRange(55.0, 100.0),
            expected_design_rate=NumericRange(0.15, 1.80),
            expected_lifespan=NumericRange(1.0, 45.0),
        ),
        CalibrationScenario(
            key="temperate_stainless_tank",
            title="Temperate industrial storage tank - stainless 316",
            material_name="Stainless Steel 316L",
            alloy_group="Austenitic Stainless",
            asset_type="Storage Tank (AST)",
            region="Temperate Industrial",
            expected_region_key="temperate_industrial",
            environment=EnvironmentInput(
                temperature_c=18.0,
                relative_humidity_pct=65.0,
                chloride_ppm=3500.0,
                ph=7.0,
                dissolved_oxygen_mg_l=6.0,
            ),
            compliance_standard="ISO 12944",
            criticality="Medium",
            uv_index=4.0,
            mic_activity="Low",
            soil_resistivity_ohm_cm=5200.0,
            expected_risk=NumericRange(5.0, 55.0),
            expected_design_rate=NumericRange(0.002, 0.20),
            expected_lifespan=NumericRange(25.0, 120.0),
        ),
        CalibrationScenario(
            key="arid_weathering_bridge",
            title="Arid desert industrial bridge beam - weathering steel",
            material_name="Weathering Steel Corten",
            alloy_group="Ferrous",
            asset_type="Bridge (Beam)",
            region="Arid Desert Industrial",
            expected_region_key="arid_desert_industrial",
            environment=EnvironmentInput(
                temperature_c=41.0,
                relative_humidity_pct=24.0,
                chloride_ppm=1500.0,
                ph=8.2,
                dissolved_oxygen_mg_l=7.0,
            ),
            compliance_standard="ASTM G1",
            criticality="High",
            uv_index=11.0,
            mic_activity="Low",
            soil_resistivity_ohm_cm=6400.0,
            expected_risk=NumericRange(15.0, 70.0),
            expected_design_rate=NumericRange(0.03, 0.60),
            expected_lifespan=NumericRange(8.0, 110.0),
        ),
        CalibrationScenario(
            key="auto_monsoon_pipeline",
            title="Auto-select monsoon coastal submerged pipeline",
            material_name="Carbon Steel A516",
            alloy_group="Ferrous",
            asset_type="Pipeline (Submerged)",
            region=None,
            expected_region_key="monsoon_coastal",
            environment=EnvironmentInput(
                temperature_c=30.0,
                relative_humidity_pct=90.0,
                chloride_ppm=18000.0,
                ph=6.6,
                dissolved_oxygen_mg_l=5.8,
            ),
            compliance_standard="NACE SP0169",
            criticality="High",
            uv_index=7.0,
            mic_activity="High",
            soil_resistivity_ohm_cm=1200.0,
            expected_risk=NumericRange(55.0, 100.0),
            expected_design_rate=NumericRange(0.14, 2.00),
            expected_lifespan=NumericRange(1.0, 35.0),
        ),
        CalibrationScenario(
            key="arctic_duplex_pipeline",
            title="Arctic subarctic atmospheric pipeline - duplex",
            material_name="Duplex Stainless Steel 2205",
            alloy_group="Duplex Stainless",
            asset_type="Pipeline (Atmospheric)",
            region="Arctic Subarctic",
            expected_region_key="arctic_subarctic",
            environment=EnvironmentInput(
                temperature_c=-12.0,
                relative_humidity_pct=72.0,
                chloride_ppm=8000.0,
                ph=7.4,
                dissolved_oxygen_mg_l=9.0,
            ),
            compliance_standard="NACE SP0169",
            criticality="Medium",
            uv_index=1.0,
            mic_activity="Low",
            soil_resistivity_ohm_cm=2200.0,
            expected_risk=NumericRange(8.0, 70.0),
            expected_design_rate=NumericRange(0.003, 0.25),
            expected_lifespan=NumericRange(20.0, 120.0),
        ),
        CalibrationScenario(
            key="auto_equatorial_urban_concrete",
            title="Auto-select equatorial humid urban reinforced concrete",
            material_name="Galvanized Steel",
            alloy_group="Ferrous",
            asset_type="Reinforced Concrete",
            region=None,
            expected_region_key="equatorial_humid_urban",
            environment=EnvironmentInput(
                temperature_c=31.0,
                relative_humidity_pct=84.0,
                chloride_ppm=7000.0,
                ph=6.8,
                dissolved_oxygen_mg_l=6.5,
            ),
            compliance_standard="ISO 12944",
            criticality="Medium",
            uv_index=9.0,
            mic_activity="Low",
            soil_resistivity_ohm_cm=1500.0,
            expected_risk=NumericRange(25.0, 85.0),
            expected_design_rate=NumericRange(0.03, 0.90),
            expected_lifespan=NumericRange(5.0, 90.0),
        ),
        CalibrationScenario(
            key="auto_temperate_wind_duplex",
            title="Auto-select temperate industrial wind turbine tower - duplex",
            material_name="Duplex Stainless Steel 2205",
            alloy_group="Duplex Stainless",
            asset_type="Wind Turbine Tower",
            region=None,
            expected_region_key="temperate_industrial",
            environment=EnvironmentInput(
                temperature_c=14.0,
                relative_humidity_pct=58.0,
                chloride_ppm=1800.0,
                ph=7.3,
                dissolved_oxygen_mg_l=7.0,
            ),
            compliance_standard="ISO 12944",
            criticality="Medium",
            uv_index=5.0,
            mic_activity="Low",
            soil_resistivity_ohm_cm=5000.0,
            expected_risk=NumericRange(5.0, 55.0),
            expected_design_rate=NumericRange(0.002, 0.18),
            expected_lifespan=NumericRange(30.0, 120.0),
        ),
    ]


def run_validation(scenarios: list[CalibrationScenario]) -> dict[str, object]:
    service = SimulationService()
    rows: list[dict[str, object]] = []

    for scenario in scenarios:
        material = build_material_profile(scenario.material_name, scenario.alloy_group)
        request = SimulationRequest(
            material=material,
            environment=scenario.environment,
            exposed_area_m2=estimate_exposed_area_m2(scenario.asset_type),
            exposure_time_hours=24 * 365,
            asset_type=scenario.asset_type,
            compliance_standard=scenario.compliance_standard,
            criticality=scenario.criticality,
            region=scenario.region,
            uv_index=scenario.uv_index,
            mic_activity=scenario.mic_activity,
            soil_resistivity_ohm_cm=scenario.soil_resistivity_ohm_cm,
        )

        result = service.run_simulation(request)
        issues = validate_result(scenario, result)

        rows.append(
            {
                "scenario_key": scenario.key,
                "scenario_title": scenario.title,
                "requested_region": scenario.region,
                "expected_region_key": scenario.expected_region_key,
                "resolved_region_key": result.region_key,
                "resolved_region_name": result.region_name,
                "risk_score": round(float(result.composite_risk_score or 0.0), 3),
                "design_corrosion_rate_mm_per_year": round(float(result.design_corrosion_rate_mm_per_year or 0.0), 5),
                "estimated_lifespan_years": round(float(result.estimated_lifespan_years), 3),
                "risk_classification": result.risk_classification,
                "calibration_confidence": round(float(result.calibration_confidence or 0.0), 3),
                "passed": not issues,
                "issues": issues,
                "response": result.model_dump(mode="json"),
            }
        )

    model_version = rows[0]["response"]["model_version"] if rows else "unknown"
    passed = [row for row in rows if row["passed"]]
    failed = [row for row in rows if not row["passed"]]

    region_groups: dict[str, list[dict[str, object]]] = {}
    for row in rows:
        key = str(row.get("resolved_region_key") or "unknown")
        region_groups.setdefault(key, []).append(row)

    region_summary: list[dict[str, object]] = []
    for region_key, members in sorted(region_groups.items()):
        avg_risk = mean(float(member["risk_score"]) for member in members)
        avg_design_rate = mean(float(member["design_corrosion_rate_mm_per_year"]) for member in members)
        avg_confidence = mean(float(member["calibration_confidence"]) for member in members)
        region_summary.append(
            {
                "region_key": region_key,
                "scenarios": len(members),
                "average_risk_score": round(avg_risk, 3),
                "average_design_corrosion_rate_mm_per_year": round(avg_design_rate, 5),
                "average_calibration_confidence": round(avg_confidence, 3),
            }
        )

    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "model_version": model_version,
        "scenario_count": len(rows),
        "passed_count": len(passed),
        "failed_count": len(failed),
        "pass_rate": round((len(passed) / len(rows)) if rows else 0.0, 4),
        "average_risk_score": round(mean(float(row["risk_score"]) for row in rows), 3) if rows else 0.0,
        "average_design_corrosion_rate_mm_per_year": round(
            mean(float(row["design_corrosion_rate_mm_per_year"]) for row in rows),
            5,
        ) if rows else 0.0,
        "average_lifespan_years": round(mean(float(row["estimated_lifespan_years"]) for row in rows), 3) if rows else 0.0,
        "region_summary": region_summary,
        "scenarios": rows,
    }


def write_markdown_report(payload: dict[str, object], output_path: Path) -> None:
    scenarios = payload["scenarios"]
    region_summary = payload["region_summary"]

    lines: list[str] = []
    lines.append("# Calibration Validation Report")
    lines.append("")
    lines.append(f"Generated UTC: {payload['generated_at_utc']}")
    lines.append(f"Model Version: {payload['model_version']}")
    lines.append(f"Scenarios: {payload['scenario_count']}")
    lines.append(f"Pass Rate: {float(payload['pass_rate']) * 100:.1f}%")
    lines.append("")
    lines.append("## Scenario Results")
    lines.append("")
    lines.append("| Scenario | Region | Risk Score | Design Rate (mm/y) | Lifespan (y) | Status | Notes |")
    lines.append("|---|---|---:|---:|---:|---|---|")

    for scenario in scenarios:
        issues = scenario["issues"]
        note = "OK" if not issues else "; ".join(issues)
        status = "PASS" if scenario["passed"] else "FAIL"
        lines.append(
            "| "
            f"{scenario['scenario_title']} | "
            f"{scenario['resolved_region_key']} | "
            f"{float(scenario['risk_score']):.2f} | "
            f"{float(scenario['design_corrosion_rate_mm_per_year']):.4f} | "
            f"{float(scenario['estimated_lifespan_years']):.2f} | "
            f"{status} | "
            f"{note} |"
        )

    lines.append("")
    lines.append("## Region Aggregates")
    lines.append("")
    lines.append("| Region Key | Scenarios | Avg Risk Score | Avg Design Rate (mm/y) | Avg Calibration Confidence |")
    lines.append("|---|---:|---:|---:|---:|")
    for region in region_summary:
        lines.append(
            "| "
            f"{region['region_key']} | "
            f"{region['scenarios']} | "
            f"{float(region['average_risk_score']):.2f} | "
            f"{float(region['average_design_corrosion_rate_mm_per_year']):.4f} | "
            f"{float(region['average_calibration_confidence']):.3f} |"
        )

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def resolve_output_dir(path_arg: str) -> Path:
    base_dir = Path(__file__).resolve().parents[1]
    candidate = Path(path_arg)
    if candidate.is_absolute():
        return candidate
    return (base_dir / candidate).resolve()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run structured multi-scenario calibration validation and generate report artifacts."
    )
    parser.add_argument(
        "--output-dir",
        default="artifacts/calibration_reports",
        help="Report output directory (absolute path or path relative to backend root).",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit with status code 1 when one or more scenarios fail validation.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = resolve_output_dir(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    payload = run_validation(scenario_set())

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")
    json_path = output_dir / f"calibration_report_{timestamp}.json"
    md_path = output_dir / f"calibration_report_{timestamp}.md"

    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_markdown_report(payload, md_path)

    pass_rate_percent = float(payload["pass_rate"]) * 100.0
    print(f"Model version: {payload['model_version']}")
    print(
        "Validation summary: "
        f"{payload['passed_count']}/{payload['scenario_count']} scenarios passed ({pass_rate_percent:.1f}%)."
    )
    print(f"JSON report: {json_path}")
    print(f"Markdown report: {md_path}")

    if args.strict and int(payload["failed_count"]) > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())