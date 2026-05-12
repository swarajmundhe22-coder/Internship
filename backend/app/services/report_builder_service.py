from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.algorithms.recommendations import prevention_recommendation
from app.core.config import get_settings
from app.core.readthrough_cache import ReadThroughCache
from app.database.models import EnvironmentEntity, MaterialEntity, SimulationEntity
from app.models.generated_report import ReportGenerateResponse


class ReportBuilderService:
    """Assemble report-ready engineering intelligence payloads from persisted simulation context."""

    _cache = ReadThroughCache[ReportGenerateResponse](namespace="report_builder")

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.settings = get_settings()

    async def build(self, simulation_id: UUID) -> ReportGenerateResponse:
        cache_key = str(simulation_id)
        return await self._cache.get_or_load(
            cache_key=cache_key,
            loader=lambda: self._build_without_cache(simulation_id),
            encode=lambda payload: payload.model_dump_json(),
            decode=ReportGenerateResponse.model_validate_json,
            hard_ttl_seconds=self.settings.redis_readthrough_hard_ttl_seconds,
            refresh_ttl_ms=self.settings.redis_readthrough_refresh_ttl_ms,
        )

    async def _build_without_cache(self, simulation_id: UUID) -> ReportGenerateResponse:
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
        return response.model_copy(deep=True)

    @classmethod
    def clear_cache(cls) -> None:
        cls._cache.clear_local()

    @classmethod
    def cache_snapshot(cls) -> dict[str, object]:
        return cls._cache.snapshot()
