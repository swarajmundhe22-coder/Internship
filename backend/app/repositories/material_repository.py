from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import MaterialEntity
from app.models.material import MaterialCreate, MaterialRead, MaterialUpdate
from app.models.pagination import MaterialListQuery, PaginatedResponse
from app.repositories.base import BaseRepository
from app.repositories.exceptions import EntityNotFoundError
from app.repositories.query_specs import apply_created_range_filters


class MaterialRepository(
    BaseRepository[MaterialEntity, MaterialCreate, MaterialUpdate, MaterialRead]
):
    """Persistence boundary for material profile CRUD operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session, entity_type=MaterialEntity, read_schema=MaterialRead)

    async def create(self, payload: MaterialCreate) -> MaterialRead:
        entity = MaterialEntity(**self._payload_dict(payload))
        self.session.add(entity)
        await self._flush_refresh(entity)
        await self._commit_or_rollback()
        return self._entity_to_read_model(entity, self.read_schema)

    async def get_by_id(self, material_id: UUID) -> MaterialRead:
        entity = await self.session.get(self.entity_type, material_id)
        if entity is None:
            raise EntityNotFoundError("MaterialEntity", material_id)
        return self._entity_to_read_model(entity, self.read_schema)

    async def list_all(self) -> list[MaterialRead]:
        statement = select(self.entity_type).order_by(self.entity_type.created_at.desc())
        result = await self.session.execute(statement)
        entities = result.scalars().all()
        return self._entities_to_read_models(entities, self.read_schema)

    async def list_paginated(self, query: MaterialListQuery) -> PaginatedResponse[MaterialRead]:
        base_statement = apply_created_range_filters(
            select(self.entity_type),
            self.entity_type,
            query.created_from,
            query.created_to,
        )

        count_statement = select(func.count()).select_from(base_statement.subquery())
        total_result = await self.session.execute(count_statement)
        total = int(total_result.scalar_one())

        paged_statement = (
            base_statement.order_by(self.entity_type.created_at.desc())
            .offset((query.page - 1) * query.page_size)
            .limit(query.page_size)
        )
        page_result = await self.session.execute(paged_statement)
        entities = page_result.scalars().all()

        return PaginatedResponse[MaterialRead](
            items=self._entities_to_read_models(entities, self.read_schema),
            total=total,
            page=query.page,
            page_size=query.page_size,
        )

    async def update(self, material_id: UUID, payload: MaterialUpdate) -> MaterialRead:
        entity = await self.session.get(self.entity_type, material_id)
        if entity is None:
            raise EntityNotFoundError("MaterialEntity", material_id)

        for field, value in self._payload_dict(payload).items():
            setattr(entity, field, value)

        await self._flush_refresh(entity)
        await self._commit_or_rollback()
        return self._entity_to_read_model(entity, self.read_schema)

    async def delete(self, material_id: UUID) -> None:
        entity = await self.session.get(self.entity_type, material_id)
        if entity is None:
            raise EntityNotFoundError("MaterialEntity", material_id)

        await self.session.delete(entity)
        await self._commit_or_rollback()
