from __future__ import annotations

import argparse
import json
from pathlib import Path


def read_json(path_arg: str) -> dict:
    path = Path(path_arg)
    if not path.is_absolute():
        path = (Path(__file__).resolve().parents[1] / path).resolve()
    return json.loads(path.read_text(encoding="utf-8"))


def flatten_p99(payload: dict) -> dict[str, float]:
    metrics: dict[str, float] = {}
    for tier in payload.get("tiers", []):
        tier_name = str(tier.get("name", "unknown"))
        endpoint_metrics = tier.get("endpoint_metrics", {})
        if not isinstance(endpoint_metrics, dict):
            continue
        for endpoint, summary in endpoint_metrics.items():
            latency = summary.get("latency_ms", {}) if isinstance(summary, dict) else {}
            p99 = float(latency.get("p99", 0.0))
            metrics[f"{tier_name}:{endpoint}"] = p99
    return metrics


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fail CI when P99 regresses more than threshold vs baseline.")
    parser.add_argument("--baseline", required=True, help="Baseline JSON report")
    parser.add_argument("--candidate", required=True, help="Candidate JSON report")
    parser.add_argument("--max-regression-pct", type=float, default=5.0)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    baseline = flatten_p99(read_json(args.baseline))
    candidate = flatten_p99(read_json(args.candidate))

    failures: list[str] = []
    for key, base_value in baseline.items():
        if base_value <= 0:
            continue
        cand_value = candidate.get(key)
        if cand_value is None:
            failures.append(f"missing_metric:{key}")
            continue
        regression_pct = ((cand_value - base_value) / base_value) * 100.0
        if regression_pct > args.max_regression_pct:
            failures.append(f"{key}: regression={regression_pct:.2f}% baseline={base_value:.2f} candidate={cand_value:.2f}")

    if failures:
        print("P99 regression gate: FAIL")
        for failure in failures:
            print(f" - {failure}")
        return 1

    print("P99 regression gate: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
