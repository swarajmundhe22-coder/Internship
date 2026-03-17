from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.models.common import BaseDomainModel


class SubscriptionTier:
    FREE = "free"
    PROFESSIONAL = "professional"
    ENTERPRISE_ELITE = "enterprise_elite"

    ALL = {FREE, PROFESSIONAL, ENTERPRISE_ELITE}


class TenantRead(BaseDomainModel):
    id: UUID
    org_name: str
    subscription_tier: str
    subscription_status: str
    created_at: datetime
    updated_at: datetime


class TenantCreateRequest(BaseDomainModel):
    org_name: str = Field(min_length=2, max_length=180)
    subscription_tier: str = Field(default=SubscriptionTier.FREE)


class TenantUpdateRequest(BaseDomainModel):
    org_name: str | None = Field(default=None, min_length=2, max_length=180)
    subscription_tier: str | None = None
    subscription_status: str | None = None


class TenantUserLinkRequest(BaseDomainModel):
    user_id: UUID
    role: str = Field(default="viewer", min_length=2, max_length=30)


class TenantUserRead(BaseDomainModel):
    tenant_id: UUID
    user_id: UUID
    role: str
    created_at: datetime


class BillingWebhookPayload(BaseDomainModel):
    event_type: str = Field(default="subscription.updated")
    tenant_id: UUID
    subscription_tier: str
