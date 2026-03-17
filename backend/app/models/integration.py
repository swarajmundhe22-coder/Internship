from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field, HttpUrl

from app.models.common import BaseDomainModel


class ApiTokenCreateRequest(BaseDomainModel):
    name: str = Field(min_length=2, max_length=120)
    scopes: list[str] = Field(default_factory=list)
    expires_in_days: int | None = Field(default=None, ge=1, le=365)


class ApiTokenCreateResponse(BaseDomainModel):
    id: UUID
    token: str
    token_prefix: str
    name: str
    scopes: list[str]
    expires_at: datetime | None = None
    created_at: datetime


class ApiTokenRead(BaseDomainModel):
    id: UUID
    token_prefix: str
    name: str
    scopes: list[str]
    is_active: bool
    expires_at: datetime | None = None
    created_at: datetime
    revoked_at: datetime | None = None


class WebhookCreateRequest(BaseDomainModel):
    event_type: str = Field(default="report.completed", min_length=3, max_length=80)
    target_url: HttpUrl


class WebhookRead(BaseDomainModel):
    id: UUID
    event_type: str
    target_url: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class WebhookDeliveryLogRead(BaseDomainModel):
    id: UUID
    webhook_subscription_id: UUID
    event_type: str
    attempt_count: int
    max_attempts: int
    success: bool
    http_status: int | None = None
    error_message: str | None = None
    first_attempt_at: datetime | None = None
    last_attempt_at: datetime | None = None
    next_retry_at: datetime | None = None
    delivered_at: datetime | None = None
    created_at: datetime


class SsoExchangeRequest(BaseDomainModel):
    provider: str = Field(default="oidc", min_length=2, max_length=50)
    email: str = Field(min_length=5, max_length=255)
    external_subject: str = Field(min_length=3, max_length=255)


class SsoExchangeResponse(BaseDomainModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class OAuthAuthorizeResponse(BaseDomainModel):
    provider: str
    authorization_url: HttpUrl


class OAuthCallbackResult(BaseDomainModel):
    provider: str
    email: str
    external_subject: str
