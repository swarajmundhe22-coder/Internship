from __future__ import annotations

import argparse
import asyncio
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from uuid import uuid4

import httpx


@dataclass
class Sample:
    case: str
    status_code: int


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def valid_payload() -> dict[str, object]:
    return {
        "material": {
            "name": "Carbon Steel",
            "alloy_group": "Ferrous",
            "density_kg_m3": 7850,
            "electrochemical_potential_v": -0.65,
        },
        "environment": {
            "temperature_c": 26,
            "relative_humidity_pct": 81,
            "chloride_ppm": 12000,
            "ph": 7.2,
            "dissolved_oxygen_mg_l": 6.5,
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
    email = f"chaos-{uuid4().hex[:10]}@example.com"
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


async def post_simulation(
    client: httpx.AsyncClient,
    *,
    case: str,
    payload: dict[str, object],
    headers: dict[str, str] | None,
) -> Sample:
    try:
        response = await client.post("/simulation/simulate", json=payload, headers=headers)
        return Sample(case=case, status_code=response.status_code)
    except Exception:
        return Sample(case=case, status_code=599)


async def run_gate(
    base_url: str,
    password: str,
    *,
    valid_burst_requests: int,
    malformed_burst_requests: int,
    concurrency: int,
    output_dir: Path,
) -> tuple[bool, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    timeout = httpx.Timeout(30.0)

    async with httpx.AsyncClient(base_url=base_url.rstrip("/"), timeout=timeout) as client:
        token = await register_engineer(client, password=password)
        authorized_headers = auth_header(token)

        samples: list[Sample] = []

        # Single-shot control checks first.
        samples.append(
            await post_simulation(
                client,
                case="unauthorized_empty",
                payload=valid_payload(),
                headers=None,
            )
        )
        samples.append(
            await post_simulation(
                client,
                case="invalid_token",
                payload=valid_payload(),
                headers=auth_header("invalid-token"),
            )
        )
        samples.append(
            await post_simulation(
                client,
                case="negative_values",
                payload={
                    "material": {"name": "Carbon Steel", "alloy_group": "Ferrous", "density_kg_m3": 7850, "electrochemical_potential_v": -0.65},
                    "environment": {"temperature_c": -100, "relative_humidity_pct": -5, "chloride_ppm": 0, "ph": 99, "dissolved_oxygen_mg_l": -1},
                    "exposed_area_m2": -1,
                    "exposure_time_hours": -1,
                },
                headers=authorized_headers,
            )
        )

        semaphore = asyncio.Semaphore(concurrency)

        async def run_case(case: str, payload: dict[str, object], headers: dict[str, str] | None) -> None:
            async with semaphore:
                sample = await post_simulation(client, case=case, payload=payload, headers=headers)
                samples.append(sample)

        valid_tasks = [
            run_case("valid_burst", valid_payload(), authorized_headers)
            for _ in range(valid_burst_requests)
        ]
        malformed_tasks = [
            run_case("malformed_burst", {"material": {}, "environment": {}}, authorized_headers)
            for _ in range(malformed_burst_requests)
        ]

        await asyncio.gather(*valid_tasks, *malformed_tasks)

    by_case: dict[str, list[int]] = {}
    for sample in samples:
        by_case.setdefault(sample.case, []).append(sample.status_code)

    unexpected_5xx = sum(1 for sample in samples if sample.status_code >= 500)
    valid_statuses = by_case.get("valid_burst", [])
    malformed_statuses = by_case.get("malformed_burst", [])

    valid_success_rate = mean([1.0 if code == 200 else 0.0 for code in valid_statuses]) if valid_statuses else 0.0
    malformed_safe_rate = mean([1.0 if code == 422 else 0.0 for code in malformed_statuses]) if malformed_statuses else 0.0

    checks = {
        "no_unexpected_5xx": unexpected_5xx == 0,
        "valid_burst_success_rate": valid_success_rate >= 0.98,
        "malformed_burst_controlled_rejection": malformed_safe_rate >= 0.98,
        "unauthorized_is_rejected": all(code in (401, 403) for code in by_case.get("unauthorized_empty", [])),
        "invalid_token_is_rejected": all(code in (401, 403) for code in by_case.get("invalid_token", [])),
        "negative_values_are_rejected": all(code == 422 for code in by_case.get("negative_values", [])),
    }
    passed = all(checks.values())

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "base_url": base_url,
        "passed": passed,
        "summary": {
            "total_samples": len(samples),
            "unexpected_5xx": unexpected_5xx,
            "valid_success_rate": valid_success_rate,
            "malformed_safe_rate": malformed_safe_rate,
        },
        "checks": checks,
        "status_by_case": by_case,
    }

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")
    report_path = output_dir / f"failure_mode_chaos_gate_{timestamp}.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return passed, report_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run burst failure-mode and chaos resilience checks against the API.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000/api/v1", help="API base URL with /api/v1")
    parser.add_argument("--password", default="StrongPass123", help="Password for temporary gate user")
    parser.add_argument("--valid-burst-requests", type=int, default=50, help="Number of concurrent valid requests")
    parser.add_argument(
        "--malformed-burst-requests",
        type=int,
        default=50,
        help="Number of concurrent malformed requests",
    )
    parser.add_argument("--concurrency", type=int, default=20, help="Concurrency for burst runs")
    parser.add_argument(
        "--output-dir",
        default="artifacts/chaos_reports",
        help="Directory where chaos gate report is written.",
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
            valid_burst_requests=args.valid_burst_requests,
            malformed_burst_requests=args.malformed_burst_requests,
            concurrency=args.concurrency,
            output_dir=output_dir,
        )
    )

    print(f"Failure-mode chaos gate status: {'PASS' if passed else 'FAIL'}")
    print(f"Chaos report: {report_path}")
    if args.strict and not passed:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
