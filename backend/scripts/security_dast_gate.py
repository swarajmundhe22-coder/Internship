from __future__ import annotations

import argparse
import asyncio
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import httpx


@dataclass
class GateResult:
    name: str
    passed: bool
    detail: str


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def register_engineer(client: httpx.AsyncClient, password: str) -> str:
    email = f"dast-{uuid4().hex[:10]}@example.com"
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


async def run_gate(base_url: str, password: str, output_dir: Path) -> tuple[bool, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    timeout = httpx.Timeout(20.0)
    results: list[GateResult] = []

    async with httpx.AsyncClient(base_url=base_url.rstrip("/"), timeout=timeout) as client:
        health = await client.get("/health")
        results.append(
            GateResult(
                name="health_endpoint",
                passed=health.status_code == 200,
                detail=f"status={health.status_code}",
            )
        )

        required_headers = {
            "x-content-type-options": "nosniff",
            "x-frame-options": "DENY",
            "referrer-policy": "no-referrer",
        }
        for header_key, expected in required_headers.items():
            actual = health.headers.get(header_key, "")
            results.append(
                GateResult(
                    name=f"header_{header_key}",
                    passed=actual.lower() == expected.lower(),
                    detail=f"expected={expected}; actual={actual or 'missing'}",
                )
            )

        valid_payload = {
            "material": {
                "name": "Carbon Steel",
                "alloy_group": "Ferrous",
                "density_kg_m3": 7850,
                "electrochemical_potential_v": -0.65,
            },
            "environment": {
                "temperature_c": 24,
                "relative_humidity_pct": 82,
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

        unauth_simulate = await client.post("/simulation/simulate", json=valid_payload)
        results.append(
            GateResult(
                name="simulate_requires_auth",
                passed=unauth_simulate.status_code in (401, 403),
                detail=f"status={unauth_simulate.status_code}",
            )
        )

        token = await register_engineer(client, password=password)

        malformed = await client.post(
            "/simulation/simulate",
            headers=auth_header(token),
            json={"material": {}, "environment": {}},
        )
        results.append(
            GateResult(
                name="simulate_payload_validation",
                passed=malformed.status_code == 422,
                detail=f"status={malformed.status_code}",
            )
        )
        valid = await client.post(
            "/simulation/simulate",
            headers=auth_header(token),
            json=valid_payload,
        )
        valid_ok = valid.status_code == 200 and bool(valid.json().get("simulation_id"))
        results.append(
            GateResult(
                name="simulate_authenticated_success",
                passed=valid_ok,
                detail=f"status={valid.status_code}",
            )
        )

    passed = all(item.passed for item in results)
    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "base_url": base_url,
        "passed": passed,
        "checks": [
            {"name": item.name, "passed": item.passed, "detail": item.detail}
            for item in results
        ],
    }

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")
    report_path = output_dir / f"security_dast_gate_{timestamp}.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return passed, report_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a lightweight DAST gate against API endpoints.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000/api/v1", help="API base URL with /api/v1")
    parser.add_argument("--password", default="StrongPass123", help="Password for temporary gate user")
    parser.add_argument(
        "--output-dir",
        default="artifacts/security_reports",
        help="Directory where security gate reports are written.",
    )
    parser.add_argument("--strict", action="store_true", help="Return non-zero when any gate check fails.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = (Path(__file__).resolve().parents[1] / output_dir).resolve()

    passed, report_path = asyncio.run(run_gate(args.base_url, args.password, output_dir))
    print(f"DAST gate status: {'PASS' if passed else 'FAIL'}")
    print(f"DAST report: {report_path}")
    if args.strict and not passed:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
