from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import EnvironmentEntity, MaterialEntity, SimulationEntity
from app.models.comparison import SimulationComparisonResponse


class ComparisonService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def compare_simulations(
        self,
        left_id: UUID,
        right_id: UUID,
    ) -> SimulationComparisonResponse:
        left = await self._load_joined(left_id)
        right = await self._load_joined(right_id)

        if left is None or right is None:
            raise ValueError("One or both simulations were not found")

        left_simulation, left_material, left_environment = left
        right_simulation, right_material, right_environment = right

        return SimulationComparisonResponse(
            left_simulation_id=left_simulation.id,
            right_simulation_id=right_simulation.id,
            corrosion_rate_delta_mm_per_year=right_simulation.corrosion_rate_mm_per_year - left_simulation.corrosion_rate_mm_per_year,
            lifespan_delta_years=right_simulation.estimated_lifespan_years - left_simulation.estimated_lifespan_years,
            risk_transition=f"{left_simulation.risk_classification} -> {right_simulation.risk_classification}",
            environmental_deltas={
                "temperature_c": right_environment.temperature_c - left_environment.temperature_c,
                "relative_humidity_pct": right_environment.relative_humidity_pct - left_environment.relative_humidity_pct,
                "chloride_ppm": right_environment.chloride_ppm - left_environment.chloride_ppm,
                "ph": right_environment.ph - left_environment.ph,
                "dissolved_oxygen_mg_l": right_environment.dissolved_oxygen_mg_l - left_environment.dissolved_oxygen_mg_l,
            },
            material_deltas={
                "density_kg_m3": right_material.density_kg_m3 - left_material.density_kg_m3,
                "electrochemical_potential_v": right_material.electrochemical_potential_v - left_material.electrochemical_potential_v,
            },
        )

    async def _load_joined(self, simulation_id: UUID):
        statement = (
            select(SimulationEntity, MaterialEntity, EnvironmentEntity)
            .join(MaterialEntity, MaterialEntity.id == SimulationEntity.material_id)
            .join(EnvironmentEntity, EnvironmentEntity.id == SimulationEntity.environment_id)
            .where(SimulationEntity.id == simulation_id)
        )
        result = await self.session.execute(statement)
        return result.first()
