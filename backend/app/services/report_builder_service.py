from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.algorithms.recommendations import prevention_recommendation
from app.core.config import get_settings
from app.database.models import EnvironmentEntity, MaterialEntity, SimulationEntity
from app.models.generated_report import ReportGenerateResponse


class ReportBuilderService:
    """Assemble report-ready engineering intelligence payloads from persisted simulation context."""

    _cache: dict[str, tuple[datetime, ReportGenerateResponse]] = {}

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.settings = get_settings()

    async def build(self, simulation_id: UUID) -> ReportGenerateResponse:
        cache_key = str(simulation_id)
        cached = self._cache.get(cache_key)
        if cached is not None:
            cached_at, payload = cached
            if datetime.now(timezone.utc) - cached_at <= timedelta(seconds=self.settings.report_cache_ttl_seconds):
                return payload.model_copy(deep=True)

        statement = (
            select(SimulationEntity, MaterialEntity, EnvironmentEntity)
            .join(MaterialEntity, MaterialEntity.id == SimulationEntity.material_id)
            .join(EnvironmentEntity, EnvironmentEntity.id == SimulationEntity.environment_id)
            .where(SimulationEntity.id == simulation_id)
        )
        result = await self.session.execute(statement)
        row = result.first()
        if row is None:
            raise ValueError(f"Simulation '{simulation_id}' was not found")

        simulation, material, environment = row
        recommendation = prevention_recommendation(simulation.risk_classification)

        response = ReportGenerateResponse(
            simulation_id=simulation.id,
            material={
                "name": material.name,
                "alloy_group": material.alloy_group,
                "density_kg_m3": material.density_kg_m3,
                "electrochemical_potential_v": material.electrochemical_potential_v,
            },
            environment={
                "profile_name": environment.profile_name,
                "temperature_c": environment.temperature_c,
                "relative_humidity_pct": environment.relative_humidity_pct,
                "chloride_ppm": environment.chloride_ppm,
                "ph": environment.ph,
                "dissolved_oxygen_mg_l": environment.dissolved_oxygen_mg_l,
            },
            metrics={
                "corrosion_rate_mm_per_year": simulation.corrosion_rate_mm_per_year,
                "risk_classification": simulation.risk_classification,
                "estimated_lifespan_years": simulation.estimated_lifespan_years,
            },
            recommendation_summary=recommendation,
            visual_summary={
                "intensity_map": [
                    {"label": "anode_zone", "value": min(simulation.corrosion_rate_mm_per_year * 180, 100)},
                    {"label": "cathode_zone", "value": min(simulation.corrosion_rate_mm_per_year * 120, 100)},
                ]
            },
        )
        self._cache[cache_key] = (datetime.now(timezone.utc), response)
        return response.model_copy(deep=True)

    @classmethod
    def clear_cache(cls) -> None:
        cls._cache.clear()
