from __future__ import annotations

import argparse
import asyncio
import gc
import json
import math
import random
import statistics
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

import httpx

try:
    import psutil  # type: ignore[import-not-found]
except Exception:  # pragma: no cover
    psutil = None  # type: ignore[assignment]


@dataclass
class EndpointScenario:
    name: str
    method: str
    path: str
    requires_auth: bool


@dataclass
class RequestSample:
    endpoint: str
    latency_ms: float
    status_code: int
    chaos_injected: bool


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = min(max(math.ceil(len(ordered) * p) - 1, 0), len(ordered) - 1)
    return float(ordered[idx])


def build_output_dir(path_arg: str) -> Path:
    path = Path(path_arg)
    if path.is_absolute():
        return path
    return (Path(__file__).resolve().parents[1] / path).resolve()


def default_profile() -> dict[str, float]:
    return {
        "simulate_post": 0.60,
        "auth_login_post": 0.15,
        "ops_performance_get": 0.10,
        "health_get": 0.15,
    }


async def register_user(client: httpx.AsyncClient, password: str) -> tuple[str, str]:
    email = f"perf-tier-{uuid4().hex}@example.com"
    register_resp = await client.post(
        "/auth/register",
        json={"email": email, "password": password, "role": "engineer"},
    )
    register_resp.raise_for_status()
    token = register_resp.json()["access_token"]
    return email, token


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


async def event_loop_lag_monitor(stop: asyncio.Event, lags: list[float], interval_s: float = 0.01) -> None:
    target = time.perf_counter()
    while not stop.is_set():
        target += interval_s
        await asyncio.sleep(interval_s)
        lag = max(time.perf_counter() - target, 0.0)
        lags.append(lag)


async def system_monitor(stop: asyncio.Event, samples: list[dict[str, float]]) -> None:
    if psutil is None:
        return

    process = psutil.Process()
    prev_disk = psutil.disk_io_counters()
    prev_time = time.perf_counter()

    while not stop.is_set():
        await asyncio.sleep(1)
        now = time.perf_counter()
        elapsed = max(now - prev_time, 0.001)

        cpu_pct = float(process.cpu_percent(interval=None))
        rss_mb = float(process.memory_info().rss / (1024 * 1024))

        disk_busy_pct = 0.0
        current_disk = psutil.disk_io_counters()
        if prev_disk and current_disk:
            delta_busy_ms = float((current_disk.read_time + current_disk.write_time) - (prev_disk.read_time + prev_disk.write_time))
            disk_busy_pct = min(max((delta_busy_ms / (elapsed * 1000.0)) * 100.0, 0.0), 100.0)
        prev_disk = current_disk
        prev_time = now

        samples.append(
            {
                "cpu_pct": cpu_pct,
                "rss_mb": rss_mb,
                "disk_busy_pct": disk_busy_pct,
            }
        )


async def issue_request(
    *,
    client: httpx.AsyncClient,
    scenario: EndpointScenario,
    token: str,
    email: str,
    password: str,
    chaos_fault_rate: float,
) -> RequestSample:
    chaos = random.random() < chaos_fault_rate
    headers: dict[str, str] = {}
    payload: dict[str, Any] | None = None

    if scenario.requires_auth:
        headers["Authorization"] = f"Bearer {token}"

    if scenario.name == "simulate_post":
        payload = simulation_payload()
        if chaos:
            payload = {"material": {}, "environment": {}}
    elif scenario.name == "auth_login_post":
        payload = {"email": email, "password": password}
        if chaos:
            payload = {"email": email, "password": "bad-password"}
    elif scenario.name == "ops_performance_get" and chaos:
        headers["Authorization"] = "Bearer invalid-token"

    if chaos and scenario.name == "health_get":
        await asyncio.sleep(0.20)

    started = time.perf_counter()
    try:
        if scenario.method == "GET":
            response = await client.get(scenario.path, headers=headers)
        else:
            response = await client.post(scenario.path, headers=headers, json=payload)
        status_code = response.status_code
    except Exception:
        status_code = 599
    latency_ms = max((time.perf_counter() - started) * 1000.0, 0.0)

    return RequestSample(
        endpoint=scenario.name,
        latency_ms=latency_ms,
        status_code=status_code,
        chaos_injected=chaos,
    )


