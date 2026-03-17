from uuid import UUID

from app.models.environment import EnvironmentCreate, EnvironmentRead, EnvironmentUpdate
from app.models.pagination import EnvironmentListQuery, PaginatedResponse
from app.repositories.environment_repository import EnvironmentRepository


class EnvironmentService:
    """Environment profile service for persistence-oriented operations."""

    def __init__(self, repository: EnvironmentRepository) -> None:
        self.repository = repository

    async def create_environment(self, payload: EnvironmentCreate) -> EnvironmentRead:
        return await self.repository.create(payload)

    async def get_environment(self, environment_id: UUID) -> EnvironmentRead:
        return await self.repository.get_by_id(environment_id)

    async def list_environments(
        self,
        query: EnvironmentListQuery,
    ) -> PaginatedResponse[EnvironmentRead]:
        return await self.repository.list_paginated(query)

    async def update_environment(
        self,
        environment_id: UUID,
        payload: EnvironmentUpdate,
    ) -> EnvironmentRead:
        return await self.repository.update(environment_id, payload)

    async def delete_environment(self, environment_id: UUID) -> None:
        await self.repository.delete(environment_id)
