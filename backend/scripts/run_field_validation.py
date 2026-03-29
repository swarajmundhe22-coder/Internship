from __future__ import annotations

import argparse
import csv
import json
import random
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
from app.models.simulation import SimulationRequest, SimulationResult
from app.services.simulation_service import SimulationService


@dataclass(frozen=True)
class FieldRecord:
    source_row: dict[str, str]
    region: str
    material_name: str
    alloy_group: str
    asset_type: str
    compliance_standard: str
    criticality: str
    temperature_c: float
    relative_humidity_pct: float
    chloride_ppm: float
    ph: float
    dissolved_oxygen_mg_l: float
    uv_index: float
    mic_activity: str
    soil_resistivity_ohm_cm: float
    true_corrosion_rate_mm_per_year: float
    true_design_corrosion_rate_mm_per_year: float
    true_lifespan_years: float
    true_risk_score: float
    observed_at: str | None


@dataclass(frozen=True)
class Thresholds:
    risk_score_mae_max: float
    design_rate_mape_max: float
    lifespan_mape_max: float
    interval_coverage_min: float


DEFAULT_THRESHOLDS = Thresholds(
    risk_score_mae_max=12.0,
    design_rate_mape_max=0.35,
    lifespan_mape_max=0.40,
    interval_coverage_min=0.75,
)


def safe_float(value: str | None, *, fallback: float | None = None, field_name: str = "") -> float:
    raw = (value or "").strip()
    if not raw:
        if fallback is None:
            raise ValueError(f"Missing numeric value for '{field_name}'.")
        return fallback
    return float(raw)


def safe_text(value: str | None, *, fallback: str = "") -> str:
    text = (value or "").strip()
    return text or fallback


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(max(int(round((len(ordered) - 1) * p)), 0), len(ordered) - 1)
    return ordered[index]


def resolve_output_dir(output_dir: str) -> Path:
    candidate = Path(output_dir)
    if candidate.is_absolute():
        return candidate
    return (BACKEND_ROOT / candidate).resolve()


def load_dataset(path: Path) -> list[FieldRecord]:
    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")

    required_columns = {
        "region",
        "material_name",
        "alloy_group",
        "asset_type",
        "compliance_standard",
        "criticality",
        "temperature_c",
        "relative_humidity_pct",
        "chloride_ppm",
        "ph",
        "dissolved_oxygen_mg_l",
        "uv_index",
        "mic_activity",
        "soil_resistivity_ohm_cm",
        "true_corrosion_rate_mm_per_year",
        "true_lifespan_years",
        "true_risk_score",
    }

    records: list[FieldRecord] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("Dataset CSV has no header row.")

        missing_columns = sorted(required_columns - set(reader.fieldnames))
        if missing_columns:
            raise ValueError(f"Dataset is missing required columns: {', '.join(missing_columns)}")

        for row in reader:
            region = safe_text(row.get("region"), fallback="global_default")
            true_corrosion = safe_float(
                row.get("true_corrosion_rate_mm_per_year"),
                field_name="true_corrosion_rate_mm_per_year",
            )
            true_design = safe_float(
                row.get("true_design_corrosion_rate_mm_per_year"),
                fallback=true_corrosion,
                field_name="true_design_corrosion_rate_mm_per_year",
            )

            records.append(
                FieldRecord(
                    source_row=row,
                    region=region,
                    material_name=safe_text(row.get("material_name"), fallback="Custom Alloy"),
                    alloy_group=safe_text(row.get("alloy_group"), fallback="Custom Alloy"),
                    asset_type=safe_text(row.get("asset_type"), fallback="Infrastructure Asset"),
                    compliance_standard=safe_text(row.get("compliance_standard"), fallback="ISO 12944"),
                    criticality=safe_text(row.get("criticality"), fallback="High"),
                    temperature_c=safe_float(row.get("temperature_c"), field_name="temperature_c"),
                    relative_humidity_pct=safe_float(
                        row.get("relative_humidity_pct"),
                        field_name="relative_humidity_pct",
                    ),
                    chloride_ppm=safe_float(row.get("chloride_ppm"), field_name="chloride_ppm"),
                    ph=safe_float(row.get("ph"), field_name="ph"),
                    dissolved_oxygen_mg_l=safe_float(
                        row.get("dissolved_oxygen_mg_l"),
                        field_name="dissolved_oxygen_mg_l",
                    ),
                    uv_index=safe_float(row.get("uv_index"), fallback=5.0, field_name="uv_index"),
                    mic_activity=safe_text(row.get("mic_activity"), fallback="Low"),
                    soil_resistivity_ohm_cm=safe_float(
                        row.get("soil_resistivity_ohm_cm"),
                        fallback=5000.0,
                        field_name="soil_resistivity_ohm_cm",
                    ),
                    true_corrosion_rate_mm_per_year=true_corrosion,
                    true_design_corrosion_rate_mm_per_year=true_design,
                    true_lifespan_years=safe_float(row.get("true_lifespan_years"), field_name="true_lifespan_years"),
                    true_risk_score=safe_float(row.get("true_risk_score"), field_name="true_risk_score"),
                    observed_at=safe_text(row.get("observed_at")) or None,
                )
            )

    if not records:
        raise ValueError("Dataset has no records.")
    return records