def summarize_samples(
    *,
    samples: list[RequestSample],
    spike_ceiling_ms: int,
) -> dict[str, Any]:
    latencies = [sample.latency_ms for sample in samples]
    errors = sum(1 for sample in samples if sample.status_code >= 500)
    spikes = sum(1 for sample in samples if sample.latency_ms > spike_ceiling_ms)
    jitter = statistics.pstdev(latencies) if len(latencies) > 1 else 0.0

    return {
        "requests": len(samples),
        "errors_5xx": errors,
        "error_rate_5xx": (errors / len(samples)) if samples else 0.0,
        "latency_ms": {
            "p50": percentile(latencies, 0.50),
            "p95": percentile(latencies, 0.95),
            "p99": percentile(latencies, 0.99),
            "max": max(latencies) if latencies else 0.0,
            "jitter_stddev": jitter,
        },
        "spike_count_over_ceiling": spikes,
    }


def infer_bottlenecks(
    *,
    event_loop_lag_p99: float,
    system_stats: dict[str, float],
    ops_snapshot: dict[str, Any],
) -> list[str]:
    findings: list[str] = []

    if event_loop_lag_p99 > 0.050:
        findings.append("thread_starvation_or_event_loop_lag")

    if system_stats.get("disk_busy_p95", 0.0) > 70.0:
        findings.append("disk_io_queueing")

    if system_stats.get("cpu_p95", 0.0) > 85.0:
        findings.append("cpu_saturation")

    db_pool = ops_snapshot.get("db_pool", {}) if isinstance(ops_snapshot, dict) else {}
    if float(db_pool.get("p99_hold_seconds", 0.0)) >= float(db_pool.get("leak_threshold_seconds", 5)):
        findings.append("connection_hold_or_lock_contention")
    if float(db_pool.get("connection_churn_per_second", 0.0)) > 40.0:
        findings.append("connection_churn")

    caches = ops_snapshot.get("caches", []) if isinstance(ops_snapshot, dict) else []
    if caches and isinstance(caches, list):
        first = caches[0]
        if isinstance(first, dict) and float(first.get("hit_rate", 1.0)) < float(first.get("target_hit_rate", 0.95)):
            findings.append("cache_misses")

    return findings


