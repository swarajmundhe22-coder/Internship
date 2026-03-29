from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


def resolve_path(path_arg: str) -> Path:
    candidate = Path(path_arg)
    if candidate.is_absolute():
        return candidate
    return (BACKEND_ROOT / candidate).resolve()


def latest_report(reports_dir: Path) -> Path:
    reports = sorted(reports_dir.glob("calibration_report_*.json"))
    if not reports:
        raise FileNotFoundError(f"No calibration report JSON files found in {reports_dir}")
    return reports[-1]


def relative_drift(current: float, baseline: float) -> float:
    denominator = abs(baseline)
    if denominator < 1e-9:
        return 0.0 if abs(current) < 1e-9 else 1.0
    return abs(current - baseline) / denominator


def to_markdown(payload: dict[str, object]) -> str:
    lines: list[str] = []
    lines.append("# Model Drift Report")
    lines.append("")
    lines.append(f"Generated UTC: {payload['generated_at_utc']}")
    lines.append(f"Overall status: {'PASS' if payload['passed'] else 'FAIL'}")
    lines.append(f"Current report: {payload['current_report_path']}")
    lines.append("")

    lines.append("## Global Drift")
    lines.append("")
    lines.append("| Metric | Baseline | Current | Relative Drift | Limit | Status |")
    lines.append("|---|---:|---:|---:|---:|---|")
    for metric in payload["global_drift"]:
        lines.append(
            "| "
            f"{metric['metric']} | "
            f"{metric['baseline']:.6f} | "
            f"{metric['current']:.6f} | "
            f"{metric['relative_drift']:.6f} | "
            f"{metric['threshold']:.6f} | "
            f"{'PASS' if metric['passed'] else 'FAIL'} |"
        )

    lines.append("")
    lines.append("## Region Drift")
    lines.append("")
    lines.append("| Region | Metric | Baseline | Current | Relative Drift | Limit | Status |")
    lines.append("|---|---|---:|---:|---:|---:|---|")
    for item in payload["region_drift"]:
        lines.append(
            "| "
            f"{item['region_key']} | "
            f"{item['metric']} | "
            f"{item['baseline']:.6f} | "
            f"{item['current']:.6f} | "
            f"{item['relative_drift']:.6f} | "
            f"{item['threshold']:.6f} | "
            f"{'PASS' if item['passed'] else 'FAIL'} |"
        )

    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare latest calibration report with drift baseline.")
    parser.add_argument(
        "--baseline",
        default="docs/model_drift_baseline.json",
        help="Path to drift baseline reference JSON.",
    )
    parser.add_argument(
        "--current-report",
        default="",
        help="Path to current calibration report JSON. If omitted, latest report from --reports-dir is used.",
    )
    parser.add_argument(
        "--reports-dir",
        default="artifacts/calibration_reports",
        help="Directory used when --current-report is omitted.",
    )
    parser.add_argument(
        "--output-dir",
        default="artifacts/model_drift",
        help="Output directory for drift report artifacts.",
    )
    parser.add_argument("--strict", action="store_true", help="Exit non-zero when drift thresholds are breached.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    baseline_path = resolve_path(args.baseline)
    reports_dir = resolve_path(args.reports_dir)
    output_dir = resolve_path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    baseline_payload = json.loads(baseline_path.read_text(encoding="utf-8"))

    if args.current_report:
        current_report_path = resolve_path(args.current_report)
    else:
        current_report_path = latest_report(reports_dir)

    current_payload = json.loads(current_report_path.read_text(encoding="utf-8"))

    thresholds = baseline_payload.get("thresholds", {})
    global_threshold = float(thresholds.get("global_relative_drift_max", 0.20))
    region_threshold = float(thresholds.get("region_relative_drift_max", 0.25))

    reference = baseline_payload["reference"]
    current_reference = {
        "average_risk_score": float(current_payload.get("average_risk_score", 0.0)),
        "average_design_corrosion_rate_mm_per_year": float(
            current_payload.get("average_design_corrosion_rate_mm_per_year", 0.0)
        ),
        "average_lifespan_years": float(current_payload.get("average_lifespan_years", 0.0)),
    }

    global_drift: list[dict[str, object]] = []
    for key, baseline_value in reference.items():
        current_value = current_reference.get(key, 0.0)
        drift = relative_drift(current_value, float(baseline_value))
        global_drift.append(
            {
                "metric": key,
                "baseline": float(baseline_value),
                "current": float(current_value),
                "relative_drift": drift,
                "threshold": global_threshold,
                "passed": drift <= global_threshold,
            }
        )

    current_regions = {
        entry["region_key"]: entry
        for entry in current_payload.get("region_summary", [])
    }
    baseline_regions = baseline_payload.get("by_region", {})

    region_drift: list[dict[str, object]] = []
    for region_key, baseline_region in baseline_regions.items():
        current_region = current_regions.get(region_key)
        if not current_region:
            region_drift.append(
                {
                    "region_key": region_key,
                    "metric": "missing_region",
                    "baseline": 1.0,
                    "current": 0.0,
                    "relative_drift": 1.0,
                    "threshold": region_threshold,
                    "passed": False,
                }
            )
            continue

        for metric_name in (
            "average_risk_score",
            "average_design_corrosion_rate_mm_per_year",
            "average_calibration_confidence",
        ):
            baseline_value = float(baseline_region.get(metric_name, 0.0))
            current_value = float(current_region.get(metric_name, 0.0))
            drift = relative_drift(current_value, baseline_value)
            region_drift.append(
                {
                    "region_key": region_key,
                    "metric": metric_name,
                    "baseline": baseline_value,
                    "current": current_value,
                    "relative_drift": drift,
                    "threshold": region_threshold,
                    "passed": drift <= region_threshold,
                }
            )

    passed = all(item["passed"] for item in global_drift) and all(item["passed"] for item in region_drift)

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "current_report_path": str(current_report_path),
        "model_version": current_payload.get("model_version"),
        "global_drift": global_drift,
        "region_drift": region_drift,
        "passed": passed,
    }

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")
    json_path = output_dir / f"model_drift_{timestamp}.json"
    md_path = output_dir / f"model_drift_{timestamp}.md"

    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    md_path.write_text(to_markdown(payload), encoding="utf-8")

    print(f"Drift status: {'PASS' if passed else 'FAIL'}")
    print(f"JSON report: {json_path}")
    print(f"Markdown report: {md_path}")

    if args.strict and not passed:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
