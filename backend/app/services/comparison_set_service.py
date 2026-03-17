from __future__ import annotations

from uuid import UUID

from app.models.comparison_set import (
    ComparisonSetDetailResponse,
    ComparisonSetListItem,
    ComparisonSetUpdateRequest,
)
from app.repositories.comparison_set_repository import ComparisonSetRepository
from app.repositories.exceptions import EntityNotFoundError
from app.repositories.project_repository import ProjectRepository
from app.services.comparison_service import ComparisonService


class ComparisonSetService:
    def __init__(
        self,
        comparison_set_repository: ComparisonSetRepository,
        project_repository: ProjectRepository,
        comparison_service: ComparisonService,
    ) -> None:
        self.comparison_set_repository = comparison_set_repository
        self.project_repository = project_repository
        self.comparison_service = comparison_service

    async def create_set(
        self,
        user_id: UUID,
        project_id: UUID,
        name: str,
        simulation_ids: list[UUID],
    ) -> ComparisonSetDetailResponse:
        await self._ensure_project_owned_by_user(project_id=project_id, user_id=user_id)
        await self._validate_project_simulations(project_id=project_id, simulation_ids=simulation_ids)

        created = await self.comparison_set_repository.create(
            project_id=project_id,
            name=name,
            created_by=user_id,
            simulation_ids=simulation_ids,
        )
        return await self._build_detail_response(created.id)

    async def list_sets(self, user_id: UUID, project_id: UUID) -> list[ComparisonSetListItem]:
        await self._ensure_project_owned_by_user(project_id=project_id, user_id=user_id)
        rows = await self.comparison_set_repository.list_by_project(project_id=project_id)
        return [ComparisonSetListItem.model_validate(row) for row in rows]

    async def get_set(self, user_id: UUID, comparison_set_id: UUID) -> ComparisonSetDetailResponse:
        await self._ensure_set_visible_to_user(comparison_set_id=comparison_set_id, user_id=user_id)
        return await self._build_detail_response(comparison_set_id)

    async def delete_set(self, user_id: UUID, comparison_set_id: UUID) -> None:
        await self._ensure_set_visible_to_user(comparison_set_id=comparison_set_id, user_id=user_id)
        await self.comparison_set_repository.delete(comparison_set_id)

    async def update_set(
        self,
        user_id: UUID,
        comparison_set_id: UUID,
        payload: ComparisonSetUpdateRequest,
    ) -> ComparisonSetDetailResponse:
        entity = await self._ensure_set_visible_to_user(comparison_set_id=comparison_set_id, user_id=user_id)

        if payload.simulation_ids is not None:
            await self._validate_project_simulations(
                project_id=entity.project_id,
                simulation_ids=payload.simulation_ids,
            )

        await self.comparison_set_repository.update(
            comparison_set_id=comparison_set_id,
            name=payload.name,
            simulation_ids=payload.simulation_ids,
        )
        return await self._build_detail_response(comparison_set_id)

    async def _build_detail_response(self, comparison_set_id: UUID) -> ComparisonSetDetailResponse:
        entity = await self.comparison_set_repository.get_by_id(comparison_set_id)
        if entity is None:
            raise EntityNotFoundError("ComparisonSetEntity", comparison_set_id)

        simulation_ids = await self.comparison_set_repository.get_simulation_ids(comparison_set_id)
        if len(simulation_ids) < 2:
            raise ValueError("Comparison set must include at least two simulations")

        anchor = simulation_ids[0]
        comparisons = []
        for candidate in simulation_ids[1:]:
            comparisons.append(
                await self.comparison_service.compare_simulations(left_id=anchor, right_id=candidate)
            )

        return ComparisonSetDetailResponse(
            id=entity.id,
            project_id=entity.project_id,
            name=entity.name,
            created_by=entity.created_by,
            created_at=entity.created_at,
            simulation_ids=simulation_ids,
            comparisons=comparisons,
        )

    async def _ensure_project_owned_by_user(self, project_id: UUID, user_id: UUID) -> None:
        project = await self.project_repository.get_by_id_for_user(project_id=project_id, user_id=user_id)
        if project is None:
            raise ValueError("Project not found")

    async def _ensure_set_visible_to_user(self, comparison_set_id: UUID, user_id: UUID):
        entity = await self.comparison_set_repository.get_by_id(comparison_set_id)
        if entity is None:
            raise EntityNotFoundError("ComparisonSetEntity", comparison_set_id)

        await self._ensure_project_owned_by_user(project_id=entity.project_id, user_id=user_id)
        return entity

    async def _validate_project_simulations(self, project_id: UUID, simulation_ids: list[UUID]) -> None:
        unique_simulation_ids = list(dict.fromkeys(simulation_ids))
        if len(unique_simulation_ids) < 2 or len(unique_simulation_ids) > 4:
            raise ValueError("Comparison sets require between 2 and 4 unique simulations")

        valid_count = await self.comparison_set_repository.count_project_simulation_membership(
            project_id=project_id,
            simulation_ids=unique_simulation_ids,
        )
        if valid_count != len(unique_simulation_ids):
            raise ValueError("All simulations in a comparison set must belong to the project")
