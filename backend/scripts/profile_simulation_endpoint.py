from __future__ import annotations

import argparse
import asyncio
import cProfile
import io
import json
import math
import pstats
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


async def register_engineer(client: httpx.AsyncClient, password: str) -> str:
    email = f"profile-{uuid4().hex[:10]}@example.com"
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
    start = time.perf_counter()
    response = await client.post(
        "/simulation/simulate",
        headers=auth_header(token),
        json=simulation_payload(),
    )
    latency_ms = (time.perf_counter() - start) * 1000.0
    return RequestSample(latency_ms=latency_ms, status_code=response.status_code)


async def run_profile_workload(
    base_url: str,
    password: str,
    *,
    requests: int,
    concurrency: int,
) -> dict[str, object]:
    async with httpx.AsyncClient(base_url=base_url.rstrip("/"), timeout=httpx.Timeout(30.0)) as client:
        token = await register_engineer(client, password=password)

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

        await asyncio.gather(*[worker() for _ in range(requests)])

    latencies = [sample.latency_ms for sample in samples if sample.status_code == 200]
    server_errors = sum(1 for sample in samples if sample.status_code >= 500)

    return {
        "request_count": len(samples),
        "success_count": sum(1 for sample in samples if sample.status_code == 200),
        "server_error_count": server_errors,
        "error_rate_5xx": (server_errors / len(samples)) if samples else 1.0,
        "p95_latency_ms": percentile(latencies, 0.95),
        "p99_latency_ms": percentile(latencies, 0.99),
        "max_latency_ms": max(latencies) if latencies else 0.0,
    }


def render_top_profile_stats(profiler: cProfile.Profile, *, sort_by: str, top_n: int) -> str:
    stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stream)
    stats.sort_stats(sort_by)
    stats.print_stats(top_n)
    return stream.getvalue()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Profile simulation endpoint workload to identify backend bottlenecks.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000/api/v1", help="API base URL with /api/v1")
    parser.add_argument("--password", default="StrongPass123", help="Password for temporary profiling user")
    parser.add_argument("--requests", type=int, default=60, help="Number of simulation requests in the profiling workload")
    parser.add_argument("--concurrency", type=int, default=10, help="Concurrent in-flight simulation requests")
    parser.add_argument(
        "--sort-by",
        default="cumulative",
        choices=["cumulative", "tottime", "ncalls"],
        help="pstats sort key for top bottleneck table",
    )
    parser.add_argument("--top", type=int, default=25, help="Top function rows to include in profile summary")
    parser.add_argument(
        "--output-dir",
        default="artifacts/performance_reports",
        help="Directory where profiling artifacts are written.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = (Path(__file__).resolve().parents[1] / output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    profiler = cProfile.Profile()
    profiler.enable()
    summary = asyncio.run(
        run_profile_workload(
            args.base_url,
            args.password,
            requests=args.requests,
            concurrency=args.concurrency,
        )
    )
    profiler.disable()

    profile_text = render_top_profile_stats(profiler, sort_by=args.sort_by, top_n=args.top)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")
    profile_binary_path = output_dir / f"simulation_profile_{timestamp}.prof"
    profile_text_path = output_dir / f"simulation_profile_{timestamp}.txt"
    profile_json_path = output_dir / f"simulation_profile_{timestamp}.json"

    profiler.dump_stats(str(profile_binary_path))
    profile_text_path.write_text(profile_text, encoding="utf-8")
    profile_json_path.write_text(
        json.dumps(
            {
                "generated_at_utc": datetime.now(timezone.utc).isoformat(),
                "base_url": args.base_url,
                "workload": {
                    "requests": args.requests,
                    "concurrency": args.concurrency,
                },
                "summary": summary,
                "profile_sort": args.sort_by,
                "profile_top": args.top,
                "profile_files": {
                    "binary": str(profile_binary_path),
                    "text": str(profile_text_path),
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print("Simulation profile complete")
    print(f"Summary report: {profile_json_path}")
    print(f"Profile binary: {profile_binary_path}")
    print(f"Profile text: {profile_text_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
