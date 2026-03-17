from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import AuditLogEntity
from app.models.audit import AuditLogRead
from app.models.pagination import AuditLogListQuery, PaginatedResponse


class AuditLogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        event_type: str,
        success: bool,
        tenant_id: UUID | None = None,
        user_id: UUID | None = None,
        user_email: str | None = None,
        detail: str | None = None,
    ) -> AuditLogEntity:
        entity = AuditLogEntity(
            event_type=event_type,
            success=success,
            tenant_id=tenant_id,
            user_id=user_id,
            user_email=user_email,
            detail=detail,
        )
        self.session.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        return entity

    async def list_events(
        self,
        *,
        event_type: str | None = None,
        since: datetime | None = None,
    ) -> list[AuditLogEntity]:
        statement = select(AuditLogEntity).order_by(AuditLogEntity.created_at.desc())
        if event_type:
            statement = statement.where(AuditLogEntity.event_type == event_type)
        if since:
            statement = statement.where(AuditLogEntity.created_at >= since)
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def list_paginated(self, query: AuditLogListQuery) -> PaginatedResponse[AuditLogRead]:
        statement = select(AuditLogEntity)
        if query.event_type:
            statement = statement.where(AuditLogEntity.event_type == query.event_type)
        if query.tenant_id:
            statement = statement.where(AuditLogEntity.tenant_id == query.tenant_id)
        if query.user_id:
            statement = statement.where(AuditLogEntity.user_id == query.user_id)
        if query.user_email:
            statement = statement.where(AuditLogEntity.user_email == query.user_email)
        if query.created_from:
            statement = statement.where(AuditLogEntity.created_at >= query.created_from)
        if query.created_to:
            statement = statement.where(AuditLogEntity.created_at <= query.created_to)

        count_statement = select(func.count()).select_from(statement.subquery())
        total_result = await self.session.execute(count_statement)
        total = int(total_result.scalar_one())

        page_statement = (
            statement
            .order_by(AuditLogEntity.created_at.desc())
            .offset((query.page - 1) * query.page_size)
            .limit(query.page_size)
        )
        rows = (await self.session.execute(page_statement)).scalars().all()

        return PaginatedResponse[AuditLogRead](
            items=[
                AuditLogRead(
                    id=row.id,
                    event_type=row.event_type,
                    tenant_id=row.tenant_id,
                    user_id=row.user_id,
                    user_email=row.user_email,
                    success=row.success,
                    detail=row.detail,
                    created_at=row.created_at,
                )
                for row in rows
            ],
            total=total,
            page=query.page,
            page_size=query.page_size,
        )
