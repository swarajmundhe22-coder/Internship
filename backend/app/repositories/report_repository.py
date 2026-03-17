from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import ReportEntity
from app.models.pagination import PaginatedResponse, ReportListQuery
from app.models.report import ReportCreate, ReportRecordRead, ReportUpdate
from app.repositories.base import BaseRepository
from app.repositories.exceptions import ConcurrencyError, EntityNotFoundError
from app.repositories.query_specs import apply_generated_range_filters


class ReportRepository(
    BaseRepository[ReportEntity, ReportCreate, ReportUpdate, ReportRecordRead]
):
    """Persistence boundary for report metadata CRUD operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session, entity_type=ReportEntity, read_schema=ReportRecordRead)

    async def create(self, payload: ReportCreate) -> ReportRecordRead:
        entity = ReportEntity(**self._payload_dict(payload))
        self.session.add(entity)
        await self._flush_refresh(entity)
        await self._commit_or_rollback()
        return self._entity_to_read_model(entity, self.read_schema)

    async def get_by_id(self, report_id: UUID) -> ReportRecordRead:
        entity = await self.session.get(self.entity_type, report_id)
        if entity is None:
            raise EntityNotFoundError("ReportEntity", report_id)
        return self._entity_to_read_model(entity, self.read_schema)

    async def list_all(self) -> list[ReportRecordRead]:
        statement = select(self.entity_type).order_by(self.entity_type.generated_at.desc())
        result = await self.session.execute(statement)
        entities = result.scalars().all()
        return self._entities_to_read_models(entities, self.read_schema)

    async def list_paginated(self, query: ReportListQuery) -> PaginatedResponse[ReportRecordRead]:
        base_statement = apply_generated_range_filters(
            select(self.entity_type),
            self.entity_type,
            query.created_from,
            query.created_to,
        )
        if query.simulation_id is not None:
            base_statement = base_statement.where(self.entity_type.simulation_id == query.simulation_id)

        count_statement = select(func.count()).select_from(base_statement.subquery())
        total_result = await self.session.execute(count_statement)
        total = int(total_result.scalar_one())

        paged_statement = (
            base_statement.order_by(self.entity_type.generated_at.desc())
            .offset((query.page - 1) * query.page_size)
            .limit(query.page_size)
        )
        page_result = await self.session.execute(paged_statement)
        entities = page_result.scalars().all()

        return PaginatedResponse[ReportRecordRead](
            items=self._entities_to_read_models(entities, self.read_schema),
            total=total,
            page=query.page,
            page_size=query.page_size,
        )

    async def update(self, report_id: UUID, payload: ReportUpdate) -> ReportRecordRead:
        entity = await self.session.get(self.entity_type, report_id)
        if entity is None:
            raise EntityNotFoundError("ReportEntity", report_id)

        update_payload = self._payload_dict(payload)
        expected_version = int(update_payload.pop("expected_version"))

        update_payload["version"] = expected_version + 1
        statement = (
            update(self.entity_type)
            .where(self.entity_type.id == report_id, self.entity_type.version == expected_version)
            .values(**update_payload)
        )
        result = await self.session.execute(statement)
        if result.rowcount == 0:
            await self.session.rollback()
            raise ConcurrencyError(
                "Report update conflict: expected version does not match current row version"
            )

        await self._commit_or_rollback()
        entity = await self.session.get(self.entity_type, report_id)
        if entity is None:
            raise EntityNotFoundError("ReportEntity", report_id)
        return self._entity_to_read_model(entity, self.read_schema)

    async def delete(self, report_id: UUID) -> None:
        entity = await self.session.get(self.entity_type, report_id)
        if entity is None:
            raise EntityNotFoundError("ReportEntity", report_id)
        await self.session.delete(entity)
        await self._commit_or_rollback()
