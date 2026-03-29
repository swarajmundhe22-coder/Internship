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


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(max(math.ceil(len(ordered) * p) - 1, 0), len(ordered) - 1)
    return ordered[index]


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def register_engineer(client: httpx.AsyncClient, password: str) -> str:
    email = f"perf-{uuid4().hex[:10]}@example.com"
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


async def simulate_once(client: httpx.AsyncClient, token: str) -> RequestSample:
    payload = {
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

    start = time.perf_counter()
    response = await client.post(
        "/simulation/simulate",
        headers=auth_header(token),
        json=payload,
    )
    latency_ms = (time.perf_counter() - start) * 1000.0
    return RequestSample(latency_ms=latency_ms, status_code=response.status_code)


async def run_sustained_load(
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


async def run_failure_mode_checks(client: httpx.AsyncClient, token: str) -> dict[str, int]:
    unauthorized = await client.post(
        "/simulation/simulate",
        json={
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
        },
    )
    malformed = await client.post(
        "/simulation/simulate",
        headers=auth_header(token),
        json={"material": {}, "environment": {}},
    )

    status_unauth = unauthorized.status_code
    status_malformed = malformed.status_code
    server_error_count = int(status_unauth >= 500) + int(status_malformed >= 500)
    return {
        "unauthorized_status": status_unauth,
        "malformed_status": status_malformed,
        "unexpected_5xx_count": server_error_count,
    }


async def run_gate(
    base_url: str,
    password: str,
    *,
    total_requests: int,
    concurrency: int,
    p95_budget_ms: int,
    p99_budget_ms: int,
    error_budget_rate: float,
    output_dir: Path,
) -> tuple[bool, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    timeout = httpx.Timeout(30.0)

    async with httpx.AsyncClient(base_url=base_url.rstrip("/"), timeout=timeout) as client:
        token = await register_engineer(client, password=password)

        samples = await run_sustained_load(
            client,
            token,
            total_requests=total_requests,
            concurrency=concurrency,
        )

        latencies = [sample.latency_ms for sample in samples if sample.status_code == 200]
        total = len(samples)
        success_count = sum(1 for sample in samples if sample.status_code == 200)
        error_count = total - success_count
        error_rate = (error_count / total) if total else 1.0

        p95_latency = percentile(latencies, 0.95)
        p99_latency = percentile(latencies, 0.99)

        failure_checks = await run_failure_mode_checks(client, token)

    checks = {
        "p95_latency_budget": p95_latency <= p95_budget_ms,
        "p99_latency_budget": p99_latency <= p99_budget_ms,
        "error_budget": error_rate <= error_budget_rate,
        "failure_mode_no_5xx": failure_checks["unexpected_5xx_count"] == 0,
        "failure_mode_unauthorized_status": failure_checks["unauthorized_status"] in (401, 403),
        "failure_mode_malformed_status": failure_checks["malformed_status"] == 422,
    }
    passed = all(checks.values())

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "base_url": base_url,
        "passed": passed,
        "sustained_load": {
            "total_requests": total,
            "success_count": success_count,
            "error_count": error_count,
            "error_rate": error_rate,
            "p95_latency_ms": p95_latency,
            "p99_latency_ms": p99_latency,
            "budgets": {
                "p95_latency_ms": p95_budget_ms,
                "p99_latency_ms": p99_budget_ms,
                "error_rate": error_budget_rate,
            },
        },
        "failure_mode": failure_checks,
        "checks": checks,
    }

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")
    report_path = output_dir / f"performance_reliability_gate_{timestamp}.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return passed, report_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run sustained-load and reliability gate checks against the API.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000/api/v1", help="API base URL with /api/v1")
    parser.add_argument("--password", default="StrongPass123", help="Password for temporary gate user")
    parser.add_argument("--total-requests", type=int, default=120, help="Total load-test requests")
    parser.add_argument("--concurrency", type=int, default=12, help="Concurrent in-flight requests")
    parser.add_argument("--p95-budget-ms", type=int, default=1200, help="Maximum allowed p95 latency")
    parser.add_argument("--p99-budget-ms", type=int, default=2000, help="Maximum allowed p99 latency")
    parser.add_argument(
        "--error-budget-rate",
        type=float,
        default=0.02,
        help="Maximum allowed request error rate.",
    )
    parser.add_argument(
        "--output-dir",
        default="artifacts/performance_reports",
        help="Directory where performance gate reports are written.",
    )
    parser.add_argument("--strict", action="store_true", help="Return non-zero when any gate check fails.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = (Path(__file__).resolve().parents[1] / output_dir).resolve()

    passed, report_path = asyncio.run(
        run_gate(
            args.base_url,
            args.password,
            total_requests=args.total_requests,
            concurrency=args.concurrency,
            p95_budget_ms=args.p95_budget_ms,
            p99_budget_ms=args.p99_budget_ms,
            error_budget_rate=args.error_budget_rate,
            output_dir=output_dir,
        )
    )

    print(f"Performance gate status: {'PASS' if passed else 'FAIL'}")
    print(f"Performance report: {report_path}")
    if args.strict and not passed:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
