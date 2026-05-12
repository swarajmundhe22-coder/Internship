from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.algorithms.microclimate_engine import (
    INDIA_STATION_CATALOG_SIZE,
    STATION_CATALOG,
    US_STATION_CATALOG_SIZE,
    county_mapped_wind_speed_mph,
    height_adjusted_wind_speed_mph,
    interpolate_weather_snapshot,
    out_of_range_parameters,
    tolerance_against_official,
)
from app.models.infrastructure import (
    CountryCode,
    ExposureCategory,
    InfrastructureLocation,
    OfficialStationObservation,
)


def _miami_location() -> InfrastructureLocation:
    return InfrastructureLocation(
        country_code=CountryCode.us,
        state="Florida",
        county="Miami-Dade",
        city="Miami",
        latitude=25.7617,
        longitude=-80.1918,
    )


def _chennai_location() -> InfrastructureLocation:
    return InfrastructureLocation(
        country_code=CountryCode.in_,
        state="Tamil Nadu",
        county="Chennai",
        city="Chennai",
        latitude=13.0827,
        longitude=80.2707,
    )


def test_station_catalog_size_requirements() -> None:
    assert len(STATION_CATALOG[CountryCode.us]) >= US_STATION_CATALOG_SIZE
    assert len(STATION_CATALOG[CountryCode.in_]) >= INDIA_STATION_CATALOG_SIZE


@pytest.mark.parametrize(
    "height_ft,exposure",
    [
        (15.0 + i * 10.0, exposure)
        for i in range(0, 20)
        for exposure in [ExposureCategory.b, ExposureCategory.c, ExposureCategory.d]
    ],
)
def test_height_adjusted_wind_range(height_ft: float, exposure: ExposureCategory) -> None:
    adjusted = height_adjusted_wind_speed_mph(
        120.0,
        exposure_category=exposure,
        structure_height_ft=height_ft,
    )
    assert 0.0 <= adjusted <= 260.0


@pytest.mark.parametrize(
    "state,county,expected",
    [
        ("Florida", "Miami-Dade", 175),
        ("Texas", "Harris", 150),
        ("California", "Los Angeles", 110),
    ],
)
def test_county_override_wind_speed(state: str, county: str, expected: int) -> None:
    location = InfrastructureLocation(
        country_code=CountryCode.us,
        state=state,
        county=county,
        city=county,
        latitude=29.0,
        longitude=-95.0,
    )
    assert county_mapped_wind_speed_mph(location) == expected


@pytest.mark.parametrize("index", list(range(0, 55)))
def test_us_weather_snapshot_edge_matrix(index: int) -> None:
    lat = 24.5 + (index % 11) * 2.1
    lon = -124.0 + (index % 13) * 4.2
    height = 20.0 + (index % 10) * 35.0

    location = InfrastructureLocation(
        country_code=CountryCode.us,
        state="Florida" if index % 2 == 0 else "Texas",
        county="Miami-Dade" if index % 3 == 0 else "Harris",
        city=f"US-City-{index}",
        latitude=lat,
        longitude=lon,
    )
    snapshot = interpolate_weather_snapshot(
        location=location,
        exposure_category=[ExposureCategory.b, ExposureCategory.c, ExposureCategory.d][index % 3],
        structure_height_ft=height,
        reference_timestamp_utc=datetime.now(timezone.utc),
    )

    assert 0 <= snapshot.basic_wind_speed_mph <= 200
    assert 0 <= snapshot.seismic_zone <= 8
    assert 1 <= snapshot.precipitation_intensity_mm_hr <= 1000
    assert 850 <= snapshot.pressure_hpa <= 1100
    assert out_of_range_parameters(snapshot) == []


@pytest.mark.parametrize("index", list(range(0, 55)))
def test_india_weather_snapshot_edge_matrix(index: int) -> None:
    lat = 8.5 + (index % 12) * 2.2
    lon = 68.5 + (index % 10) * 2.9
    height = 20.0 + (index % 9) * 30.0

    location = InfrastructureLocation(
        country_code=CountryCode.in_,
        state="Tamil Nadu" if index % 2 == 0 else "Delhi",
        county="Chennai" if index % 3 == 0 else "New Delhi",
        city="Chennai" if index % 3 == 0 else "New Delhi",
        latitude=lat,
        longitude=lon,
    )
    snapshot = interpolate_weather_snapshot(
        location=location,
        exposure_category=[ExposureCategory.b, ExposureCategory.c, ExposureCategory.d][index % 3],
        structure_height_ft=height,
        reference_timestamp_utc=datetime.now(timezone.utc),
    )

    assert 0 <= snapshot.basic_wind_speed_mph <= 200
    assert 0 <= snapshot.seismic_zone <= 8
    assert 1 <= snapshot.precipitation_intensity_mm_hr <= 1000
    assert 850 <= snapshot.pressure_hpa <= 1100
    assert out_of_range_parameters(snapshot) == []


def test_tolerance_against_official_within_threshold() -> None:
    snapshot = interpolate_weather_snapshot(
        location=_miami_location(),
        exposure_category=ExposureCategory.c,
        structure_height_ft=120.0,
    )
    official = OfficialStationObservation(
        station_id="US-MIA-0001",
        wind_speed_mph=snapshot.basic_wind_speed_mph * 0.99,
        precipitation_intensity_mm_hr=snapshot.precipitation_intensity_mm_hr * 1.01,
        pressure_hpa=snapshot.pressure_hpa * 1.00,
    )
    check = tolerance_against_official(snapshot, official, threshold_pct=5.0)
    assert check.within_tolerance is True
    assert check.max_error_pct <= 5.0


def test_tolerance_against_official_outside_threshold() -> None:
    snapshot = interpolate_weather_snapshot(
        location=_chennai_location(),
        exposure_category=ExposureCategory.c,
        structure_height_ft=120.0,
    )
    official = OfficialStationObservation(
        station_id="IN-MAA-0001",
        wind_speed_mph=max(1.0, snapshot.basic_wind_speed_mph * 0.75),
        precipitation_intensity_mm_hr=max(1.0, snapshot.precipitation_intensity_mm_hr * 0.70),
        pressure_hpa=snapshot.pressure_hpa,
    )
    check = tolerance_against_official(snapshot, official, threshold_pct=5.0)
    assert check.within_tolerance is False
    assert check.max_error_pct > 5.0
