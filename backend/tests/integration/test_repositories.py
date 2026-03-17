from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.environment import EnvironmentCreate, EnvironmentUpdate
from app.models.material import MaterialCreate, MaterialUpdate
from app.models.pagination import EnvironmentListQuery, MaterialListQuery, ReportListQuery, SimulationListQuery
from app.models.report import ReportCreate, ReportUpdate
from app.models.simulation import SimulationCreate, SimulationUpdate
from app.repositories.environment_repository import EnvironmentRepository
from app.repositories.exceptions import ConcurrencyError, EntityNotFoundError
from app.repositories.material_repository import MaterialRepository
from app.repositories.report_repository import ReportRepository
from app.repositories.simulation_repository import SimulationRepository


@pytest.mark.asyncio
async def test_material_repository_crud(db_session: AsyncSession) -> None:
    repository = MaterialRepository(db_session)

    created = await repository.create(
        MaterialCreate(
            name="Pipeline Steel X65",
            alloy_group="Ferrous",
            density_kg_m3=7850.0,
            electrochemical_potential_v=-0.61,
        )
    )
    assert created.name == "Pipeline Steel X65"

    fetched = await repository.get_by_id(created.id)
    assert fetched.id == created.id

    updated = await repository.update(
        created.id,
        MaterialUpdate(electrochemical_potential_v=-0.58),
    )
    assert updated.electrochemical_potential_v == pytest.approx(-0.58)

    all_records = await repository.list_paginated(MaterialListQuery(page=1, page_size=10))
    assert all_records.total == 1
    assert len(all_records.items) == 1

    await repository.delete(created.id)
    with pytest.raises(EntityNotFoundError):
        await repository.get_by_id(created.id)


@pytest.mark.asyncio
async def test_environment_repository_crud(db_session: AsyncSession) -> None:
    repository = EnvironmentRepository(db_session)

    created = await repository.create(
        EnvironmentCreate(
            profile_name="Marine Lab",
            temperature_c=24.0,
            relative_humidity_pct=88.0,
            chloride_ppm=18000.0,
            ph=8.2,
            dissolved_oxygen_mg_l=7.1,
        )
    )
    assert created.profile_name == "Marine Lab"

    fetched = await repository.get_by_id(created.id)
    assert fetched.id == created.id

    updated = await repository.update(
        created.id,
        EnvironmentUpdate(ph=7.8),
    )
    assert updated.ph == pytest.approx(7.8)

    all_records = await repository.list_paginated(EnvironmentListQuery(page=1, page_size=10))
    assert all_records.total == 1
    assert len(all_records.items) == 1

    await repository.delete(created.id)
    with pytest.raises(EntityNotFoundError):
        await repository.get_by_id(created.id)


@pytest.mark.asyncio
async def test_simulation_and_report_repository_crud(db_session: AsyncSession) -> None:
    material_repository = MaterialRepository(db_session)
    environment_repository = EnvironmentRepository(db_session)
    simulation_repository = SimulationRepository(db_session)
    report_repository = ReportRepository(db_session)

    material = await material_repository.create(
        MaterialCreate(
            name="Alloy 625",
            alloy_group="Non-Ferrous",
            density_kg_m3=8440.0,
            electrochemical_potential_v=-0.15,
        )
    )
    environment = await environment_repository.create(
        EnvironmentCreate(
            profile_name="Industrial Wet",
            temperature_c=33.0,
            relative_humidity_pct=75.0,
            chloride_ppm=450.0,
            ph=5.6,
            dissolved_oxygen_mg_l=6.3,
        )
    )

    simulation = await simulation_repository.create(
        SimulationCreate(
            material_id=material.id,
            environment_id=environment.id,
            exposed_area_m2=12.0,
            exposure_time_hours=720.0,
            corrosion_rate_mm_per_year=0.14,
            estimated_lifespan_years=9.5,
            risk_classification="high",
        )
    )
    assert simulation.risk_classification == "high"

    simulation_updated = await simulation_repository.update(
        simulation.id,
        SimulationUpdate(expected_version=simulation.version, risk_classification="moderate"),
    )
    assert simulation_updated.risk_classification == "moderate"
    assert simulation_updated.version == simulation.version + 1

    report = await report_repository.create(
        ReportCreate(
            simulation_id=simulation.id,
            report_uri="s3://on-looker/reports/sample.pdf",
            status="generated",
            version=1,
        )
    )
    assert report.simulation_id == simulation.id

    report_updated = await report_repository.update(
        report.id,
        ReportUpdate(expected_version=report.version, status="archived"),
    )
    assert report_updated.status == "archived"
    assert report_updated.version == report.version + 1

    simulation_page = await simulation_repository.list_paginated(
        SimulationListQuery(page=1, page_size=20, material_id=material.id)
    )
    assert simulation_page.total == 1

    report_page = await report_repository.list_paginated(
        ReportListQuery(page=1, page_size=20, simulation_id=simulation.id)
    )
    assert report_page.total == 1

    await report_repository.delete(report.id)
    with pytest.raises(EntityNotFoundError):
        await report_repository.get_by_id(report.id)

    await simulation_repository.delete(simulation.id)
    with pytest.raises(EntityNotFoundError):
        await simulation_repository.get_by_id(simulation.id)


@pytest.mark.asyncio
async def test_repository_not_found_exceptions(db_session: AsyncSession) -> None:
    repository = ReportRepository(db_session)
    with pytest.raises(EntityNotFoundError):
        await repository.get_by_id(uuid4())


@pytest.mark.asyncio
async def test_optimistic_locking_rejects_stale_version(db_session: AsyncSession) -> None:
    material_repository = MaterialRepository(db_session)
    environment_repository = EnvironmentRepository(db_session)
    simulation_repository = SimulationRepository(db_session)

    material = await material_repository.create(
        MaterialCreate(
            name="Concurrent Material",
            alloy_group="Ferrous",
            density_kg_m3=7850.0,
            electrochemical_potential_v=-0.55,
        )
    )
    environment = await environment_repository.create(
        EnvironmentCreate(
            profile_name="Concurrent Environment",
            temperature_c=28.0,
            relative_humidity_pct=70.0,
            chloride_ppm=200.0,
            ph=6.5,
            dissolved_oxygen_mg_l=6.0,
        )
    )
    simulation = await simulation_repository.create(
        SimulationCreate(
            material_id=material.id,
            environment_id=environment.id,
            exposed_area_m2=8.0,
            exposure_time_hours=300.0,
            corrosion_rate_mm_per_year=0.07,
            estimated_lifespan_years=20.0,
            risk_classification="moderate",
        )
    )

    # First writer updates from version 1 to 2.
    _ = await simulation_repository.update(
        simulation.id,
        SimulationUpdate(expected_version=simulation.version, risk_classification="high"),
    )

    # Second writer still tries with stale version 1 and must fail.
    with pytest.raises(ConcurrencyError):
        await simulation_repository.update(
            simulation.id,
            SimulationUpdate(expected_version=simulation.version, risk_classification="critical"),
        )
