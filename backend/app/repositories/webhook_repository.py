from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import WebhookDeliveryLogEntity, WebhookSubscriptionEntity
from app.models.pagination import PaginatedResponse, PaginationParams


class WebhookRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        user_id: UUID,
        event_type: str,
        target_url: str,
        signing_secret: str,
    ) -> WebhookSubscriptionEntity:
        entity = WebhookSubscriptionEntity(
            user_id=user_id,
            event_type=event_type,
            target_url=target_url,
            signing_secret=signing_secret,
        )
        self.session.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        return entity

    async def list_for_user(self, user_id: UUID) -> list[WebhookSubscriptionEntity]:
        statement = (
            select(WebhookSubscriptionEntity)
            .where(WebhookSubscriptionEntity.user_id == user_id)
            .order_by(WebhookSubscriptionEntity.created_at.desc())
        )
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def list_active_by_event(self, event_type: str) -> list[WebhookSubscriptionEntity]:
        statement = select(WebhookSubscriptionEntity).where(
            WebhookSubscriptionEntity.event_type == event_type,
            WebhookSubscriptionEntity.is_active.is_(True),
        )
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def deactivate(self, *, user_id: UUID, webhook_id: UUID) -> bool:
        entity = await self.session.get(WebhookSubscriptionEntity, webhook_id)
        if entity is None or entity.user_id != user_id:
            return False
        entity.is_active = False
        await self.session.commit()
        return True

    async def create_delivery_log(
        self,
        *,
        webhook_subscription_id: UUID,
        event_type: str,
        payload_json: str,
        max_attempts: int,
    ) -> WebhookDeliveryLogEntity:
        entity = WebhookDeliveryLogEntity(
            webhook_subscription_id=webhook_subscription_id,
            event_type=event_type,
            payload_json=payload_json,
            max_attempts=max_attempts,
        )
        self.session.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        return entity

    async def update_delivery_log_attempt(
        self,
        *,
        log_id: UUID,
        attempt_count: int,
        success: bool,
        http_status: int | None,
        error_message: str | None,
        first_attempt_at: datetime,
        last_attempt_at: datetime,
        next_retry_at: datetime | None,
        delivered_at: datetime | None,
    ) -> None:
        entity = await self.session.get(WebhookDeliveryLogEntity, log_id)
        if entity is None:
            return
        entity.attempt_count = attempt_count
        entity.success = success
        entity.http_status = http_status
        entity.error_message = error_message
        entity.first_attempt_at = first_attempt_at
        entity.last_attempt_at = last_attempt_at
        entity.next_retry_at = next_retry_at
        entity.delivered_at = delivered_at
        await self.session.commit()

    async def list_delivery_logs_for_user(
        self,
        *,
        user_id: UUID,
        query: PaginationParams,
        webhook_id: UUID | None = None,
        success: bool | None = None,
    ) -> PaginatedResponse[WebhookDeliveryLogEntity]:
        base_statement = (
            select(WebhookDeliveryLogEntity)
            .join(
                WebhookSubscriptionEntity,
                WebhookSubscriptionEntity.id == WebhookDeliveryLogEntity.webhook_subscription_id,
            )
            .where(WebhookSubscriptionEntity.user_id == user_id)
        )
        if webhook_id is not None:
            base_statement = base_statement.where(WebhookDeliveryLogEntity.webhook_subscription_id == webhook_id)
        if success is not None:
            base_statement = base_statement.where(WebhookDeliveryLogEntity.success.is_(success))

        total_result = await self.session.execute(select(func.count()).select_from(base_statement.subquery()))
        total = int(total_result.scalar_one())

        result = await self.session.execute(
            base_statement
            .order_by(WebhookDeliveryLogEntity.created_at.desc())
            .offset((query.page - 1) * query.page_size)
            .limit(query.page_size)
        )
        items = result.scalars().all()
        return PaginatedResponse[WebhookDeliveryLogEntity](
            items=items,
            total=total,
            page=query.page,
            page_size=query.page_size,
        )
