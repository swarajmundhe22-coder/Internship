from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.api.dependencies import get_audit_log_repository, get_tenant_repository
from app.models.tenant import TenantRead
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.tenant_repository import TenantRepository
from app.services.billing_service import BillingService

router = APIRouter(prefix="/billing", tags=["billing"])


def get_billing_service(
    tenant_repository: TenantRepository = Depends(get_tenant_repository),
) -> BillingService:
    return BillingService(tenant_repository=tenant_repository)


@router.post("/webhook")
async def paypal_webhook(
    event: dict[str, object],
    x_paypal_signature: str | None = Header(default=None, alias="X-PayPal-Signature"),
    service: BillingService = Depends(get_billing_service),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> dict[str, str | TenantRead]:
    body = service.normalize_for_signature(event)
    if not service.verify_signature(body=body, signature=x_paypal_signature):
        await audit_logs.create(
            event_type="billing.paypal.signature_failed",
            success=False,
            detail="invalid_signature",
        )
        await audit_logs.create(
            event_type="BILLING_EVENT",
            success=False,
            detail="invalid_signature",
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid PayPal signature")

    try:
        parsed = service.parse_payload(event)
        tenant = await service.handle_webhook(parsed)
        await audit_logs.create(
            event_type=f"billing.paypal.{parsed.event_type.strip().lower()}",
            tenant_id=parsed.tenant_id,
            success=True,
            detail=f"tenant_id={parsed.tenant_id};tier={tenant.subscription_tier};status={tenant.subscription_status}",
        )
        await audit_logs.create(
            event_type="BILLING_EVENT",
            tenant_id=parsed.tenant_id,
            success=True,
            detail=f"event_type={parsed.event_type};tier={tenant.subscription_tier};status={tenant.subscription_status}",
        )
    except ValueError as exc:
        parsed_event_type = str(event.get("event_type") or "unknown").strip().lower()
        await audit_logs.create(
            event_type=f"billing.paypal.{parsed_event_type}",
            success=False,
            detail=str(exc),
        )
        await audit_logs.create(
            event_type="BILLING_EVENT",
            success=False,
            detail=f"event_type={parsed_event_type};error={str(exc)}",
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return {
        "status": "success",
        "tenant": tenant,
    }
