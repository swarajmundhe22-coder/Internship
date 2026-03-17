from uuid import UUID

from app.models.pagination import PaginatedResponse, SimulationListQuery
from app.models.simulation import SimulationCreate, SimulationRead, SimulationUpdate
from app.repositories.simulation_repository import SimulationRepository
from app.repositories.tenant_repository import TenantRepository
from app.repositories.visualization_repository import VisualizationRepository
from app.services.visualization_service import VisualizationService


class SimulationRecordService:
    """Simulation record service for persistence-oriented operations."""

    def __init__(
        self,
        repository: SimulationRepository,
        tenant_repository: TenantRepository | None = None,
        visualization_repository: VisualizationRepository | None = None,
    ) -> None:
        self.repository = repository
        self.tenant_repository = tenant_repository
        self.visualization_repository = visualization_repository

    async def create_simulation(self, payload: SimulationCreate, user_id: UUID | None = None) -> SimulationRead:
        simulation = await self.repository.create(payload)
        tenant_id = None
        if self.tenant_repository is not None and user_id is not None:
            tenant = await self.tenant_repository.get_primary_tenant_for_user(user_id=user_id)
            if tenant is not None:
                tenant_id = tenant.id
                await self.tenant_repository.bind_simulation_to_tenant(
                    tenant_id=tenant.id,
                    simulation_id=simulation.id,
                )

        if self.visualization_repository is not None:
            visualization_service = VisualizationService(repository=self.visualization_repository)
            await visualization_service.auto_generate_twin(simulation_id=simulation.id, tenant_id=tenant_id)
        return simulation

    async def get_simulation(self, simulation_id: UUID) -> SimulationRead:
        return await self.repository.get_by_id(simulation_id)

    async def list_simulations(
        self,
        query: SimulationListQuery,
    ) -> PaginatedResponse[SimulationRead]:
        return await self.repository.list_paginated(query)

    async def update_simulation(
        self,
        simulation_id: UUID,
        payload: SimulationUpdate,
    ) -> SimulationRead:
        return await self.repository.update(simulation_id, payload)

    async def delete_simulation(self, simulation_id: UUID) -> None:
        await self.repository.delete(simulation_id)
