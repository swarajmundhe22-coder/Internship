from __future__ import annotations

import argparse
import asyncio
import json
import math
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import httpx


@dataclass
class RequestSample:
    latency_ms: float
    status_code: int


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(max(math.ceil(len(ordered) * p) - 1, 0), len(ordered) - 1)
    return float(ordered[index])


async def register_engineer(client: httpx.AsyncClient, password: str) -> str:
    email = f"p99-monitor-{uuid4().hex[:10]}@example.com"
    response = await client.post(
        "/auth/register",
        json={"email": email, "password": password, "role": "engineer"},
    )
    response.raise_for_status()
    payload = response.json()
    token = payload.get("access_token")
    if not token:
        raise RuntimeError("Register endpoint did not return access_token.")
    return token


def simulation_payload() -> dict[str, object]:
    return {
        "material": {
            "name": "Carbon Steel",
            "alloy_group": "Ferrous",
            "density_kg_m3": 7850,
            "electrochemical_potential_v": -0.65,
        },
        "environment": {
            "temperature_c": 25,
            "relative_humidity_pct": 80,
            "chloride_ppm": 12000,
            "ph": 7.1,
            "dissolved_oxygen_mg_l": 6.4,
        },
        "exposed_area_m2": 180,
        "exposure_time_hours": 8760,
        "asset_type": "Pipeline (Submerged)",
        "compliance_standard": "NACE SP0169",
        "criticality": "High",
        "region": "Monsoon Coastal",
        "uv_index": 6,
        "mic_activity": "Medium",
        "soil_resistivity_ohm_cm": 2200,
    }


async def simulate_once(client: httpx.AsyncClient, token: str) -> RequestSample:
    start = time.perf_counter()
    response = await client.post(
        "/simulation/simulate",
        headers=auth_header(token),
        json=simulation_payload(),
    )
    latency_ms = (time.perf_counter() - start) * 1000.0
    return RequestSample(latency_ms=latency_ms, status_code=response.status_code)


async def run_warmup(
    client: httpx.AsyncClient,
    token: str,
    *,
    total_requests: int,
    concurrency: int,
) -> list[RequestSample]:
    semaphore = asyncio.Semaphore(concurrency)
    samples: list[RequestSample] = []

    async def worker() -> None:
        async with semaphore:
            try:
                sample = await simulate_once(client, token)
            except Exception:
                samples.append(RequestSample(latency_ms=0.0, status_code=599))
                return
            samples.append(sample)

    await asyncio.gather(*[worker() for _ in range(total_requests)])
    return samples


async def fetch_runtime_metrics(client: httpx.AsyncClient, token: str) -> dict[str, object]:
    response = await client.get(
        "/ops/performance",
        headers=auth_header(token),
        params={"path": "/api/v1/simulation/simulate", "include_paths": "true", "top": "3"},
    )
    response.raise_for_status()
    payload = response.json()
    if not isinstance(payload, dict):
        raise RuntimeError("Runtime ops/performance payload was invalid.")
    return payload


async def run_monitor(
    base_url: str,
    password: str,
    *,
    warmup_requests: int,
    concurrency: int,
    p99_budget_ms: int,
    error_budget_rate: float,
    output_dir: Path,
) -> tuple[bool, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)

    async with httpx.AsyncClient(base_url=base_url.rstrip("/"), timeout=httpx.Timeout(30.0)) as client:
        token = await register_engineer(client, password=password)
        warmup_samples = await run_warmup(
            client,
            token,
            total_requests=warmup_requests,
            concurrency=concurrency,
        )
        runtime_payload = await fetch_runtime_metrics(client, token)

    warmup_latencies = [sample.latency_ms for sample in warmup_samples if sample.status_code == 200]
    warmup_errors = sum(1 for sample in warmup_samples if sample.status_code >= 500)
    warmup_error_rate = (warmup_errors / len(warmup_samples)) if warmup_samples else 1.0

    runtime_latency = runtime_payload.get("latency_ms", {})
    runtime_alerts = runtime_payload.get("alerts", {})

    runtime_request_count = int(runtime_payload.get("request_count", 0))
    runtime_p99 = float(runtime_latency.get("p99", 0.0))
    runtime_error_rate = float(runtime_payload.get("error_rate_5xx", 1.0))

    checks = {
        "runtime_request_count": runtime_request_count >= warmup_requests,
        "runtime_p99_budget": runtime_p99 <= p99_budget_ms,
        "runtime_error_budget": runtime_error_rate <= error_budget_rate,
        "runtime_alert_not_critical_p99": not bool(runtime_alerts.get("critical_latency_p99", False)),
    }
    passed = all(checks.values())

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "base_url": base_url,
        "passed": passed,
        "warmup": {
            "requests": len(warmup_samples),
            "success_count": sum(1 for sample in warmup_samples if sample.status_code == 200),
            "error_count": sum(1 for sample in warmup_samples if sample.status_code >= 500),
            "error_rate_5xx": warmup_error_rate,
            "p95_latency_ms": percentile(warmup_latencies, 0.95),
            "p99_latency_ms": percentile(warmup_latencies, 0.99),
        },
        "runtime_metrics": runtime_payload,
        "budgets": {
            "p99_latency_ms": p99_budget_ms,
            "error_rate_5xx": error_budget_rate,
        },
        "checks": checks,
    }

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")
    report_path = output_dir / f"p99_monitor_{timestamp}.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return passed, report_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Poll runtime P99 telemetry and alert state from /ops/performance.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000/api/v1", help="API base URL with /api/v1")
    parser.add_argument("--password", default="StrongPass123", help="Password for temporary monitor user")
    parser.add_argument("--warmup-requests", type=int, default=80, help="Simulation requests to seed runtime metrics")
    parser.add_argument("--concurrency", type=int, default=10, help="Concurrent in-flight simulation requests")
    parser.add_argument("--p99-budget-ms", type=int, default=2000, help="Maximum allowed runtime p99 latency")
    parser.add_argument(
        "--error-budget-rate",
        type=float,
        default=0.02,
        help="Maximum allowed runtime 5xx error rate",
    )
    parser.add_argument(
        "--output-dir",
        default="artifacts/performance_reports",
        help="Directory where monitor reports are written.",
    )
    parser.add_argument("--strict", action="store_true", help="Return non-zero when checks fail.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = (Path(__file__).resolve().parents[1] / output_dir).resolve()

    passed, report_path = asyncio.run(
        run_monitor(
            args.base_url,
            args.password,
            warmup_requests=args.warmup_requests,
            concurrency=args.concurrency,
            p99_budget_ms=args.p99_budget_ms,
            error_budget_rate=args.error_budget_rate,
            output_dir=output_dir,
        )
    )

    print(f"Runtime P99 monitor status: {'PASS' if passed else 'FAIL'}")
    print(f"Runtime P99 report: {report_path}")
    if args.strict and not passed:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
