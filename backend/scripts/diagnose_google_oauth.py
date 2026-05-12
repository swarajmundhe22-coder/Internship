from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import httpx

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import get_settings  # noqa: E402


def resolve_path(path_arg: str) -> Path:
    candidate = Path(path_arg)
    if candidate.is_absolute():
        return candidate
    return (BACKEND_ROOT / candidate).resolve()


def _check_config_presence() -> list[dict[str, object]]:
    settings = get_settings()
    checks: list[dict[str, object]] = []

    checks.append(
        {
            "name": "google_client_id_present",
            "passed": bool(settings.oauth_google_client_id),
            "value": bool(settings.oauth_google_client_id),
            "expected": True,
        }
    )
    checks.append(
        {
            "name": "google_client_secret_present",
            "passed": bool(settings.oauth_google_client_secret),
            "value": bool(settings.oauth_google_client_secret),
            "expected": True,
        }
    )
    checks.append(
        {
            "name": "google_redirect_uri_present",
            "passed": bool(settings.oauth_google_redirect_uri),
            "value": settings.oauth_google_redirect_uri,
            "expected": "non-empty URI",
        }
    )

    redirect_uri = settings.oauth_google_redirect_uri or ""
    parsed_redirect = urlparse(redirect_uri)
    checks.append(
        {
            "name": "google_redirect_uri_path",
            "passed": parsed_redirect.path.endswith("/api/v1/auth/oauth/google/callback"),
            "value": parsed_redirect.path,
            "expected": "/api/v1/auth/oauth/google/callback",
        }
    )
    checks.append(
        {
            "name": "google_redirect_uri_scheme",
            "passed": parsed_redirect.scheme in {"http", "https"},
            "value": parsed_redirect.scheme,
            "expected": "http or https",
        }
    )

    if settings.environment.lower() == "production":
        checks.append(
            {
                "name": "google_redirect_uri_https_in_production",
                "passed": parsed_redirect.scheme == "https",
                "value": parsed_redirect.scheme,
                "expected": "https",
            }
        )

    return checks


def _inspect_authorization_url(authorization_url: str) -> list[dict[str, object]]:
    settings = get_settings()
    parsed = urlparse(authorization_url)
    params = parse_qs(parsed.query)
    scopes = set((params.get("scope", [""])[0] or "").split())

    checks: list[dict[str, object]] = []
    checks.append(
        {
            "name": "auth_url_has_state",
            "passed": bool(params.get("state", [""])[0]),
            "value": bool(params.get("state", [""])[0]),
            "expected": True,
        }
    )
    checks.append(
        {
            "name": "auth_url_client_id_matches",
            "passed": params.get("client_id", [""])[0] == (settings.oauth_google_client_id or ""),
            "value": params.get("client_id", [""])[0],
            "expected": settings.oauth_google_client_id or "",
        }
    )
    checks.append(
        {
            "name": "auth_url_redirect_uri_matches",
            "passed": params.get("redirect_uri", [""])[0] == (settings.oauth_google_redirect_uri or ""),
            "value": params.get("redirect_uri", [""])[0],
            "expected": settings.oauth_google_redirect_uri or "",
        }
    )
    checks.append(
        {
            "name": "auth_url_scope_contains_openid",
            "passed": "openid" in scopes,
            "value": sorted(scopes),
            "expected": "openid",
        }
    )
    checks.append(
        {
            "name": "auth_url_scope_contains_email",
            "passed": "email" in scopes,
            "value": sorted(scopes),
            "expected": "email",
        }
    )
    checks.append(
        {
            "name": "auth_url_scope_contains_profile",
            "passed": "profile" in scopes,
            "value": sorted(scopes),
            "expected": "profile",
        }
    )
    checks.append(
        {
            "name": "auth_url_has_nonce",
            "passed": bool(params.get("nonce", [""])[0]),
            "value": bool(params.get("nonce", [""])[0]),
            "expected": True,
        }
    )
    return checks


async def run_diagnostics(
    *,
    base_url: str,
    return_to: str,
    login_hint: str | None,
    timeout_seconds: float,
) -> dict[str, object]:
    checks = _check_config_presence()
    authorize_response: dict[str, object] = {
        "status_code": None,
        "authorization_url": None,
        "error": None,
    }

    params = {"return_to": return_to}
    if login_hint:
        params["login_hint"] = login_hint

    try:
        async with httpx.AsyncClient(base_url=base_url.rstrip("/"), timeout=timeout_seconds) as client:
            response = await client.get("/auth/oauth/google/authorize", params=params)
    except Exception as exc:
        authorize_response["error"] = f"request_failed: {exc}"
        return {
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "base_url": base_url,
            "checks": checks,
            "authorize_response": authorize_response,
            "manual_console_checks": [
                "Google Cloud OAuth consent screen is published for target user type.",
                "Authorized redirect URI exactly matches OAUTH_GOOGLE_REDIRECT_URI.",
                "Firebase Authentication authorized domains include production host.",
            ],
            "passed": False,
        }

    authorize_response["status_code"] = response.status_code

    if response.status_code == 200:
        payload = response.json()
        authorization_url = payload.get("authorization_url")
        authorize_response["authorization_url"] = authorization_url
        if isinstance(authorization_url, str) and authorization_url:
            checks.extend(_inspect_authorization_url(authorization_url))
        else:
            checks.append(
                {
                    "name": "authorize_response_contains_url",
                    "passed": False,
                    "value": authorization_url,
                    "expected": "non-empty authorization URL",
                }
            )
    else:
        try:
            payload = response.json()
        except ValueError:
            payload = {"raw": response.text}
        authorize_response["error"] = payload
        checks.append(
            {
                "name": "authorize_endpoint_healthy",
                "passed": False,
                "value": response.status_code,
                "expected": 200,
            }
        )

    passed = all(bool(item.get("passed")) for item in checks)
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "base_url": base_url,
        "checks": checks,
        "authorize_response": authorize_response,
        "manual_console_checks": [
            "Google Cloud OAuth consent screen is published for target user type.",
            "Google OAuth app is in the correct project and client ID matches deployment secret.",
            "Authorized redirect URI exactly matches OAUTH_GOOGLE_REDIRECT_URI.",
            "Firebase Authentication authorized domains include all app hosts used for popup flow.",
            "Requested scopes are approved on consent screen: openid, email, profile.",
        ],
        "passed": passed,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Diagnose Google OAuth configuration and authorize endpoint health.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000/api/v1", help="Backend API base URL including /api/v1")
    parser.add_argument(
        "--return-to",
        default="http://localhost:3000/auth/oauth/callback?next=%2Fdashboard",
        help="Frontend callback URL used for OAuth state return_to",
    )
    parser.add_argument("--login-hint", default="", help="Optional login_hint email")
    parser.add_argument("--timeout-seconds", type=float, default=10.0, help="HTTP timeout for diagnostics")
    parser.add_argument(
        "--output-dir",
        default="artifacts/security_reports",
        help="Directory where diagnostic report JSON is written",
    )
    parser.add_argument("--strict", action="store_true", help="Exit with non-zero status when checks fail")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = resolve_path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    report = asyncio.run(
        run_diagnostics(
            base_url=args.base_url,
            return_to=args.return_to,
            login_hint=args.login_hint or None,
            timeout_seconds=args.timeout_seconds,
        )
    )

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")
    report_path = output_dir / f"google_oauth_diagnostics_{timestamp}.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"Google OAuth diagnostics: {'PASS' if report['passed'] else 'FAIL'}")
    print(f"Report: {report_path}")

    if args.strict and not report["passed"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
