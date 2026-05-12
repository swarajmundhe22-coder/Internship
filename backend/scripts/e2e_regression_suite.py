from __future__ import annotations

import argparse
import asyncio
import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from uuid import uuid4

import httpx


def percentile(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(max(math.ceil(len(ordered) * p) - 1, 0), len(ordered) - 1)
    return float(ordered[index])


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def simulation_payload(material: dict[str, object], environment: dict[str, object]) -> dict[str, object]:
    return {
        "material": {
            "name": str(material["name"]),
            "alloy_group": str(material["alloy_group"]),
            "density_kg_m3": float(material["density_kg_m3"]),
            "electrochemical_potential_v": float(material["electrochemical_potential_v"]),
        },
        "environment": {
            "temperature_c": float(environment["temperature_c"]),
            "relative_humidity_pct": float(environment["relative_humidity_pct"]),
            "chloride_ppm": float(environment["chloride_ppm"]),
            "ph": float(environment["ph"]),
            "dissolved_oxygen_mg_l": float(environment["dissolved_oxygen_mg_l"]),
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


async def run_suite(
    base_url: str,
    password: str,
    *,
    p99_budget_ms: int,
    error_budget_rate: float,
    telemetry_requests: int,
    output_dir: Path,
) -> tuple[bool, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)

    checks: dict[str, bool] = {}
    evidence: dict[str, object] = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "base_url": base_url,
        "checks": checks,
    }

    async with httpx.AsyncClient(base_url=base_url.rstrip("/"), timeout=httpx.Timeout(30.0)) as client:
        email = f"e2e-{uuid4().hex[:10]}@example.com"
        register = await client.post(
            "/auth/register",
            json={"email": email, "password": password, "role": "engineer"},
        )
        checks["register_engineer"] = register.status_code == 200
        if register.status_code != 200:
            raise RuntimeError(f"Register failed: {register.status_code} {register.text}")

        token = register.json()["access_token"]
        headers = auth_header(token)

        material_create = await client.post(
            "/materials",
            json={
                "name": f"E2E Material {uuid4().hex[:8]}",
                "alloy_group": "Ferrous",
                "density_kg_m3": 7850,
                "electrochemical_potential_v": -0.62,
            },
            headers=headers,
        )
        checks["material_create"] = material_create.status_code == 201
        material = material_create.json()

        environment_create = await client.post(
            "/environment",
            json={
                "profile_name": f"E2E Env {uuid4().hex[:8]}",
                "temperature_c": 24,
                "relative_humidity_pct": 82,
                "chloride_ppm": 12000,
                "ph": 7.2,
                "dissolved_oxygen_mg_l": 7.0,
            },
            headers=headers,
        )
        checks["environment_create"] = environment_create.status_code == 201
        environment = environment_create.json()

        simulation_predict = await client.post(
            "/simulation/simulate",
            headers=headers,
            json=simulation_payload(material, environment),
        )
        checks["simulation_predict"] = simulation_predict.status_code == 200

        simulation_record = await client.post(
            "/simulation",
            headers=headers,
            json={
                "material_id": material["id"],
                "environment_id": environment["id"],
                "exposed_area_m2": 20,
                "exposure_time_hours": 1200,
                "corrosion_rate_mm_per_year": 0.11,
                "estimated_lifespan_years": 12,
                "risk_classification": "high",
            },
        )
        checks["simulation_record_create"] = simulation_record.status_code == 201
        simulation_record_payload = simulation_record.json()

        report_create = await client.post(
            "/reports",
            headers=headers,
            json={
                "simulation_id": simulation_record_payload["id"],
                "report_uri": "s3://on-looker/e2e/report.pdf",
                "status": "generated",
                "version": 1,
            },
        )
        checks["report_create"] = report_create.status_code == 201
        report_payload = report_create.json()

        report_update = await client.put(
            f"/reports/{report_payload['id']}",
            headers=headers,
            json={"expected_version": report_payload["version"], "status": "archived"},
        )
        checks["report_update"] = report_update.status_code == 200

        report_stale = await client.put(
            f"/reports/{report_payload['id']}",
            headers=headers,
            json={"expected_version": report_payload["version"], "status": "generated"},
        )
        checks["report_optimistic_lock"] = report_stale.status_code == 409

        oauth_authorize = await client.get("/auth/oauth/google/authorize")
        if oauth_authorize.status_code == 503:
            detail = oauth_authorize.json().get("detail", {})
            checks["oauth_failure_classification"] = detail.get("code") == "oauth_provider_not_configured"
        elif oauth_authorize.status_code == 200:
            auth_url = oauth_authorize.json().get("authorization_url", "")
            scope_values = parse_qs(urlparse(auth_url).query).get("scope", [""])
            checks["oauth_failure_classification"] = "profile" in scope_values[0]
        else:
            checks["oauth_failure_classification"] = False

        telemetry_latencies: list[float] = []
        telemetry_error_count = 0
        for _ in range(telemetry_requests):
            start = time.perf_counter()
            response = await client.post(
                "/simulation/simulate",
                headers=headers,
                json=simulation_payload(material, environment),
            )
            telemetry_latencies.append((time.perf_counter() - start) * 1000.0)
            telemetry_error_count += int(response.status_code >= 500)

        ops_performance = await client.get(
            "/ops/performance",
            headers=headers,
            params={"path": "/api/v1/simulation/simulate", "include_paths": "true", "top": "3"},
        )
        checks["ops_performance_endpoint"] = ops_performance.status_code == 200

        runtime_payload: dict[str, object] = {}
        if ops_performance.status_code == 200:
            runtime_payload = ops_performance.json()
            runtime_latency = runtime_payload.get("latency_ms", {}) if isinstance(runtime_payload, dict) else {}
            runtime_p99 = float(runtime_latency.get("p99", 0.0))
            runtime_error_rate = float(runtime_payload.get("error_rate_5xx", 1.0))

            checks["ops_runtime_p99_budget"] = runtime_p99 <= p99_budget_ms
            checks["ops_runtime_error_budget"] = runtime_error_rate <= error_budget_rate
        else:
            checks["ops_runtime_p99_budget"] = False
            checks["ops_runtime_error_budget"] = False

    evidence["telemetry_workload"] = {
        "requests": telemetry_requests,
        "client_p95_latency_ms": percentile(telemetry_latencies, 0.95),
        "client_p99_latency_ms": percentile(telemetry_latencies, 0.99),
        "client_error_rate_5xx": (telemetry_error_count / telemetry_requests) if telemetry_requests else 1.0,
    }
    evidence["runtime_metrics"] = runtime_payload
    evidence["budgets"] = {
        "p99_latency_ms": p99_budget_ms,
        "error_rate_5xx": error_budget_rate,
    }

    passed = all(checks.values())
    evidence["passed"] = passed

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")
    report_path = output_dir / f"e2e_regression_{timestamp}.json"
    report_path.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    return passed, report_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run end-to-end regression suite for production readiness.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000/api/v1", help="API base URL with /api/v1")
    parser.add_argument("--password", default="StrongPass123", help="Password for temporary E2E user")
    parser.add_argument("--p99-budget-ms", type=int, default=2000, help="Maximum allowed runtime p99 latency")
    parser.add_argument(
        "--error-budget-rate",
        type=float,
        default=0.02,
        help="Maximum allowed runtime 5xx error budget",
    )
    parser.add_argument("--telemetry-requests", type=int, default=40, help="Simulation requests used to seed runtime telemetry")
    parser.add_argument(
        "--output-dir",
        default="artifacts/performance_reports",
        help="Directory where E2E regression reports are written.",
    )
    parser.add_argument("--strict", action="store_true", help="Return non-zero when checks fail.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = (Path(__file__).resolve().parents[1] / output_dir).resolve()

    passed, report_path = asyncio.run(
        run_suite(
            args.base_url,
            args.password,
            p99_budget_ms=args.p99_budget_ms,
            error_budget_rate=args.error_budget_rate,
            telemetry_requests=args.telemetry_requests,
            output_dir=output_dir,
        )
    )

    print(f"E2E regression suite status: {'PASS' if passed else 'FAIL'}")
    print(f"E2E report: {report_path}")
    if args.strict and not passed:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