def render_markdown_report(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# P99 Sustained Load Analysis")
    lines.append("")
    lines.append(f"Generated UTC: {payload['generated_at_utc']}")
    lines.append("")
    lines.append("## Pre-Optimization P99 Heatmap")
    lines.append("")
    lines.append("| Tier | Endpoint | P50 (ms) | P95 (ms) | P99 (ms) | Max (ms) | Spikes > Ceiling | SLA P99 | Status |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|---|")

    for tier in payload.get("tiers", []):
        tier_name = tier["name"]
        for endpoint_name, summary in tier.get("endpoint_metrics", {}).items():
            latency = summary["latency_ms"]
            status = "PASS" if summary.get("sla_p99_pass") and summary.get("spike_pass") else "FAIL"
            lines.append(
                "| {tier} | {endpoint} | {p50:.2f} | {p95:.2f} | {p99:.2f} | {maxv:.2f} | {spikes} | {sla} | {status} |".format(
                    tier=tier_name,
                    endpoint=endpoint_name,
                    p50=latency["p50"],
                    p95=latency["p95"],
                    p99=latency["p99"],
                    maxv=latency["max"],
                    spikes=summary.get("spike_count_over_ceiling", 0),
                    sla=summary.get("sla_p99_ms", 0),
                    status=status,
                )
            )

    lines.append("")
    lines.append("## 瓶颈分析")
    lines.append("")
    bottlenecks = payload.get("suspected_bottlenecks", [])
    if bottlenecks:
        for item in bottlenecks:
            lines.append(f"- {item}")
    else:
        lines.append("- No dominant bottleneck signatures were detected in this run.")

    lines.append("")
    lines.append("## Flame-Graph Evidence")
    lines.append("")
    lines.append("- Profile artifacts: see `artifacts/performance_reports/simulation_profile_*.prof` and `simulation_profile_*.txt`.")

    return "\n".join(lines) + "\n"


async def run_analysis(args: argparse.Namespace) -> tuple[dict[str, Any], Path, Path]:
    output_dir = build_output_dir(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    scenarios = {
        "health_get": EndpointScenario(name="health_get", method="GET", path="/health", requires_auth=False),
        "simulate_post": EndpointScenario(name="simulate_post", method="POST", path="/simulation/simulate", requires_auth=True),
        "auth_login_post": EndpointScenario(name="auth_login_post", method="POST", path="/auth/login", requires_auth=False),
        "ops_performance_get": EndpointScenario(name="ops_performance_get", method="GET", path="/ops/performance", requires_auth=True),
    }

    profile = default_profile()
    selected_scenarios = [scenarios[name] for name in profile.keys()]
    weights = [profile[scenario.name] for scenario in selected_scenarios]

    async with httpx.AsyncClient(base_url=args.base_url.rstrip("/"), timeout=httpx.Timeout(30.0)) as client:
        email, token = await register_user(client, args.password)

        gc_before = gc.get_stats() if hasattr(gc, "get_stats") else []

        stop_monitors = asyncio.Event()
        lag_samples: list[float] = []
        system_samples: list[dict[str, float]] = []
        lag_task = asyncio.create_task(event_loop_lag_monitor(stop_monitors, lag_samples))
        sys_task = asyncio.create_task(system_monitor(stop_monitors, system_samples))

        tiers = [
            ("low", 1, args.sla_low_p99_ms),
            ("medium", 3, args.sla_medium_p99_ms),
            ("high", 5, args.sla_high_p99_ms),
        ]

        tier_results: list[dict[str, Any]] = []
        for tier_name, multiplier, sla_p99 in tiers:
            tier_qps = args.baseline_qps * multiplier
            total_requests = max(int(tier_qps * args.duration_seconds), 1)
            interval = 1.0 / tier_qps

            samples: list[RequestSample] = []
            tasks: set[asyncio.Task[RequestSample]] = set()

            started = time.perf_counter()
            target = started
            for _ in range(total_requests):
                scenario = random.choices(selected_scenarios, weights=weights, k=1)[0]
                tasks.add(
                    asyncio.create_task(
                        issue_request(
                            client=client,
                            scenario=scenario,
                            token=token,
                            email=email,
                            password=args.password,
                            chaos_fault_rate=args.chaos_fault_rate,
                        )
                    )
                )
                target += interval
                sleep_for = target - time.perf_counter()
                if sleep_for > 0:
                    await asyncio.sleep(sleep_for)

            for task in asyncio.as_completed(tasks):
                samples.append(await task)

            by_endpoint: dict[str, list[RequestSample]] = {}
            for sample in samples:
                by_endpoint.setdefault(sample.endpoint, []).append(sample)

            endpoint_metrics: dict[str, Any] = {}
            for endpoint_name, endpoint_samples in by_endpoint.items():
                summary = summarize_samples(samples=endpoint_samples, spike_ceiling_ms=args.spike_ceiling_ms)
                summary["sla_p99_ms"] = sla_p99
                summary["sla_p99_pass"] = summary["latency_ms"]["p99"] <= sla_p99
                summary["spike_pass"] = summary["spike_count_over_ceiling"] == 0
                endpoint_metrics[endpoint_name] = summary

            tier_results.append(
                {
                    "name": tier_name,
                    "multiplier": multiplier,
                    "target_qps": tier_qps,
                    "duration_seconds": args.duration_seconds,
                    "endpoint_metrics": endpoint_metrics,
                    "tier_pass": all(metric.get("sla_p99_pass") and metric.get("spike_pass") for metric in endpoint_metrics.values()),
                }
            )

        stop_monitors.set()
        await lag_task
        await sys_task

        ops_resp = await client.get(
            "/ops/performance",
            headers={"Authorization": f"Bearer {token}"},
            params={"include_paths": "true", "top": "10"},
        )
        ops_snapshot = ops_resp.json() if ops_resp.status_code == 200 else {}

        gc_after = gc.get_stats() if hasattr(gc, "get_stats") else []

    lag_ms = [value * 1000.0 for value in lag_samples]
    system_cpu = [row["cpu_pct"] for row in system_samples] if system_samples else []
    system_rss = [row["rss_mb"] for row in system_samples] if system_samples else []
    system_disk = [row["disk_busy_pct"] for row in system_samples] if system_samples else []

    system_stats = {
        "cpu_p95": percentile(system_cpu, 0.95),
        "rss_mb_p95": percentile(system_rss, 0.95),
        "disk_busy_p95": percentile(system_disk, 0.95),
    }

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "base_url": args.base_url,
        "baseline_qps": args.baseline_qps,
        "duration_seconds": args.duration_seconds,
        "chaos_fault_rate": args.chaos_fault_rate,
        "spike_ceiling_ms": args.spike_ceiling_ms,
        "tiers": tier_results,
        "event_loop": {
            "lag_ms_p95": percentile(lag_ms, 0.95),
            "lag_ms_p99": percentile(lag_ms, 0.99),
            "lag_ms_max": max(lag_ms) if lag_ms else 0.0,
        },
        "system_stats": system_stats,
        "gc_delta": {
            "before": gc_before,
            "after": gc_after,
        },
        "ops_snapshot": ops_snapshot,
    }

    payload["suspected_bottlenecks"] = infer_bottlenecks(
        event_loop_lag_p99=payload["event_loop"]["lag_ms_p99"] / 1000.0,
        system_stats=system_stats,
        ops_snapshot=ops_snapshot,
    )

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")
    json_path = output_dir / f"sustained_p99_analysis_{stamp}.json"
    md_path = output_dir / f"sustained_p99_analysis_{stamp}.md"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    md_path.write_text(render_markdown_report(payload), encoding="utf-8")

    return payload, json_path, md_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run sustained low/medium/high tier latency analysis with bottleneck heuristics.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000/api/v1", help="Backend API base URL including /api/v1")
    parser.add_argument("--password", default="StrongPass123", help="Password for temporary benchmark account")
    parser.add_argument("--baseline-qps", type=int, default=20, help="Baseline QPS used for low load tier (1x)")
    parser.add_argument("--duration-seconds", type=int, default=120, help="Sustained duration per tier")
    parser.add_argument("--chaos-fault-rate", type=float, default=0.01, help="Fraction of requests with injected faults")
    parser.add_argument("--sla-low-p99-ms", type=int, default=100)
    parser.add_argument("--sla-medium-p99-ms", type=int, default=150)
    parser.add_argument("--sla-high-p99-ms", type=int, default=200)
    parser.add_argument("--spike-ceiling-ms", type=int, default=250)
    parser.add_argument("--output-dir", default="artifacts/performance_reports")
    parser.add_argument("--strict", action="store_true", help="Return non-zero when any tier breaches SLA/spike policy")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload, json_path, md_path = asyncio.run(run_analysis(args))

    all_passed = all(bool(tier.get("tier_pass")) for tier in payload.get("tiers", []))
    print(f"Sustained P99 analysis status: {'PASS' if all_passed else 'FAIL'}")
    print(f"JSON report: {json_path}")
    print(f"Markdown report: {md_path}")

    if args.strict and not all_passed:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
