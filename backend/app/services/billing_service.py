from __future__ import annotations

import hashlib
import hmac
import json
from uuid import UUID

from app.core.config import get_settings
from app.models.tenant import BillingWebhookPayload, SubscriptionTier, TenantRead
from app.repositories.tenant_repository import TenantRepository


class BillingService:
    def __init__(self, tenant_repository: TenantRepository) -> None:
        self.tenant_repository = tenant_repository
        self.settings = get_settings()

    def verify_signature(self, *, body: bytes, signature: str | None) -> bool:
        secret = self.settings.paypal_webhook_secret or self.settings.paypal_secret
        if not secret:
            # Allow non-production local testing when webhook secret is not configured.
            return True
        if not signature:
            return False
        digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(digest, signature)

    async def handle_webhook(self, payload: BillingWebhookPayload) -> TenantRead:
        existing = await self.tenant_repository.get_by_id(payload.tenant_id)
        if existing is None:
            raise ValueError("Tenant not found")

        normalized_event = payload.event_type.strip().lower()
        if normalized_event in {
            "billing.subscription.created",
            "subscription.created",
            "create",
            "billing.subscription.updated",
            "subscription.updated",
            "update",
        }:
            next_status = "active"
            next_tier = payload.subscription_tier
        elif normalized_event in {"billing.subscription.cancelled", "subscription.cancelled", "cancel"}:
            next_status = "canceled"
            next_tier = SubscriptionTier.FREE
        elif normalized_event in {"billing.subscription.suspended", "subscription.suspended", "suspend"}:
            next_status = "suspended"
            next_tier = existing.subscription_tier
        elif normalized_event in {"billing.subscription.activated", "subscription.activated", "reactivate"}:
            next_status = "active"
            next_tier = payload.subscription_tier if payload.subscription_tier in SubscriptionTier.ALL else existing.subscription_tier
        else:
            raise ValueError("Unsupported billing event type")

        if next_tier not in SubscriptionTier.ALL:
            raise ValueError("Unsupported subscription tier")

        tenant = await self.tenant_repository.update_subscription_tier(
            tenant_id=payload.tenant_id,
            subscription_tier=next_tier,
            subscription_status=next_status,
        )
        if tenant is None:
            raise ValueError("Tenant not found")
        return TenantRead.model_validate(tenant)

    def parse_payload(self, event: dict[str, object]) -> BillingWebhookPayload:
        resource = event.get("resource") if isinstance(event.get("resource"), dict) else {}
        tenant_value = resource.get("tenant_id") or resource.get("custom_id") or event.get("tenant_id")
        tier_value = resource.get("subscription_tier") or resource.get("plan_name") or event.get("subscription_tier")

        normalized = str(tier_value or "").strip().lower().replace("$", "").replace(" ", "_")
        tier_map = {
            "free": SubscriptionTier.FREE,
            "0": SubscriptionTier.FREE,
            "professional": SubscriptionTier.PROFESSIONAL,
            "999": SubscriptionTier.PROFESSIONAL,
            "enterprise_elite": SubscriptionTier.ENTERPRISE_ELITE,
            "enterprise": SubscriptionTier.ENTERPRISE_ELITE,
            "1999": SubscriptionTier.ENTERPRISE_ELITE,
        }
        resolved_tier = tier_map.get(normalized, normalized)

        parsed = BillingWebhookPayload(
            event_type=str(event.get("event_type") or "subscription.updated"),
            tenant_id=UUID(str(tenant_value)),
            subscription_tier=resolved_tier,
        )
        return parsed

    @staticmethod
    def normalize_for_signature(event: dict[str, object]) -> bytes:
        return json.dumps(event, separators=(",", ":"), sort_keys=True).encode("utf-8")
