from __future__ import annotations

import logging
from urllib.parse import urlparse, urlunparse
from uuid import uuid4

from fastapi import APIRouter, Depends

from app.api.dependencies import get_audit_log_repository
from app.core.config import get_settings
from app.models.demo import DemoRequestCreate, DemoRequestResponse
from app.repositories.audit_log_repository import AuditLogRepository

router = APIRouter(prefix="/demo", tags=["demo"])
logger = logging.getLogger(__name__)


def _normalize_demo_booking_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.netloc.lower() != "calendly.com":
        return url

    segments = [segment for segment in parsed.path.split("/") if segment]
    if len(segments) >= 2 and segments[-1].lower() == "request-demo":
        normalized_path = "/" + "/".join(segments[:-1])
        return urlunparse((parsed.scheme, parsed.netloc, normalized_path, "", "", ""))

    return url


@router.post("/request", response_model=DemoRequestResponse)
async def create_demo_request(
    payload: DemoRequestCreate,
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> DemoRequestResponse:
    settings = get_settings()
    request_id = uuid4()

    try:
        await audit_logs.create(
            event_type="demo.request.submit",
            success=True,
            user_email=str(payload.email),
            detail=(
                f"request_id={request_id}; company={payload.company}; role={payload.role}; "
                f"auth_provider={payload.preferred_auth_provider}"
            ),
        )
    except Exception:
        # Demo intake should stay available even if audit storage is temporarily unavailable.
        logger.exception("Unable to persist demo.request.submit audit event")

    return DemoRequestResponse(
        request_id=request_id,
        message="Demo request received. Use the booking URL to schedule your session.",
        booking_url=_normalize_demo_booking_url(settings.demo_booking_url),
    )


@router.get("/booking-url")
async def get_booking_url() -> dict[str, str]:
    settings = get_settings()
    return {"booking_url": _normalize_demo_booking_url(settings.demo_booking_url)}
