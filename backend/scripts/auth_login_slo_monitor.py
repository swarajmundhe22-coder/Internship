from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.core.config import get_settings  # noqa: E402
from app.database.models import AuditLogEntity  # noqa: E402

AUTH_LOGIN_EVENTS = (
    "auth.login",
    "auth.login.otp.verify",
    "auth.sso.exchange",
    "auth.oauth.callback",
)


def resolve_path(path_arg: str) -> Path:
    candidate = Path(path_arg)
    if candidate.is_absolute():
        return candidate
    return (BACKEND_ROOT / candidate).resolve()


async def collect_auth_slo(hours: int) -> dict[str, object]:
    settings = get_settings()
    engine = create_async_engine(settings.database_url, echo=False, future=True)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    now = datetime.now(timezone.utc)
    since = now - timedelta(hours=hours)

    async with session_factory() as session:
        total_stmt = select(func.count()).where(
            AuditLogEntity.event_type.in_(AUTH_LOGIN_EVENTS),
            AuditLogEntity.created_at >= since,
        )
        success_stmt = select(func.count()).where(
            AuditLogEntity.event_type.in_(AUTH_LOGIN_EVENTS),
            AuditLogEntity.created_at >= since,
            AuditLogEntity.success.is_(True),
        )
        group_stmt = (
            select(
                AuditLogEntity.event_type,
                AuditLogEntity.success,
                func.count(),
            )
            .where(
                AuditLogEntity.event_type.in_(AUTH_LOGIN_EVENTS),
                AuditLogEntity.created_at >= since,
            )
            .group_by(AuditLogEntity.event_type, AuditLogEntity.success)
            .order_by(AuditLogEntity.event_type)
        )

        total = int((await session.execute(total_stmt)).scalar_one())
        success = int((await session.execute(success_stmt)).scalar_one())
        grouped_rows = (await session.execute(group_stmt)).all()

    await engine.dispose()

    grouped: dict[str, dict[str, int]] = {}
    for event_type, event_success, count in grouped_rows:
        if event_type not in grouped:
            grouped[event_type] = {"success": 0, "failure": 0}
        if event_success:
            grouped[event_type]["success"] += int(count)
        else:
            grouped[event_type]["failure"] += int(count)

    success_rate_pct = (success / total * 100.0) if total else 0.0

    return {
        "generated_at_utc": now.isoformat(),
        "window_hours": hours,
        "window_start_utc": since.isoformat(),
        "window_end_utc": now.isoformat(),
        "events_considered": list(AUTH_LOGIN_EVENTS),
        "attempt_count": total,
        "success_count": success,
        "failure_count": max(total - success, 0),
        "success_rate_pct": success_rate_pct,
        "by_event": grouped,
    }


def to_markdown(report: dict[str, object], target_success_rate_pct: float, passed: bool) -> str:
    lines: list[str] = []
    lines.append("# Auth Login SLO Report")
    lines.append("")
    lines.append(f"Generated UTC: {report['generated_at_utc']}")
    lines.append(f"Window: last {report['window_hours']} hours")
    lines.append(f"Target success rate: {target_success_rate_pct:.3f}%")
    lines.append(f"Observed success rate: {report['success_rate_pct']:.3f}%")
    lines.append(f"Status: {'PASS' if passed else 'FAIL'}")
    lines.append("")
    lines.append("## Aggregate")
    lines.append("")
    lines.append(f"- Attempts: {report['attempt_count']}")
    lines.append(f"- Success: {report['success_count']}")
    lines.append(f"- Failure: {report['failure_count']}")
    lines.append("")
    lines.append("## Event Breakdown")
    lines.append("")
    lines.append("| Event | Success | Failure |")
    lines.append("|---|---:|---:|")
    by_event = report.get("by_event", {})
    if isinstance(by_event, dict):
        for event_name in sorted(by_event.keys()):
            stats = by_event[event_name]
            if not isinstance(stats, dict):
                continue
            lines.append(f"| {event_name} | {int(stats.get('success', 0))} | {int(stats.get('failure', 0))} |")

    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compute login success SLO from auth audit logs.")
    parser.add_argument("--window-hours", type=int, default=24, help="Rolling window in hours")
    parser.add_argument(
        "--target-success-rate-pct",
        type=float,
        default=99.9,
        help="SLO threshold for auth login success rate",
    )
    parser.add_argument(
        "--output-dir",
        default="artifacts/security_reports",
        help="Output directory for SLO reports",
    )
    parser.add_argument("--strict", action="store_true", help="Exit non-zero if SLO target is missed")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = resolve_path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    report = asyncio.run(collect_auth_slo(hours=args.window_hours))
    passed = bool(report["attempt_count"]) and float(report["success_rate_pct"]) >= float(args.target_success_rate_pct)

    payload = {
        **report,
        "target_success_rate_pct": float(args.target_success_rate_pct),
        "passed": passed,
    }

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")
    json_path = output_dir / f"auth_login_slo_{timestamp}.json"
    md_path = output_dir / f"auth_login_slo_{timestamp}.md"

    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    md_path.write_text(to_markdown(payload, float(args.target_success_rate_pct), passed), encoding="utf-8")

    print(f"Auth login SLO: {'PASS' if passed else 'FAIL'}")
    print(f"JSON report: {json_path}")
    print(f"Markdown report: {md_path}")

    if args.strict and not passed:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