def load_thresholds(path: Path) -> tuple[Thresholds, dict[str, Thresholds]]:
    if not path.exists():
        return DEFAULT_THRESHOLDS, {}

    payload = json.loads(path.read_text(encoding="utf-8"))

    global_cfg = payload.get("global", {})
    global_thresholds = Thresholds(
        risk_score_mae_max=float(global_cfg.get("risk_score_mae_max", DEFAULT_THRESHOLDS.risk_score_mae_max)),
        design_rate_mape_max=float(global_cfg.get("design_rate_mape_max", DEFAULT_THRESHOLDS.design_rate_mape_max)),
        lifespan_mape_max=float(global_cfg.get("lifespan_mape_max", DEFAULT_THRESHOLDS.lifespan_mape_max)),
        interval_coverage_min=float(global_cfg.get("interval_coverage_min", DEFAULT_THRESHOLDS.interval_coverage_min)),
    )

    by_region_cfg = payload.get("by_region", {})
    by_region: dict[str, Thresholds] = {}
    for region_key, cfg in by_region_cfg.items():
        by_region[region_key] = Thresholds(
            risk_score_mae_max=float(cfg.get("risk_score_mae_max", global_thresholds.risk_score_mae_max)),
            design_rate_mape_max=float(cfg.get("design_rate_mape_max", global_thresholds.design_rate_mape_max)),
            lifespan_mape_max=float(cfg.get("lifespan_mape_max", global_thresholds.lifespan_mape_max)),
            interval_coverage_min=float(cfg.get("interval_coverage_min", global_thresholds.interval_coverage_min)),
        )

    return global_thresholds, by_region


def split_holdout(records: list[FieldRecord], holdout_ratio: float, seed: int) -> tuple[list[FieldRecord], list[FieldRecord]]:
    grouped: dict[str, list[FieldRecord]] = {}
    for record in records:
        grouped.setdefault(record.region, []).append(record)

    train: list[FieldRecord] = []
    holdout: list[FieldRecord] = []
    rng = random.Random(seed)

    for region, region_records in grouped.items():
        ordered = list(region_records)
        with_timestamp = [record for record in ordered if record.observed_at]
        if len(with_timestamp) == len(ordered):
            ordered.sort(key=lambda item: item.observed_at or "")
        else:
            rng.shuffle(ordered)

        holdout_count = max(1, int(round(len(ordered) * holdout_ratio)))
        holdout_count = min(holdout_count, max(1, len(ordered) - 1)) if len(ordered) > 1 else 1

        holdout.extend(ordered[-holdout_count:])
        train.extend(ordered[:-holdout_count])

    return train, holdout


def build_material(record: FieldRecord) -> MaterialRead:
    density = safe_float(record.source_row.get("density_kg_m3"), fallback=7800.0, field_name="density_kg_m3")
    potential = safe_float(
        record.source_row.get("electrochemical_potential_v"),
        fallback=-0.25,
        field_name="electrochemical_potential_v",
    )
    return MaterialRead(
        name=record.material_name,
        alloy_group=record.alloy_group,
        density_kg_m3=density,
        electrochemical_potential_v=potential,
    )


def build_request(record: FieldRecord) -> SimulationRequest:
    return SimulationRequest(
        material=build_material(record),
        environment=EnvironmentInput(
            temperature_c=record.temperature_c,
            relative_humidity_pct=record.relative_humidity_pct,
            chloride_ppm=record.chloride_ppm,
            ph=record.ph,
            dissolved_oxygen_mg_l=record.dissolved_oxygen_mg_l,
        ),
        exposed_area_m2=safe_float(record.source_row.get("exposed_area_m2"), fallback=140.0, field_name="exposed_area_m2"),
        exposure_time_hours=safe_float(
            record.source_row.get("exposure_time_hours"),
            fallback=24 * 365,
            field_name="exposure_time_hours",
        ),
        asset_type=record.asset_type,
        compliance_standard=record.compliance_standard,
        criticality=record.criticality,
        region=record.region,
        uv_index=record.uv_index,
        mic_activity=record.mic_activity,
        soil_resistivity_ohm_cm=record.soil_resistivity_ohm_cm,
    )


def mape(truth: float, predicted: float) -> float:
    denominator = abs(truth)
    if denominator < 1e-9:
        return 0.0
    return abs(predicted - truth) / denominator


