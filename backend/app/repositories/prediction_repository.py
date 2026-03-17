from __future__ import annotations

import json
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import ProjectPredictionEntity
from app.models.pagination import PaginatedResponse, ProjectPredictionListQuery
from app.models.prediction import PredictionTimelinePoint, ProjectPredictionRead
from app.repositories.query_specs import apply_created_range_filters


class PredictionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_prediction(
        self,
        *,
        project_id: UUID,
        simulation_id: UUID | None,
        model_name: str,
        horizon_hours: int,
        step_hours: int,
        summary: str,
        timeline: list[PredictionTimelinePoint],
    ) -> ProjectPredictionRead:
        timeline_payload = [point.model_dump() for point in timeline]
        entity = ProjectPredictionEntity(
            project_id=project_id,
            simulation_id=simulation_id,
            model_name=model_name,
            horizon_hours=horizon_hours,
            step_hours=step_hours,
            summary=summary,
            timeline_json=json.dumps(timeline_payload),
        )
        self.session.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        return self._to_read_model(entity)

    async def list_predictions(
        self,
        *,
        project_id: UUID,
        query: ProjectPredictionListQuery,
    ) -> PaginatedResponse[ProjectPredictionRead]:
        base_statement = select(ProjectPredictionEntity).where(ProjectPredictionEntity.project_id == project_id)
        base_statement = apply_created_range_filters(
            base_statement,
            ProjectPredictionEntity,
            query.created_from,
            query.created_to,
        )

        if query.simulation_id is not None:
            base_statement = base_statement.where(ProjectPredictionEntity.simulation_id == query.simulation_id)

        count_statement = select(func.count()).select_from(base_statement.subquery())
        total_result = await self.session.execute(count_statement)
        total = int(total_result.scalar_one())

        page_statement = (
            base_statement.order_by(ProjectPredictionEntity.created_at.desc())
            .offset((query.page - 1) * query.page_size)
            .limit(query.page_size)
        )
        page_result = await self.session.execute(page_statement)
        entities = page_result.scalars().all()

        return PaginatedResponse[ProjectPredictionRead](
            items=[self._to_read_model(entity) for entity in entities],
            total=total,
            page=query.page,
            page_size=query.page_size,
        )

    def _to_read_model(self, entity: ProjectPredictionEntity) -> ProjectPredictionRead:
        timeline_payload = json.loads(entity.timeline_json)
        timeline = [PredictionTimelinePoint.model_validate(item) for item in timeline_payload]
        return ProjectPredictionRead(
            id=entity.id,
            project_id=entity.project_id,
            simulation_id=entity.simulation_id,
            model_name=entity.model_name,
            horizon_hours=entity.horizon_hours,
            step_hours=entity.step_hours,
            summary=entity.summary,
            timeline=timeline,
            created_at=entity.created_at,
        )
