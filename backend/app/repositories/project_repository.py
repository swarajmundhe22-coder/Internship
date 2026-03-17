from __future__ import annotations

import json
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import (
    EnvironmentEntity,
    MaterialEntity,
    ProjectEntity,
    ProjectSimulationEntity,
    ReportEntity,
    SimulationEntity,
)
from app.models.pagination import ProjectReportListQuery, ProjectSimulationListQuery
from app.repositories.query_specs import apply_created_range_filters, apply_generated_range_filters


class ProjectRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_by_user(self, user_id: UUID) -> list[ProjectEntity]:
        statement = select(ProjectEntity).where(ProjectEntity.user_id == user_id).order_by(ProjectEntity.created_at.desc())
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def create(
        self,
        user_id: UUID,
        name: str,
        tenant_id: UUID | None = None,
        metadata: dict[str, object] | None = None,
    ) -> ProjectEntity:
        project = ProjectEntity(
            user_id=user_id,
            name=name,
            tenant_id=tenant_id,
            metadata_json=json.dumps(metadata or {}, separators=(",", ":"), sort_keys=True),
        )
        self.session.add(project)
        await self.session.commit()
        await self.session.refresh(project)
        return project

    async def get_by_id_for_user(self, project_id: UUID, user_id: UUID) -> ProjectEntity | None:
        statement = select(ProjectEntity).where(
            ProjectEntity.id == project_id,
            ProjectEntity.user_id == user_id,
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list_project_simulation_summaries(
        self,
        project_id: UUID,
        query: ProjectSimulationListQuery,
    ) -> tuple[list[dict[str, object]], int]:
        # The join table preserves many-to-many ownership between projects and existing simulations.
        base_statement = (
            select(
                SimulationEntity.id.label("simulation_id"),
                MaterialEntity.name.label("material"),
                EnvironmentEntity.profile_name.label("environment"),
                SimulationEntity.risk_classification.label("risk_level"),
                SimulationEntity.estimated_lifespan_years.label("lifespan_years"),
                SimulationEntity.created_at.label("created_at"),
            )
            .join(ProjectSimulationEntity, ProjectSimulationEntity.simulation_id == SimulationEntity.id)
            .join(MaterialEntity, MaterialEntity.id == SimulationEntity.material_id)
            .join(EnvironmentEntity, EnvironmentEntity.id == SimulationEntity.environment_id)
            .where(ProjectSimulationEntity.project_id == project_id)
        )

        base_statement = apply_created_range_filters(
            base_statement,
            SimulationEntity,
            query.created_from,
            query.created_to,
        )

        if query.material_id is not None:
            base_statement = base_statement.where(SimulationEntity.material_id == query.material_id)
        if query.environment_id is not None:
            base_statement = base_statement.where(SimulationEntity.environment_id == query.environment_id)
        if query.risk_level is not None:
            base_statement = base_statement.where(SimulationEntity.risk_classification == query.risk_level)

        count_statement = select(func.count()).select_from(base_statement.subquery())
        total_result = await self.session.execute(count_statement)
        total = int(total_result.scalar_one())

        page_statement = (
            base_statement.order_by(SimulationEntity.created_at.desc())
            .offset((query.page - 1) * query.page_size)
            .limit(query.page_size)
        )
        result = await self.session.execute(page_statement)
        return [dict(row._mapping) for row in result.all()], total

    async def add_simulation(self, project_id: UUID, simulation_id: UUID) -> ProjectSimulationEntity:
        link = ProjectSimulationEntity(project_id=project_id, simulation_id=simulation_id)
        self.session.add(link)
        await self.session.commit()
        await self.session.refresh(link)
        return link

    async def get_project_simulation(
        self,
        project_id: UUID,
        simulation_id: UUID,
    ) -> SimulationEntity | None:
        statement = (
            select(SimulationEntity)
            .join(ProjectSimulationEntity, ProjectSimulationEntity.simulation_id == SimulationEntity.id)
            .where(
                ProjectSimulationEntity.project_id == project_id,
                ProjectSimulationEntity.simulation_id == simulation_id,
            )
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_latest_project_simulation(self, project_id: UUID) -> SimulationEntity | None:
        statement = (
            select(SimulationEntity)
            .join(ProjectSimulationEntity, ProjectSimulationEntity.simulation_id == SimulationEntity.id)
            .where(ProjectSimulationEntity.project_id == project_id)
            .order_by(ProjectSimulationEntity.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list_project_report_summaries(
        self,
        project_id: UUID,
        query: ProjectReportListQuery,
    ) -> tuple[list[dict[str, object]], int]:
        base_statement = (
            select(
                ReportEntity.id.label("report_id"),
                ReportEntity.report_uri.label("report_uri"),
                SimulationEntity.id.label("simulation_id"),
                MaterialEntity.name.label("material"),
                EnvironmentEntity.profile_name.label("environment"),
                SimulationEntity.risk_classification.label("simulation_risk_level"),
                SimulationEntity.risk_classification.label("risk_level"),
                SimulationEntity.estimated_lifespan_years.label("lifespan_years"),
                ReportEntity.generated_at.label("created_at"),
            )
            .join(SimulationEntity, SimulationEntity.id == ReportEntity.simulation_id)
            .join(ProjectSimulationEntity, ProjectSimulationEntity.simulation_id == SimulationEntity.id)
            .join(MaterialEntity, MaterialEntity.id == SimulationEntity.material_id)
            .join(EnvironmentEntity, EnvironmentEntity.id == SimulationEntity.environment_id)
            .where(ProjectSimulationEntity.project_id == project_id)
        )

        base_statement = apply_generated_range_filters(
            base_statement,
            ReportEntity,
            query.created_from,
            query.created_to,
        )

        if query.simulation_id is not None:
            base_statement = base_statement.where(SimulationEntity.id == query.simulation_id)
        if query.risk_level is not None:
            base_statement = base_statement.where(SimulationEntity.risk_classification == query.risk_level)

        count_statement = select(func.count()).select_from(base_statement.subquery())
        total_result = await self.session.execute(count_statement)
        total = int(total_result.scalar_one())

        page_statement = (
            base_statement.order_by(ReportEntity.generated_at.desc())
            .offset((query.page - 1) * query.page_size)
            .limit(query.page_size)
        )
        result = await self.session.execute(page_statement)
        return [dict(row._mapping) for row in result.all()], total
