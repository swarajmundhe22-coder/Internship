from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, distinct, func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import (
    ComparisonSetEntity,
    ComparisonSetSimulationEntity,
    ProjectSimulationEntity,
)
from app.repositories.exceptions import ConflictError, EntityNotFoundError, PersistenceError


class ComparisonSetRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        project_id: UUID,
        name: str,
        created_by: UUID,
        simulation_ids: list[UUID],
    ) -> ComparisonSetEntity:
        entity = ComparisonSetEntity(project_id=project_id, name=name, created_by=created_by)
        self.session.add(entity)

        try:
            await self.session.flush()
            for index, simulation_id in enumerate(simulation_ids):
                self.session.add(
                    ComparisonSetSimulationEntity(
                        comparison_set_id=entity.id,
                        simulation_id=simulation_id,
                        ordering=index,
                    )
                )
            await self.session.commit()
            await self.session.refresh(entity)
            return entity
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError(str(exc.orig)) from exc
        except SQLAlchemyError as exc:
            await self.session.rollback()
            raise PersistenceError(str(exc)) from exc

    async def list_by_project(self, project_id: UUID) -> list[dict[str, object]]:
        statement = (
            select(
                ComparisonSetEntity.id,
                ComparisonSetEntity.project_id,
                ComparisonSetEntity.name,
                ComparisonSetEntity.created_by,
                ComparisonSetEntity.created_at,
                func.count(ComparisonSetSimulationEntity.id).label("simulation_count"),
            )
            .outerjoin(
                ComparisonSetSimulationEntity,
                ComparisonSetSimulationEntity.comparison_set_id == ComparisonSetEntity.id,
            )
            .where(ComparisonSetEntity.project_id == project_id)
            .group_by(
                ComparisonSetEntity.id,
                ComparisonSetEntity.project_id,
                ComparisonSetEntity.name,
                ComparisonSetEntity.created_by,
                ComparisonSetEntity.created_at,
            )
            .order_by(ComparisonSetEntity.created_at.desc())
        )
        result = await self.session.execute(statement)
        return [dict(row._mapping) for row in result.all()]

    async def get_by_id(self, comparison_set_id: UUID) -> ComparisonSetEntity | None:
        return await self.session.get(ComparisonSetEntity, comparison_set_id)

    async def get_simulation_ids(self, comparison_set_id: UUID) -> list[UUID]:
        statement = (
            select(ComparisonSetSimulationEntity.simulation_id)
            .where(ComparisonSetSimulationEntity.comparison_set_id == comparison_set_id)
            .order_by(ComparisonSetSimulationEntity.ordering.asc())
        )
        result = await self.session.execute(statement)
        return [row[0] for row in result.all()]

    async def update(
        self,
        comparison_set_id: UUID,
        name: str | None,
        simulation_ids: list[UUID] | None,
    ) -> ComparisonSetEntity:
        entity = await self.get_by_id(comparison_set_id)
        if entity is None:
            raise EntityNotFoundError("ComparisonSetEntity", comparison_set_id)

        if name is not None:
            entity.name = name

        try:
            if simulation_ids is not None:
                await self.session.execute(
                    delete(ComparisonSetSimulationEntity).where(
                        ComparisonSetSimulationEntity.comparison_set_id == comparison_set_id
                    )
                )
                for index, simulation_id in enumerate(simulation_ids):
                    self.session.add(
                        ComparisonSetSimulationEntity(
                            comparison_set_id=comparison_set_id,
                            simulation_id=simulation_id,
                            ordering=index,
                        )
                    )

            await self.session.commit()
            await self.session.refresh(entity)
            return entity
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError(str(exc.orig)) from exc
        except SQLAlchemyError as exc:
            await self.session.rollback()
            raise PersistenceError(str(exc)) from exc

    async def delete(self, comparison_set_id: UUID) -> None:
        entity = await self.get_by_id(comparison_set_id)
        if entity is None:
            raise EntityNotFoundError("ComparisonSetEntity", comparison_set_id)

        await self.session.delete(entity)
        try:
            await self.session.commit()
        except SQLAlchemyError as exc:
            await self.session.rollback()
            raise PersistenceError(str(exc)) from exc

    async def count_project_simulation_membership(
        self,
        project_id: UUID,
        simulation_ids: list[UUID],
    ) -> int:
        if not simulation_ids:
            return 0

        statement = (
            select(func.count(distinct(ProjectSimulationEntity.simulation_id)))
            .where(
                ProjectSimulationEntity.project_id == project_id,
                ProjectSimulationEntity.simulation_id.in_(simulation_ids),
            )
        )
        result = await self.session.execute(statement)
        return int(result.scalar_one())
