from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.algorithms.microclimate_engine import interpolate_weather_snapshot
from app.algorithms.structural_validation_engine import validate_all_codes
from app.models.infrastructure import (
    CountryCode,
    DesignCodeFamily,
    ExposureCategory,
    InfrastructureLocation,
    InfrastructureValidationRequest,
    MaterialSystem,
    StructuralCapacityInput,
    StructuralLoadCaseInput,
)


@pytest.mark.parametrize("index", list(range(0, 55)))
def test_asce_limit_states_edge_matrix(index: int) -> None:
    request = InfrastructureValidationRequest(
        location=InfrastructureLocation(
            country_code=CountryCode.us,
            state="Florida",
            county="Miami-Dade",
            city="Miami",
            latitude=25.5 + (index % 4) * 0.1,
            longitude=-80.2 + (index % 5) * 0.1,
        ),
        loads=StructuralLoadCaseInput(
            dead_load_kN=400 + index * 8,
            live_load_kN=120 + index * 3,
            snow_load_kN=index % 15,
            thermal_load_kN=20 + (index % 7) * 2,
        ),
        capacities=StructuralCapacityInput(
            ultimate_capacity_kN=1800 + index * 10,
            serviceability_capacity_kN=1400 + index * 8,
            member_area_mm2=18000 + index * 150,
            allowable_stress_mpa=200 + (index % 5) * 10,
        ),
        design_codes=[DesignCodeFamily.asce7_22],
        material_system=MaterialSystem.steel,
        exposure_category=[ExposureCategory.b, ExposureCategory.c, ExposureCategory.d][index % 3],
        structure_height_ft=40 + (index % 10) * 12,
        effective_projected_area_m2=90 + (index % 8) * 10,
        reference_timestamp_utc=datetime.now(timezone.utc),
    )

    weather = interpolate_weather_snapshot(
        location=request.location,
        exposure_category=request.exposure_category,
        structure_height_ft=request.structure_height_ft,
    )
    results = validate_all_codes(request, weather)
    assert len(results) == 1
    asce = results[0]
    assert asce.code_family == DesignCodeFamily.asce7_22
    assert len(asce.limit_states) >= 6
    for state in asce.limit_states:
        assert state.capacity_kN > 0
        assert state.utilization_ratio >= 0


@pytest.mark.parametrize("index", list(range(0, 55)))
def test_eurocode_limit_states_edge_matrix(index: int) -> None:
    request = InfrastructureValidationRequest(
        location=InfrastructureLocation(
            country_code=CountryCode.in_,
            state="Tamil Nadu" if index % 2 == 0 else "Delhi",
            county="Chennai" if index % 2 == 0 else "New Delhi",
            city="Chennai" if index % 2 == 0 else "New Delhi",
            latitude=12.9 + (index % 7) * 0.4,
            longitude=77.0 + (index % 6) * 0.6,
        ),
        loads=StructuralLoadCaseInput(
            dead_load_kN=380 + index * 7,
            live_load_kN=110 + index * 2.5,
            snow_load_kN=index % 6,
            thermal_load_kN=25 + (index % 8) * 2,
        ),
        capacities=StructuralCapacityInput(
            ultimate_capacity_kN=1700 + index * 11,
            serviceability_capacity_kN=1300 + index * 9,
            member_area_mm2=17000 + index * 170,
            allowable_stress_mpa=180 + (index % 6) * 8,
        ),
        design_codes=[DesignCodeFamily.eurocode_in_na],
        material_system=MaterialSystem.concrete if index % 2 == 0 else MaterialSystem.steel,
        exposure_category=[ExposureCategory.b, ExposureCategory.c, ExposureCategory.d][index % 3],
        structure_height_ft=35 + (index % 10) * 10,
        effective_projected_area_m2=80 + (index % 9) * 9,
        reference_timestamp_utc=datetime.now(timezone.utc),
    )

    weather = interpolate_weather_snapshot(
        location=request.location,
        exposure_category=request.exposure_category,
        structure_height_ft=request.structure_height_ft,
    )
    results = validate_all_codes(request, weather)
    assert len(results) == 1
    ec = results[0]
    assert ec.code_family == DesignCodeFamily.eurocode_in_na
    assert len(ec.limit_states) >= 5
    for state in ec.limit_states:
        assert state.capacity_kN > 0
        assert state.utilization_ratio >= 0


@pytest.mark.parametrize("index", list(range(0, 55)))
def test_gb_limit_states_edge_matrix(index: int) -> None:
    request = InfrastructureValidationRequest(
        location=InfrastructureLocation(
            country_code=CountryCode.cn,
            state="Guangdong",
            county="Shenzhen",
            city="Shenzhen",
            latitude=22.5 + (index % 6) * 0.3,
            longitude=113.9 + (index % 6) * 0.35,
        ),
        loads=StructuralLoadCaseInput(
            dead_load_kN=420 + index * 6,
            live_load_kN=105 + index * 2,
            snow_load_kN=index % 8,
            thermal_load_kN=15 + (index % 9) * 1.5,
        ),
        capacities=StructuralCapacityInput(
            ultimate_capacity_kN=1600 + index * 12,
            serviceability_capacity_kN=1200 + index * 10,
            member_area_mm2=16500 + index * 130,
            allowable_stress_mpa=175 + (index % 7) * 9,
        ),
        design_codes=[DesignCodeFamily.gb_500],
        material_system=MaterialSystem.steel,
        exposure_category=[ExposureCategory.b, ExposureCategory.c, ExposureCategory.d][index % 3],
        structure_height_ft=30 + (index % 10) * 14,
        effective_projected_area_m2=100 + (index % 11) * 8,
        reference_timestamp_utc=datetime.now(timezone.utc),
    )

    weather = interpolate_weather_snapshot(
        location=request.location,
        exposure_category=request.exposure_category,
        structure_height_ft=request.structure_height_ft,
    )
    results = validate_all_codes(request, weather)
    assert len(results) == 1
    gb = results[0]
    assert gb.code_family == DesignCodeFamily.gb_500
    assert len(gb.limit_states) >= 5
    for state in gb.limit_states:
        assert state.capacity_kN > 0
        assert state.utilization_ratio >= 0
