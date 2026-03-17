from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import SimulationEntity
from app.models.simulation import SimulationCreate, SimulationRead, SimulationUpdate
from app.models.pagination import PaginatedResponse, SimulationListQuery
from app.repositories.base import BaseRepository
from app.repositories.exceptions import ConcurrencyError, EntityNotFoundError
from app.repositories.query_specs import apply_created_range_filters


class SimulationRepository(
    BaseRepository[SimulationEntity, SimulationCreate, SimulationUpdate, SimulationRead]
):
    """Persistence boundary for simulation record CRUD operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session=session, entity_type=SimulationEntity, read_schema=SimulationRead)

    async def create(self, payload: SimulationCreate) -> SimulationRead:
        entity = SimulationEntity(**self._payload_dict(payload))
        self.session.add(entity)
        await self._flush_refresh(entity)
        await self._commit_or_rollback()
        return self._entity_to_read_model(entity, self.read_schema)

    async def get_by_id(self, simulation_id: UUID) -> SimulationRead:
        entity = await self.session.get(self.entity_type, simulation_id)
        if entity is None:
            raise EntityNotFoundError("SimulationEntity", simulation_id)
        return self._entity_to_read_model(entity, self.read_schema)

    async def list_all(self) -> list[SimulationRead]:
        statement = select(self.entity_type).order_by(self.entity_type.created_at.desc())
        result = await self.session.execute(statement)
        entities = result.scalars().all()
        return self._entities_to_read_models(entities, self.read_schema)

    async def list_paginated(self, query: SimulationListQuery) -> PaginatedResponse[SimulationRead]:
        base_statement = select(self.entity_type)
        base_statement = apply_created_range_filters(
            base_statement,
            self.entity_type,
            query.created_from,
            query.created_to,
        )

        if query.material_id is not None:
            base_statement = base_statement.where(self.entity_type.material_id == query.material_id)
        if query.environment_id is not None:
            base_statement = base_statement.where(self.entity_type.environment_id == query.environment_id)
        if query.risk_level is not None:
            base_statement = base_statement.where(self.entity_type.risk_classification == query.risk_level)

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

        return PaginatedResponse[SimulationRead](
            items=self._entities_to_read_models(entities, self.read_schema),
            total=total,
            page=query.page,
            page_size=query.page_size,
        )

    async def update(self, simulation_id: UUID, payload: SimulationUpdate) -> SimulationRead:
        entity = await self.session.get(self.entity_type, simulation_id)
        if entity is None:
            raise EntityNotFoundError("SimulationEntity", simulation_id)

        update_payload = self._payload_dict(payload)
        expected_version = int(update_payload.pop("expected_version"))

        update_payload["version"] = expected_version + 1
        statement = (
            update(self.entity_type)
            .where(self.entity_type.id == simulation_id, self.entity_type.version == expected_version)
            .values(**update_payload)
        )
        result = await self.session.execute(statement)
        if result.rowcount == 0:
            await self.session.rollback()
            raise ConcurrencyError(
                "Simulation update conflict: expected version does not match current row version"
            )

        await self._commit_or_rollback()
        entity = await self.session.get(self.entity_type, simulation_id)
        if entity is None:
            raise EntityNotFoundError("SimulationEntity", simulation_id)
        return self._entity_to_read_model(entity, self.read_schema)

    async def delete(self, simulation_id: UUID) -> None:
        entity = await self.session.get(self.entity_type, simulation_id)
        if entity is None:
            raise EntityNotFoundError("SimulationEntity", simulation_id)
        await self.session.delete(entity)
        await self._commit_or_rollback()