def evaluate_holdout(
    holdout: list[FieldRecord],
    global_thresholds: Thresholds,
    by_region_thresholds: dict[str, Thresholds],
) -> dict[str, object]:
    service = SimulationService()

    rows: list[dict[str, object]] = []
    grouped_rows: dict[str, list[dict[str, object]]] = {}

    for record in holdout:
        result: SimulationResult = service.run_simulation(build_request(record))

        design_rate_pred = float(result.design_corrosion_rate_mm_per_year or 0.0)
        risk_pred = float(result.composite_risk_score or 0.0)
        lifespan_pred = float(result.estimated_lifespan_years)

        design_interval = result.uncertainty_bands.design_corrosion_rate_mm_per_year
        risk_interval = result.uncertainty_bands.composite_risk_score
        lifespan_interval = result.uncertainty_bands.estimated_lifespan_years

        row = {
            "region": record.region,
            "resolved_region_key": str(result.region_key or record.region),
            "scenario_id": record.source_row.get("scenario_id") or record.source_row.get("asset_id") or "unknown",
            "design_rate_true": record.true_design_corrosion_rate_mm_per_year,
            "design_rate_pred": design_rate_pred,
            "design_rate_mape": mape(record.true_design_corrosion_rate_mm_per_year, design_rate_pred),
            "risk_true": record.true_risk_score,
            "risk_pred": risk_pred,
            "risk_mae": abs(record.true_risk_score - risk_pred),
            "lifespan_true": record.true_lifespan_years,
            "lifespan_pred": lifespan_pred,
            "lifespan_mape": mape(record.true_lifespan_years, lifespan_pred),
            "design_rate_in_interval": design_interval.lower <= record.true_design_corrosion_rate_mm_per_year <= design_interval.upper,
            "risk_in_interval": risk_interval.lower <= record.true_risk_score <= risk_interval.upper,
            "lifespan_in_interval": lifespan_interval.lower <= record.true_lifespan_years <= lifespan_interval.upper,
            "calibration_confidence": float(result.calibration_confidence or 0.0),
            "fallback_applied": bool(result.fallback_applied),
        }
        rows.append(row)
        grouped_rows.setdefault(str(row["resolved_region_key"]), []).append(row)

    def summarize(rows_subset: list[dict[str, object]]) -> dict[str, float]:
        return {
            "samples": float(len(rows_subset)),
            "risk_score_mae": mean(float(row["risk_mae"]) for row in rows_subset) if rows_subset else 0.0,
            "design_rate_mape": mean(float(row["design_rate_mape"]) for row in rows_subset) if rows_subset else 0.0,
            "lifespan_mape": mean(float(row["lifespan_mape"]) for row in rows_subset) if rows_subset else 0.0,
            "interval_coverage": mean(
                [
                    1.0
                    if bool(row["design_rate_in_interval"]) and bool(row["risk_in_interval"]) and bool(row["lifespan_in_interval"])
                    else 0.0
                    for row in rows_subset
                ]
            ) if rows_subset else 0.0,
            "fallback_rate": mean([1.0 if bool(row["fallback_applied"]) else 0.0 for row in rows_subset]) if rows_subset else 0.0,
        }

    def threshold_failures(summary: dict[str, float], thresholds: Thresholds) -> list[str]:
        failures: list[str] = []
        if summary["risk_score_mae"] > thresholds.risk_score_mae_max:
            failures.append(
                f"risk_score_mae {summary['risk_score_mae']:.4f} > {thresholds.risk_score_mae_max:.4f}"
            )
        if summary["design_rate_mape"] > thresholds.design_rate_mape_max:
            failures.append(
                f"design_rate_mape {summary['design_rate_mape']:.4f} > {thresholds.design_rate_mape_max:.4f}"
            )
        if summary["lifespan_mape"] > thresholds.lifespan_mape_max:
            failures.append(
                f"lifespan_mape {summary['lifespan_mape']:.4f} > {thresholds.lifespan_mape_max:.4f}"
            )
        if summary["interval_coverage"] < thresholds.interval_coverage_min:
            failures.append(
                f"interval_coverage {summary['interval_coverage']:.4f} < {thresholds.interval_coverage_min:.4f}"
            )
        return failures

    by_region_summary: dict[str, dict[str, object]] = {}
    region_failures: dict[str, list[str]] = {}
    for region, region_rows in sorted(grouped_rows.items()):
        region_summary = summarize(region_rows)
        thresholds = by_region_thresholds.get(region, global_thresholds)
        failures = threshold_failures(region_summary, thresholds)
        by_region_summary[region] = {
            **region_summary,
            "passed": not failures,
            "thresholds": {
                "risk_score_mae_max": thresholds.risk_score_mae_max,
                "design_rate_mape_max": thresholds.design_rate_mape_max,
                "lifespan_mape_max": thresholds.lifespan_mape_max,
                "interval_coverage_min": thresholds.interval_coverage_min,
            },
            "failures": failures,
        }
        if failures:
            region_failures[region] = failures

    global_summary = summarize(rows)
    global_failures = threshold_failures(global_summary, global_thresholds)

    overall_passed = not global_failures and not region_failures

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_rows": len(holdout),
        "global_summary": {
            **global_summary,
            "passed": not global_failures,
            "thresholds": {
                "risk_score_mae_max": global_thresholds.risk_score_mae_max,
                "design_rate_mape_max": global_thresholds.design_rate_mape_max,
                "lifespan_mape_max": global_thresholds.lifespan_mape_max,
                "interval_coverage_min": global_thresholds.interval_coverage_min,
            },
            "failures": global_failures,
        },
        "by_region": by_region_summary,
        "rows": rows,
        "passed": overall_passed,
    }
    return payload


