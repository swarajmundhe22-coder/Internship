from uuid import UUID

from app.models.material import MaterialCreate, MaterialRead, MaterialUpdate
from app.models.pagination import MaterialListQuery, PaginatedResponse
from app.repositories.material_repository import MaterialRepository


class MaterialService:
    """Material service that coordinates business logic and repository access."""

    def __init__(self, repository: MaterialRepository) -> None:
        self.repository = repository

    async def create_material(self, payload: MaterialCreate) -> MaterialRead:
        return await self.repository.create(payload)

    async def get_material(self, material_id: UUID) -> MaterialRead:
        return await self.repository.get_by_id(material_id)

    async def list_materials(self, query: MaterialListQuery) -> PaginatedResponse[MaterialRead]:
        return await self.repository.list_paginated(query)

    async def update_material(self, material_id: UUID, payload: MaterialUpdate) -> MaterialRead:
        return await self.repository.update(material_id, payload)

    async def delete_material(self, material_id: UUID) -> None:
        await self.repository.delete(material_id)

