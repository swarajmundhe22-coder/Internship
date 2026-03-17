from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import EnvironmentEntity, MaterialEntity


BASELINE_MATERIALS: list[dict[str, object]] = [
    {
        "name": "Carbon Steel",
        "alloy_group": "Ferrous",
        "density_kg_m3": 7850.0,
        # Representative potential for common steel in neutral aerated environments.
        "electrochemical_potential_v": -0.61,
    },
    {
        "name": "Stainless Steel",
        "alloy_group": "Ferrous",
        "density_kg_m3": 8000.0,
        # Passive stainless potential is less negative than carbon steel.
        "electrochemical_potential_v": -0.10,
    },
    {
        "name": "Aluminum",
        "alloy_group": "Non-Ferrous",
        "density_kg_m3": 2700.0,
        "electrochemical_potential_v": -0.76,
    },
    {
        "name": "Copper Alloys",
        "alloy_group": "Non-Ferrous",
        "density_kg_m3": 8940.0,
        "electrochemical_potential_v": 0.34,
    },
]


BASELINE_ENVIRONMENTS: list[dict[str, object]] = [
    {
        "profile_name": "Marine",
        "temperature_c": 22.0,
        "relative_humidity_pct": 88.0,
        "chloride_ppm": 19500.0,
        "ph": 8.1,
        "dissolved_oxygen_mg_l": 7.5,
    },
    {
        "profile_name": "Industrial",
        "temperature_c": 30.0,
        "relative_humidity_pct": 72.0,
        "chloride_ppm": 350.0,
        "ph": 5.2,
        "dissolved_oxygen_mg_l": 6.2,
    },
    {
        "profile_name": "Soil",
        "temperature_c": 18.0,
        "relative_humidity_pct": 65.0,
        "chloride_ppm": 120.0,
        "ph": 6.4,
        "dissolved_oxygen_mg_l": 3.5,
    },
    {
        "profile_name": "Atmospheric",
        "temperature_c": 25.0,
        "relative_humidity_pct": 55.0,
        "chloride_ppm": 30.0,
        "ph": 7.0,
        "dissolved_oxygen_mg_l": 8.0,
    },
]


async def _insert_material_if_missing(session: AsyncSession, payload: dict[str, object]) -> None:
    statement = select(MaterialEntity).where(MaterialEntity.name == payload["name"])
    result = await session.execute(statement)
    if result.scalar_one_or_none() is None:
        session.add(MaterialEntity(**payload))


async def _insert_environment_if_missing(session: AsyncSession, payload: dict[str, object]) -> None:
    statement = select(EnvironmentEntity).where(
        EnvironmentEntity.profile_name == payload["profile_name"]
    )
    result = await session.execute(statement)
    if result.scalar_one_or_none() is None:
        session.add(EnvironmentEntity(**payload))


async def seed_baseline_data(session: AsyncSession) -> None:
    """Idempotent seed loader for baseline GIFIP-aligned material and environment profiles."""
    for material in BASELINE_MATERIALS:
        await _insert_material_if_missing(session, material)

    for environment in BASELINE_ENVIRONMENTS:
        await _insert_environment_if_missing(session, environment)

    await session.commit()
