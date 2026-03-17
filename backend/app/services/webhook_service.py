from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
import secrets
from uuid import UUID

import httpx

from app.core.config import get_settings
from app.models.integration import WebhookCreateRequest, WebhookRead
from app.models.pagination import PaginatedResponse, PaginationParams
from app.repositories.webhook_repository import WebhookRepository
from app.models.integration import WebhookDeliveryLogRead


class WebhookService:
    def __init__(self, repository: WebhookRepository) -> None:
        self.repository = repository
        self.settings = get_settings()

    async def create_webhook(self, *, user_id: UUID, payload: WebhookCreateRequest) -> WebhookRead:
        entity = await self.repository.create(
            user_id=user_id,
            event_type=payload.event_type,
            target_url=str(payload.target_url),
            signing_secret=secrets.token_urlsafe(24),
        )
        return WebhookRead.model_validate(entity)

    async def list_webhooks(self, *, user_id: UUID) -> list[WebhookRead]:
        entities = await self.repository.list_for_user(user_id)
        return [WebhookRead.model_validate(entity) for entity in entities]

    async def delete_webhook(self, *, user_id: UUID, webhook_id: UUID) -> None:
        if not await self.repository.deactivate(user_id=user_id, webhook_id=webhook_id):
            raise ValueError("Webhook not found")

    async def trigger_event(self, *, event_type: str, payload: dict[str, object]) -> None:
        subscriptions = await self.repository.list_active_by_event(event_type)
        if not subscriptions:
            return

        body = json.dumps(payload).encode("utf-8")
        async with httpx.AsyncClient(timeout=2.0) as client:
            for subscription in subscriptions:
                signature = hmac.new(
                    subscription.signing_secret.encode("utf-8"),
                    body,
                    hashlib.sha256,
                ).hexdigest()
                delivery = await self.repository.create_delivery_log(
                    webhook_subscription_id=subscription.id,
                    event_type=event_type,
                    payload_json=body.decode("utf-8"),
                    max_attempts=self.settings.webhook_retry_attempts,
                )

                first_attempt_at: datetime | None = None
                delivered = False
                for attempt in range(1, self.settings.webhook_retry_attempts + 1):
                    attempted_at = datetime.now(timezone.utc)
                    if first_attempt_at is None:
                        first_attempt_at = attempted_at
                    try:
                        response = await client.post(
                            subscription.target_url,
                            content=body,
                            headers={
                                "Content-Type": "application/json",
                                "X-OnLooker-Event": event_type,
                                "X-OnLooker-Signature": signature,
                            },
                        )
                        ok = 200 <= response.status_code < 300
                        next_retry_at = None
                        if not ok and attempt < self.settings.webhook_retry_attempts:
                            backoff_ms = self.settings.webhook_retry_base_delay_ms * (2 ** (attempt - 1))
                            next_retry_at = attempted_at + timedelta(milliseconds=backoff_ms)

                        await self.repository.update_delivery_log_attempt(
                            log_id=delivery.id,
                            attempt_count=attempt,
                            success=ok,
                            http_status=response.status_code,
                            error_message=None if ok else f"HTTP {response.status_code}",
                            first_attempt_at=first_attempt_at,
                            last_attempt_at=attempted_at,
                            next_retry_at=next_retry_at,
                            delivered_at=attempted_at if ok else None,
                        )

                        if ok:
                            delivered = True
                            break
                    except httpx.HTTPError as exc:
                        next_retry_at = None
                        if attempt < self.settings.webhook_retry_attempts:
                            backoff_ms = self.settings.webhook_retry_base_delay_ms * (2 ** (attempt - 1))
                            next_retry_at = attempted_at + timedelta(milliseconds=backoff_ms)

                        await self.repository.update_delivery_log_attempt(
                            log_id=delivery.id,
                            attempt_count=attempt,
                            success=False,
                            http_status=None,
                            error_message=str(exc),
                            first_attempt_at=first_attempt_at,
                            last_attempt_at=attempted_at,
                            next_retry_at=next_retry_at,
                            delivered_at=None,
                        )

                    if attempt < self.settings.webhook_retry_attempts:
                        delay_seconds = (self.settings.webhook_retry_base_delay_ms * (2 ** (attempt - 1))) / 1000.0
                        await self._sleep(delay_seconds)

                if not delivered:
                    continue

    async def list_delivery_logs(
        self,
        *,
        user_id: UUID,
        page: int,
        page_size: int,
        webhook_id: UUID | None,
        success: bool | None,
    ) -> PaginatedResponse[WebhookDeliveryLogRead]:
        query = PaginationParams(page=page, page_size=page_size)
        result = await self.repository.list_delivery_logs_for_user(
            user_id=user_id,
            query=query,
            webhook_id=webhook_id,
            success=success,
        )
        return PaginatedResponse[WebhookDeliveryLogRead](
            items=[WebhookDeliveryLogRead.model_validate(item) for item in result.items],
            total=result.total,
            page=result.page,
            page_size=result.page_size,
        )

    async def _sleep(self, seconds: float) -> None:
        import asyncio

        await asyncio.sleep(seconds)
