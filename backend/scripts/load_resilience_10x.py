from __future__ import annotations

import argparse
import asyncio
import json
import math
import random
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

import httpx


@dataclass
class RequestSample:
    endpoint: str
    latency_ms: float
    status_code: int


@dataclass(frozen=True)
class EndpointScenario:
    name: str
    method: str
    path: str
    requires_auth: bool


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = min(max(math.ceil(len(ordered) * p) - 1, 0), len(ordered) - 1)
    return float(ordered[idx])


def simulation_payload() -> dict[str, Any]:
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run 10x traffic resilience load test (4,000+ concurrent requests).")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000/api/v1")
    parser.add_argument("--password", default="StrongPass123")
    parser.add_argument("--concurrency", type=int, default=4000)
    parser.add_argument("--total-requests", type=int, default=12000)
    parser.add_argument("--p99-budget-ms", type=int, default=100)
    parser.add_argument("--error-budget-rate", type=float, default=0.01)
    parser.add_argument("--output-dir", default="artifacts/performance_reports")
    parser.add_argument("--strict", action="store_true")
    return parser.parse_args()


def resolve_output_dir(path_arg: str) -> Path:
    candidate = Path(path_arg)
    if candidate.is_absolute():
        return candidate
    return (Path(__file__).resolve().parents[1] / candidate).resolve()


async def register_user(client: httpx.AsyncClient, password: str) -> tuple[str, str]:
    email = f"load10x-{uuid4().hex}@example.com"
    response = await client.post(
        "/auth/register",
        json={"email": email, "password": password, "role": "engineer"},
    )
    response.raise_for_status()
    token = str(response.json()["access_token"])
    return email, token


async def issue_request(
    *,
    client: httpx.AsyncClient,
    scenario: EndpointScenario,
    token: str,
    email: str,
    password: str,
) -> RequestSample:
    headers: dict[str, str] = {}
    payload: dict[str, Any] | None = None

    if scenario.requires_auth:
        headers["Authorization"] = f"Bearer {token}"

    if scenario.name == "simulate_post":
        payload = simulation_payload()
    elif scenario.name == "auth_login_post":
        payload = {"email": email, "password": password}

    started = time.perf_counter()
    try:
        if scenario.method == "GET":
            response = await client.get(scenario.path, headers=headers)
        else:
            response = await client.post(scenario.path, headers=headers, json=payload)
        status_code = response.status_code
    except Exception:
        status_code = 599

    latency_ms = (time.perf_counter() - started) * 1000.0
    return RequestSample(endpoint=scenario.name, latency_ms=latency_ms, status_code=status_code)


async def run_load_test(args: argparse.Namespace) -> tuple[dict[str, Any], Path]:
    out_dir = resolve_output_dir(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    scenarios = [
        EndpointScenario(name="simulate_post", method="POST", path="/simulation/simulate", requires_auth=True),
        EndpointScenario(name="auth_login_post", method="POST", path="/auth/login", requires_auth=False),
        EndpointScenario(name="ops_performance_get", method="GET", path="/ops/performance", requires_auth=True),
        EndpointScenario(name="health_get", method="GET", path="/health", requires_auth=False),
    ]
    weights = [0.60, 0.15, 0.10, 0.15]

    timeout = httpx.Timeout(connect=10.0, read=45.0, write=30.0, pool=45.0)
    limits = httpx.Limits(max_connections=max(args.concurrency * 2, 4000), max_keepalive_connections=max(args.concurrency, 2000))

    async with httpx.AsyncClient(base_url=args.base_url.rstrip("/"), timeout=timeout, limits=limits) as client:
        email, token = await register_user(client, args.password)

        work_queue: asyncio.Queue[int] = asyncio.Queue()
        for idx in range(args.total_requests):
            work_queue.put_nowait(idx)

        samples: list[RequestSample] = []
        lock = asyncio.Lock()

        async def worker() -> None:
            while True:
                try:
                    _ = work_queue.get_nowait()
                except asyncio.QueueEmpty:
                    return

                scenario = random.choices(scenarios, weights=weights, k=1)[0]
                sample = await issue_request(
                    client=client,
                    scenario=scenario,
                    token=token,
                    email=email,
                    password=args.password,
                )
                async with lock:
                    samples.append(sample)
                work_queue.task_done()

        started = time.perf_counter()
        workers = [asyncio.create_task(worker()) for _ in range(args.concurrency)]
        await asyncio.gather(*workers)
        total_duration_s = time.perf_counter() - started

        ops_snapshot = {}
        try:
            ops_response = await client.get(
                "/ops/performance",
                headers={"Authorization": f"Bearer {token}"},
                params={"include_paths": "true", "top": "10"},
            )
            if ops_response.status_code == 200:
                ops_snapshot = ops_response.json()
        except Exception:
            ops_snapshot = {}

    endpoint_groups: dict[str, list[RequestSample]] = {}
    for sample in samples:
        endpoint_groups.setdefault(sample.endpoint, []).append(sample)

    endpoint_metrics: dict[str, Any] = {}
    for endpoint, rows in endpoint_groups.items():
        latencies = [row.latency_ms for row in rows]
        errors_5xx = sum(1 for row in rows if row.status_code >= 500)
        endpoint_metrics[endpoint] = {
            "requests": len(rows),
            "errors_5xx": errors_5xx,
            "error_rate_5xx": (errors_5xx / len(rows)) if rows else 0.0,
            "latency_ms": {
                "p50": percentile(latencies, 0.50),
                "p95": percentile(latencies, 0.95),
                "p99": percentile(latencies, 0.99),
                "max": max(latencies) if latencies else 0.0,
            },
        }

    all_latencies = [sample.latency_ms for sample in samples]
    all_errors_5xx = sum(1 for sample in samples if sample.status_code >= 500)
    observed_rps = (len(samples) / total_duration_s) if total_duration_s > 0 else 0.0

    checks = {
        "concurrency_requirement": args.concurrency >= 4000,
        "p99_budget": percentile(all_latencies, 0.99) <= args.p99_budget_ms,
        "error_budget": ((all_errors_5xx / len(samples)) if samples else 1.0) <= args.error_budget_rate,
    }

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "base_url": args.base_url,
        "workload": {
            "concurrency": args.concurrency,
            "total_requests": args.total_requests,
            "duration_seconds": total_duration_s,
            "observed_rps": observed_rps,
        },
        "aggregate": {
            "request_count": len(samples),
            "error_count_5xx": all_errors_5xx,
            "error_rate_5xx": (all_errors_5xx / len(samples)) if samples else 0.0,
            "latency_ms": {
                "p50": percentile(all_latencies, 0.50),
                "p95": percentile(all_latencies, 0.95),
                "p99": percentile(all_latencies, 0.99),
                "max": max(all_latencies) if all_latencies else 0.0,
            },
        },
        "endpoint_metrics": endpoint_metrics,
        "budgets": {
            "p99_budget_ms": args.p99_budget_ms,
            "error_budget_rate": args.error_budget_rate,
        },
        "checks": checks,
        "passed": all(checks.values()),
        "ops_snapshot": ops_snapshot,
    }

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")
    report_path = out_dir / f"load_10x_resilience_{stamp}.json"
    report_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload, report_path


def main() -> int:
    args = parse_args()
    payload, report_path = asyncio.run(run_load_test(args))

    print(f"10x resilience load status: {'PASS' if payload['passed'] else 'FAIL'}")
    print(f"Report: {report_path}")

    if args.strict and not payload["passed"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
