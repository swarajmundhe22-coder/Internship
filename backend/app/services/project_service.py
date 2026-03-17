from __future__ import annotations

import json
from uuid import UUID

from app.models.project import (
    ProjectDetailResponse,
    ProjectRead,
    ProjectReportSummary,
    ProjectSimulationSummary,
)
from app.models.pagination import PaginatedResponse, ProjectReportListQuery, ProjectSimulationListQuery
from app.repositories.project_repository import ProjectRepository
from app.repositories.tenant_repository import TenantRepository


class ProjectService:
    def __init__(self, repository: ProjectRepository, tenant_repository: TenantRepository | None = None) -> None:
        self.repository = repository
        self.tenant_repository = tenant_repository

    async def list_projects(self, user_id: UUID) -> list[ProjectRead]:
        projects = await self.repository.list_by_user(user_id)
        return [self._to_project_read(project) for project in projects]

    async def create_project(
        self,
        user_id: UUID,
        name: str,
        metadata: dict[str, object] | None = None,
    ) -> ProjectRead:
        tenant_id = None
        if self.tenant_repository is not None:
            tenant = await self.tenant_repository.get_primary_tenant_for_user(user_id=user_id)
            tenant_id = tenant.id if tenant is not None else None

        project = await self.repository.create(
            user_id=user_id,
            name=name,
            tenant_id=tenant_id,
            metadata=metadata,
        )
        return self._to_project_read(project)

    async def get_project_detail(
        self,
        user_id: UUID,
        project_id: UUID,
        query: ProjectSimulationListQuery,
    ) -> ProjectDetailResponse:
        project = await self.repository.get_by_id_for_user(project_id=project_id, user_id=user_id)
        if project is None:
            raise ValueError("Project not found")

        simulation_rows, total = await self.repository.list_project_simulation_summaries(
            project_id=project_id,
            query=query,
        )
        simulations = [ProjectSimulationSummary.model_validate(item) for item in simulation_rows]
        return ProjectDetailResponse(
            id=project.id,
            name=project.name,
            created_at=project.created_at,
            simulations=PaginatedResponse[ProjectSimulationSummary](
                items=simulations,
                total=total,
                page=query.page,
                page_size=query.page_size,
            ),
        )

    async def save_simulation(self, project_id: UUID, simulation_id: UUID) -> None:
        await self.repository.add_simulation(project_id=project_id, simulation_id=simulation_id)

    async def list_project_reports(
        self,
        user_id: UUID,
        project_id: UUID,
        query: ProjectReportListQuery,
    ) -> PaginatedResponse[ProjectReportSummary]:
        project = await self.repository.get_by_id_for_user(project_id=project_id, user_id=user_id)
        if project is None:
            raise ValueError("Project not found")

        report_rows, total = await self.repository.list_project_report_summaries(
            project_id=project_id,
            query=query,
        )
        items = [ProjectReportSummary.model_validate(item) for item in report_rows]
        return PaginatedResponse[ProjectReportSummary](
            items=items,
            total=total,
            page=query.page,
            page_size=query.page_size,
        )

    @staticmethod
    def _to_project_read(project: object) -> ProjectRead:
        metadata_payload: dict[str, object] = {}
        raw_metadata = getattr(project, "metadata_json", "{}")
        if isinstance(raw_metadata, str) and raw_metadata:
            try:
                parsed = json.loads(raw_metadata)
                if isinstance(parsed, dict):
                    metadata_payload = parsed
            except json.JSONDecodeError:
                metadata_payload = {}

        return ProjectRead(
            id=getattr(project, "id"),
            user_id=getattr(project, "user_id"),
            name=getattr(project, "name"),
            metadata=metadata_payload,
            created_at=getattr(project, "created_at"),
            updated_at=getattr(project, "updated_at"),
        )
