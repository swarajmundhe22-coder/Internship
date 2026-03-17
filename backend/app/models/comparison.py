from __future__ import annotations

from uuid import UUID

from app.models.common import BaseDomainModel


class SimulationComparisonRequest(BaseDomainModel):
    left_simulation_id: UUID
    right_simulation_id: UUID


class SimulationComparisonResponse(BaseDomainModel):
    left_simulation_id: UUID
    right_simulation_id: UUID
    corrosion_rate_delta_mm_per_year: float
    lifespan_delta_years: float
    risk_transition: str
    environmental_deltas: dict[str, float]
    material_deltas: dict[str, float]