def to_markdown(payload: dict[str, object]) -> str:
    lines: list[str] = []
    lines.append("# External Field Validation Report")
    lines.append("")
    lines.append(f"Generated UTC: {payload['generated_at_utc']}")
    lines.append(f"Holdout records: {payload['dataset_rows']}")
    lines.append(f"Overall status: {'PASS' if payload['passed'] else 'FAIL'}")
    lines.append("")

    global_summary = payload["global_summary"]
    lines.append("## Global Holdout Summary")
    lines.append("")
    lines.append("| Metric | Value | Threshold |")
    lines.append("|---|---:|---:|")
    lines.append(
        f"| Risk score MAE | {float(global_summary['risk_score_mae']):.4f} | <= {float(global_summary['thresholds']['risk_score_mae_max']):.4f} |"
    )
    lines.append(
        f"| Design rate MAPE | {float(global_summary['design_rate_mape']):.4f} | <= {float(global_summary['thresholds']['design_rate_mape_max']):.4f} |"
    )
    lines.append(
        f"| Lifespan MAPE | {float(global_summary['lifespan_mape']):.4f} | <= {float(global_summary['thresholds']['lifespan_mape_max']):.4f} |"
    )
    lines.append(
        f"| Interval coverage | {float(global_summary['interval_coverage']):.4f} | >= {float(global_summary['thresholds']['interval_coverage_min']):.4f} |"
    )
    lines.append("")

    lines.append("## Region Holdout Summary")
    lines.append("")
    lines.append("| Region | Samples | Risk MAE | Design MAPE | Lifespan MAPE | Interval Coverage | Fallback Rate | Status |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---|")
    for region, summary in payload["by_region"].items():
        lines.append(
            "| "
            f"{region} | "
            f"{int(float(summary['samples']))} | "
            f"{float(summary['risk_score_mae']):.4f} | "
            f"{float(summary['design_rate_mape']):.4f} | "
            f"{float(summary['lifespan_mape']):.4f} | "
            f"{float(summary['interval_coverage']):.4f} | "
            f"{float(summary['fallback_rate']):.4f} | "
            f"{'PASS' if summary['passed'] else 'FAIL'} |"
        )

    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run external field validation against holdout dataset with region-level error bounds.",
    )
    parser.add_argument("--dataset", required=True, help="Path to external benchmark CSV dataset.")
    parser.add_argument(
        "--targets",
        default="docs/field_validation_targets.json",
        help="Path to JSON file containing global and region holdout thresholds.",
    )
    parser.add_argument(
        "--output-dir",
        default="artifacts/field_validation",
        help="Directory for generated validation reports.",
    )
    parser.add_argument("--holdout-ratio", type=float, default=0.2, help="Holdout ratio per region.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for holdout sampling fallback.")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero when thresholds fail.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    dataset_path = Path(args.dataset)
    if not dataset_path.is_absolute():
        dataset_path = (BACKEND_ROOT / dataset_path).resolve()

    targets_path = Path(args.targets)
    if not targets_path.is_absolute():
        targets_path = (BACKEND_ROOT / targets_path).resolve()

    output_dir = resolve_output_dir(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    records = load_dataset(dataset_path)
    _, holdout = split_holdout(records, args.holdout_ratio, args.seed)

    global_thresholds, by_region_thresholds = load_thresholds(targets_path)
    payload = evaluate_holdout(holdout, global_thresholds, by_region_thresholds)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")
    json_path = output_dir / f"field_validation_{timestamp}.json"
    md_path = output_dir / f"field_validation_{timestamp}.md"

    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    md_path.write_text(to_markdown(payload), encoding="utf-8")

    print(
        "Field validation summary: "
        f"rows={payload['dataset_rows']} status={'PASS' if payload['passed'] else 'FAIL'}"
    )
    print(f"JSON report: {json_path}")
    print(f"Markdown report: {md_path}")

    if args.strict and not payload["passed"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
