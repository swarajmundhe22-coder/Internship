from __future__ import annotations

import argparse
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import httpx


def output_dir(path_arg: str) -> Path:
    path = Path(path_arg)
    if path.is_absolute():
        return path
    return (Path(__file__).resolve().parents[1] / path).resolve()


def parse_stats_from_log(stdout: str) -> dict[str, float]:
    # Gatling stdout summary parsing is best-effort and may vary between versions.
    numbers = {
        "p50_ms": 0.0,
        "p95_ms": 0.0,
        "p99_ms": 0.0,
        "max_ms": 0.0,
    }
    for key, regex in {
        "p50_ms": r"50th pct\s+([0-9]+)",
        "p95_ms": r"95th pct\s+([0-9]+)",
        "p99_ms": r"99th pct\s+([0-9]+)",
        "max_ms": r"max\s+([0-9]+)",
    }.items():
        match = re.search(regex, stdout)
        if match:
            numbers[key] = float(match.group(1))
    return numbers


async def issue_token(base_url: str, password: str) -> str:
    email = f"gatling-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}@example.com"
    async with httpx.AsyncClient(base_url=base_url.rstrip("/"), timeout=httpx.Timeout(30.0)) as client:
        response = await client.post(
            "/auth/register",
            json={"email": email, "password": password, "role": "engineer"},
        )
        response.raise_for_status()
        return str(response.json()["access_token"])


def run_suite(args: argparse.Namespace, token: str) -> tuple[list[dict[str, object]], bool]:
    gatling_root = (Path(__file__).resolve().parents[1] / "performance" / "gatling").resolve()
    tiers = ["low", "medium", "high"]
    duration_minutes = args.duration_minutes
    results: list[dict[str, object]] = []

    for tier in tiers:
        cmd = [
            "sbt",
            f"-DbaseUrl={args.base_url}",
            f"-Dtier={tier}",
            f"-DdurationMinutes={duration_minutes}",
            f"-DchaosRate={args.chaos_rate}",
            f"-Dtoken={token}",
            "gatling:testOnly onlookers.SustainedLatencySimulation",
        ]
        proc = subprocess.run(cmd, cwd=gatling_root, capture_output=True, text=True)
        stdout = (proc.stdout or "") + ("\n" if proc.stdout and proc.stderr else "") + (proc.stderr or "")

        numbers = parse_stats_from_log(stdout)
        sla = {"low": args.sla_low_p99, "medium": args.sla_medium_p99, "high": args.sla_high_p99}[tier]
        tier_pass = numbers["p99_ms"] <= sla and numbers["max_ms"] <= args.spike_ceiling_ms

        results.append(
            {
                "tier": tier,
                "exit_code": proc.returncode,
                "duration_minutes": duration_minutes,
                "metrics": numbers,
                "sla_p99_ms": sla,
                "spike_ceiling_ms": args.spike_ceiling_ms,
                "passed": tier_pass and proc.returncode == 0,
                "stdout_tail": stdout.splitlines()[-40:],
            }
        )

    all_passed = all(bool(item["passed"]) for item in results)
    return results, all_passed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Gatling sustained latency suite for low/medium/high traffic tiers.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000/api/v1")
    parser.add_argument("--password", default="StrongPass123")
    parser.add_argument("--duration-minutes", type=int, default=60)
    parser.add_argument("--chaos-rate", type=float, default=0.01)
    parser.add_argument("--sla-low-p99", type=int, default=100)
    parser.add_argument("--sla-medium-p99", type=int, default=150)
    parser.add_argument("--sla-high-p99", type=int, default=200)
    parser.add_argument("--spike-ceiling-ms", type=int, default=250)
    parser.add_argument("--output-dir", default="artifacts/performance_reports")
    parser.add_argument("--strict", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    out_dir = output_dir(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    token = __import__("asyncio").run(issue_token(args.base_url, args.password))
    results, all_passed = run_suite(args, token)

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "base_url": args.base_url,
        "duration_minutes": args.duration_minutes,
        "chaos_rate": args.chaos_rate,
        "results": results,
        "passed": all_passed,
    }

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")
    report_path = out_dir / f"gatling_latency_suite_{stamp}.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    print(f"Gatling suite status: {'PASS' if all_passed else 'FAIL'}")
    print(f"Report: {report_path}")

    if args.strict and not all_passed:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
