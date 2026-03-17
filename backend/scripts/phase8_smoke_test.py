from __future__ import annotations

import argparse
import asyncio
import base64
import json
from dataclasses import dataclass
from uuid import uuid4

import httpx


@dataclass
class SmokeContext:
    base_url: str
    password: str


def _decode_jwt_sub(token: str) -> str:
    payload = token.split(".")[1]
    padded = payload + "=" * (-len(payload) % 4)
    decoded = json.loads(base64.urlsafe_b64decode(padded.encode("utf-8")).decode("utf-8"))
    return str(decoded["sub"])


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _register_user(client: httpx.AsyncClient, *, role: str, password: str, prefix: str) -> tuple[str, str]:
    email = f"{prefix}-{uuid4().hex}@example.com"
    response = await client.post(
        "/auth/register",
        json={"email": email, "password": password, "role": role},
    )
    if response.status_code != 200:
        raise RuntimeError(f"register {role} failed: {response.status_code} {response.text}")
    token = response.json().get("access_token")
    if not token:
        raise RuntimeError(f"register {role} missing access token")
    return email, token


async def run_smoke(ctx: SmokeContext) -> None:
    timeout = httpx.Timeout(25.0)
    async with httpx.AsyncClient(base_url=ctx.base_url, timeout=timeout) as client:
        print("[1/9] Register admin + engineer")
        _, admin_token = await _register_user(
            client,
            role="admin",
            password=ctx.password,
            prefix="phase8-smoke-admin",
        )
        _, engineer_token = await _register_user(
            client,
            role="engineer",
            password=ctx.password,
            prefix="phase8-smoke-engineer",
        )

        print("[2/9] Create tenant and bind engineer")
        tenant_response = await client.post(
            "/tenants",
            json={"org_name": f"Phase8 Smoke {uuid4().hex[:8]}", "subscription_tier": "professional"},
            headers=_auth_header(admin_token),
        )
        if tenant_response.status_code != 200:
            raise RuntimeError(f"create tenant failed: {tenant_response.status_code} {tenant_response.text}")
        tenant_id = tenant_response.json()["id"]

        engineer_user_id = _decode_jwt_sub(engineer_token)
        add_member = await client.post(
            f"/tenants/{tenant_id}/users",
            json={"user_id": engineer_user_id, "role": "admin"},
            headers=_auth_header(admin_token),
        )
        if add_member.status_code != 200:
            raise RuntimeError(f"add tenant member failed: {add_member.status_code} {add_member.text}")

        print("[3/9] Create material + environment")
        material = await client.post(
            "/materials",
            json={
                "name": f"Smoke Alloy {uuid4().hex[:8]}",
                "alloy_group": "Ferrous",
                "density_kg_m3": 7850.0,
                "electrochemical_potential_v": -0.61,
            },
            headers=_auth_header(engineer_token),
        )
        environment = await client.post(
            "/environment",
            json={
                "profile_name": f"Smoke Env {uuid4().hex[:8]}",
                "temperature_c": 23.0,
                "relative_humidity_pct": 81.0,
                "chloride_ppm": 11000.0,
                "ph": 7.2,
                "dissolved_oxygen_mg_l": 6.9,
            },
            headers=_auth_header(engineer_token),
        )
        if material.status_code != 200:
            raise RuntimeError(f"create material failed: {material.status_code} {material.text}")
        if environment.status_code != 200:
            raise RuntimeError(f"create environment failed: {environment.status_code} {environment.text}")

        print("[4/9] Create simulation with accuracy >= 0.95")
        simulation = await client.post(
            "/simulation",
            json={
                "material_id": material.json()["id"],
                "environment_id": environment.json()["id"],
                "exposed_area_m2": 10.5,
                "exposure_time_hours": 900.0,
                "corrosion_rate_mm_per_year": 0.09,
                "estimated_lifespan_years": 13.5,
                "accuracy_score": 0.97,
                "risk_classification": "moderate",
            },
            headers=_auth_header(engineer_token),
        )
        if simulation.status_code != 201:
            raise RuntimeError(f"create simulation failed: {simulation.status_code} {simulation.text}")
        simulation_id = simulation.json()["id"]

        print("[5/9] Generate digital twin")
        twin = await client.post(
            "/visualization/twin",
            json={"simulation_id": simulation_id, "tenant_id": tenant_id, "mode": "twin"},
            headers=_auth_header(engineer_token),
        )
        if twin.status_code != 200:
            raise RuntimeError(f"twin generation failed: {twin.status_code} {twin.text}")
        twin_body = twin.json()
        if float(twin_body.get("overlay_accuracy", 0.0)) < 0.95:
            raise RuntimeError("twin overlay accuracy below 0.95")

        print("[6/9] Prepare VR playback")
        playback = await client.post(
            "/visualization/playback",
            json={"simulation_id": simulation_id, "tenant_id": tenant_id, "mode": "vr"},
            headers=_auth_header(engineer_token),
        )
        if playback.status_code != 200:
            raise RuntimeError(f"playback failed: {playback.status_code} {playback.text}")
        playback_body = playback.json()
        if playback_body.get("status") != "playback_ready":
            raise RuntimeError("playback status is not playback_ready")

        print("[7/9] Export investor artifact")
        export = await client.post(
            "/visualization/export",
            json={
                "simulation_id": simulation_id,
                "tenant_id": tenant_id,
                "mode": "vr",
                "file_type": "mp4",
            },
            headers=_auth_header(engineer_token),
        )
        if export.status_code != 200:
            raise RuntimeError(f"export failed: {export.status_code} {export.text}")
        export_body = export.json()
        if export_body.get("status") != "exported":
            raise RuntimeError("export status is not exported")

        print("[8/9] Verify visualization export audit trail")
        found = False
        for event_type in ("EXPORT_COMPLETED", "visualization.export"):
            logs = await client.get(
                "/audit-logs",
                params={"event_type": event_type, "page": 1, "page_size": 50},
                headers=_auth_header(admin_token),
            )
            if logs.status_code != 200:
                raise RuntimeError(f"audit query failed: {logs.status_code} {logs.text}")
            items = logs.json().get("items", [])
            for item in items:
                if not item.get("success"):
                    continue
                detail = str(item.get("detail") or "")
                if tenant_id in detail and simulation_id in detail:
                    found = True
                    break
            if found:
                break
        if not found:
            raise RuntimeError("no successful visualization.export audit event found for this run")

        print("[9/9] Smoke flow complete")
        print(f"PASS tenant={tenant_id} simulation={simulation_id} export={export_body['export']['file_uri']}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Phase 8 mission-control smoke test")
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:8000/api/v1",
        help="API base URL including /api/v1 prefix",
    )
    parser.add_argument(
        "--password",
        default="StrongPass123",
        help="Password used for temporary smoke users",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    ctx = SmokeContext(base_url=args.base_url.rstrip("/"), password=args.password)
    try:
        asyncio.run(run_smoke(ctx))
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
