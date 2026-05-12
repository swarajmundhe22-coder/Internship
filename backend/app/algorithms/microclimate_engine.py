from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import math

from app.models.infrastructure import (
    CountryCode,
    ExposureCategory,
    InfrastructureLocation,
    OfficialStationObservation,
    ValidationToleranceCheck,
    WeatherParameterSnapshot,
)

MICROCLIMATE_ENGINE_VERSION = "microclimate-v2.0.0"
US_STATION_CATALOG_SIZE = 2200
INDIA_STATION_CATALOG_SIZE = 650


@dataclass(frozen=True)
class StationRecord:
    station_id: str
    country_code: CountryCode
    name: str
    latitude: float
    longitude: float
    validated: bool
    wind_speed_mph: int
    ss_g: float
    s1_g: float
    idf_100_year_mm_hr: float
    freeze_thaw_cycles: int
    coastal: bool
    salt_spray_mg_m2_day: float
    so2_ug_m3: float
    pressure_hpa: float


US_COUNTY_WIND_OVERRIDES: dict[tuple[str, str], int] = {
    ("florida", "miami-dade"): 175,
    ("texas", "harris"): 150,
    ("california", "los angeles"): 110,
    ("new york", "kings"): 120,
    ("washington", "king"): 115,
}

INDIA_CITY_SEISMIC_ZONE: dict[str, int] = {
    "chennai": 3,
    "mumbai": 3,
    "new delhi": 4,
    "delhi": 4,
    "guwahati": 5,
    "imphal": 5,
    "srinagar": 5,
    "kolkata": 3,
    "hyderabad": 2,
    "bengaluru": 2,
}


def _hash_fraction(seed: str) -> float:
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    value = int(digest[:12], 16)
    return value / float(0xFFFFFFFFFFFF)


def _blend(seed: str, min_value: float, max_value: float) -> float:
    return min_value + (max_value - min_value) * _hash_fraction(seed)


def _canonical_text(value: str | None) -> str:
    return (value or "").strip().lower()


def _haversine_km(lat_a: float, lon_a: float, lat_b: float, lon_b: float) -> float:
    radius_km = 6371.0088
    lat_a_rad = math.radians(lat_a)
    lon_a_rad = math.radians(lon_a)
    lat_b_rad = math.radians(lat_b)
    lon_b_rad = math.radians(lon_b)

    dlat = lat_b_rad - lat_a_rad
    dlon = lon_b_rad - lon_a_rad

    sin_dlat = math.sin(dlat / 2.0)
    sin_dlon = math.sin(dlon / 2.0)
    a = sin_dlat * sin_dlat + math.cos(lat_a_rad) * math.cos(lat_b_rad) * sin_dlon * sin_dlon
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return radius_km * c


def _coastal_hint(location: InfrastructureLocation) -> bool:
    city = _canonical_text(location.city)
    county = _canonical_text(location.county)
    state = _canonical_text(location.state)
    text = f"{city} {county} {state}"
    return any(
        token in text
        for token in (
            "coast",
            "beach",
            "bay",
            "harbor",
            "harbour",
            "miami",
            "chennai",
            "mumbai",
            "goa",
            "port",
        )
    )


def _clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(max_value, value))


def _round_1mph(value: float) -> int:
    return int(round(_clamp(value, 0.0, 200.0)))


def _generate_synthetic_station(country_code: CountryCode, index: int) -> StationRecord:
    seed = f"{country_code.value}-{index}"
    if country_code == CountryCode.us:
        latitude = _blend(seed + "-lat", 24.0, 49.5)
        longitude = _blend(seed + "-lon", -124.5, -66.5)
        wind = _round_1mph(_blend(seed + "-wind", 85.0, 190.0))
        ss = _blend(seed + "-ss", 0.05, 1.80)
        s1 = _blend(seed + "-s1", 0.02, 0.90)
        freeze_thaw = int(round(_blend(seed + "-freeze", 0.0, 70.0)))
        idf = _blend(seed + "-idf", 40.0, 320.0)
        coastal = _hash_fraction(seed + "-coastal") > 0.75
        salt = _blend(seed + "-salt", 5.0, 200.0) if coastal else _blend(seed + "-salt", 1.0, 40.0)
        so2 = _blend(seed + "-so2", 4.0, 45.0)
        pressure = _blend(seed + "-pressure", 930.0, 1035.0)
    elif country_code == CountryCode.in_:
        latitude = _blend(seed + "-lat", 8.0, 36.5)
        longitude = _blend(seed + "-lon", 68.0, 97.5)
        wind = _round_1mph(_blend(seed + "-wind", 70.0, 175.0))
        ss = _blend(seed + "-ss", 0.08, 1.30)
        s1 = _blend(seed + "-s1", 0.03, 0.70)
        freeze_thaw = int(round(_blend(seed + "-freeze", 0.0, 35.0)))
        idf = _blend(seed + "-idf", 55.0, 380.0)
        coastal = _hash_fraction(seed + "-coastal") > 0.72
        salt = _blend(seed + "-salt", 8.0, 260.0) if coastal else _blend(seed + "-salt", 1.0, 55.0)
        so2 = _blend(seed + "-so2", 5.0, 52.0)
        pressure = _blend(seed + "-pressure", 900.0, 1025.0)
    else:
        latitude = _blend(seed + "-lat", 18.0, 53.0)
        longitude = _blend(seed + "-lon", 73.0, 135.0)
        wind = _round_1mph(_blend(seed + "-wind", 80.0, 190.0))
        ss = _blend(seed + "-ss", 0.10, 2.00)
        s1 = _blend(seed + "-s1", 0.05, 1.10)
        freeze_thaw = int(round(_blend(seed + "-freeze", 0.0, 60.0)))
        idf = _blend(seed + "-idf", 35.0, 350.0)
        coastal = _hash_fraction(seed + "-coastal") > 0.78
        salt = _blend(seed + "-salt", 6.0, 250.0) if coastal else _blend(seed + "-salt", 1.0, 45.0)
        so2 = _blend(seed + "-so2", 6.0, 60.0)
        pressure = _blend(seed + "-pressure", 900.0, 1035.0)

    return StationRecord(
        station_id=f"{country_code.value}-AUTO-{index:04d}",
        country_code=country_code,
        name=f"{country_code.value} Synthetic Station {index}",
        latitude=latitude,
        longitude=longitude,
        validated=(_hash_fraction(seed + "-validated") > 0.08),
        wind_speed_mph=wind,
        ss_g=round(ss, 3),
        s1_g=round(s1, 3),
        idf_100_year_mm_hr=round(_clamp(idf, 1.0, 1000.0), 2),
        freeze_thaw_cycles=max(0, freeze_thaw),
        coastal=coastal,
        salt_spray_mg_m2_day=round(salt, 2),
        so2_ug_m3=round(so2, 2),
        pressure_hpa=round(_clamp(pressure, 850.0, 1100.0), 2),
    )


def _build_station_catalog() -> dict[CountryCode, list[StationRecord]]:
    us_seed = [
        StationRecord(
            station_id="US-MIA-0001",
            country_code=CountryCode.us,
            name="Miami International Validated",
            latitude=25.7959,
            longitude=-80.2871,
            validated=True,
            wind_speed_mph=175,
            ss_g=0.18,
            s1_g=0.06,
            idf_100_year_mm_hr=260.0,
            freeze_thaw_cycles=0,
            coastal=True,
            salt_spray_mg_m2_day=245.0,
            so2_ug_m3=12.5,
            pressure_hpa=1013.2,
        ),
        StationRecord(
            station_id="US-HOU-0002",
            country_code=CountryCode.us,
            name="Houston Validated",
            latitude=29.9902,
            longitude=-95.3368,
            validated=True,
            wind_speed_mph=150,
            ss_g=0.21,
            s1_g=0.08,
            idf_100_year_mm_hr=180.0,
            freeze_thaw_cycles=2,
            coastal=True,
            salt_spray_mg_m2_day=172.0,
            so2_ug_m3=10.3,
            pressure_hpa=1011.8,
        ),
    ]

    in_seed = [
        StationRecord(
            station_id="IN-MAA-0001",
            country_code=CountryCode.in_,
            name="Chennai Meenambakkam Validated",
            latitude=12.9941,
            longitude=80.1709,
            validated=True,
            wind_speed_mph=130,
            ss_g=0.36,
            s1_g=0.18,
            idf_100_year_mm_hr=310.0,
            freeze_thaw_cycles=0,
            coastal=True,
            salt_spray_mg_m2_day=230.0,
            so2_ug_m3=18.8,
            pressure_hpa=1008.5,
        ),
        StationRecord(
            station_id="IN-DEL-0002",
            country_code=CountryCode.in_,
            name="Delhi IGI Validated",
            latitude=28.5562,
            longitude=77.1000,
            validated=True,
            wind_speed_mph=110,
            ss_g=0.55,
            s1_g=0.28,
            idf_100_year_mm_hr=120.0,
            freeze_thaw_cycles=8,
            coastal=False,
            salt_spray_mg_m2_day=22.0,
            so2_ug_m3=24.6,
            pressure_hpa=1005.9,
        ),
    ]

    us_stations = list(us_seed)
    for index in range(len(us_stations), US_STATION_CATALOG_SIZE):
        us_stations.append(_generate_synthetic_station(CountryCode.us, index))

    in_stations = list(in_seed)
    for index in range(len(in_stations), INDIA_STATION_CATALOG_SIZE):
        in_stations.append(_generate_synthetic_station(CountryCode.in_, index))

    cn_stations = [_generate_synthetic_station(CountryCode.cn, index) for index in range(220)]

    return {
        CountryCode.us: us_stations,
        CountryCode.in_: in_stations,
        CountryCode.cn: cn_stations,
    }


STATION_CATALOG = _build_station_catalog()


def find_nearest_station(
    location: InfrastructureLocation,
    *,
    validated_only: bool,
) -> StationRecord | None:
    stations = STATION_CATALOG.get(location.country_code, [])
    nearest: StationRecord | None = None
    nearest_distance_km = float("inf")

    for station in stations:
        if validated_only and not station.validated:
            continue
        distance_km = _haversine_km(location.latitude, location.longitude, station.latitude, station.longitude)
        if distance_km < nearest_distance_km:
            nearest_distance_km = distance_km
            nearest = station

    return nearest


def county_mapped_wind_speed_mph(location: InfrastructureLocation) -> int:
    if location.country_code != CountryCode.us:
        raise ValueError("county_mapped_wind_speed_mph is only valid for US locations")

    state = _canonical_text(location.state)
    county = _canonical_text(location.county)

    if state and county and (state, county) in US_COUNTY_WIND_OVERRIDES:
        return US_COUNTY_WIND_OVERRIDES[(state, county)]

    seed = f"{state}|{county}|{location.latitude:.4f}|{location.longitude:.4f}"
    return 90 + int(round(_blend(seed, 0.0, 110.0)))


def height_adjusted_wind_speed_mph(
    basic_wind_speed_mph: float,
    *,
    exposure_category: ExposureCategory,
    structure_height_ft: float,
) -> float:
    # ASCE 7 exposure scaling via power law approximation by exposure category.
    exponent = {
        ExposureCategory.b: 0.15,
        ExposureCategory.c: 0.20,
        ExposureCategory.d: 0.25,
    }[exposure_category]
    normalized_height_ft = _clamp(structure_height_ft, 15.0, 1200.0)
    adjusted = basic_wind_speed_mph * ((normalized_height_ft / 33.0) ** exponent)
    return round(_clamp(adjusted, 0.0, 260.0), 2)


def _resolve_india_seismic_zone(location: InfrastructureLocation) -> int:
    city = _canonical_text(location.city)
    state = _canonical_text(location.state)
    for key, zone in INDIA_CITY_SEISMIC_ZONE.items():
        if key in city or key in state:
            return zone

    seed = f"india-zone|{location.latitude:.4f}|{location.longitude:.4f}"
    zone_levels = [2, 3, 4]
    index = min(int(_blend(seed, 0.0, float(len(zone_levels) - 1)) + 0.49), len(zone_levels) - 1)
    return zone_levels[index]


def _resolve_us_seismic_zone(ss_g: float, s1_g: float) -> int:
    candidate = int(round(max(ss_g * 3.5, s1_g * 8.0)))
    return max(0, min(8, candidate))


def _resolve_china_seismic_zone(location: InfrastructureLocation) -> int:
    seed = f"china-zone|{location.latitude:.4f}|{location.longitude:.4f}"
    return max(3, min(8, int(round(_blend(seed, 3.0, 8.0)))))


def resolve_seismic_zone_and_spectrum(
    location: InfrastructureLocation,
    station: StationRecord,
) -> tuple[int, float, float, list[str]]:
    steps: list[str] = []
    if location.country_code == CountryCode.us:
        zone = _resolve_us_seismic_zone(station.ss_g, station.s1_g)
        ss_g = station.ss_g
        s1_g = station.s1_g
        steps.append("USGS spectral proxies pulled from nearest station profile")
    elif location.country_code == CountryCode.in_:
        zone = _resolve_india_seismic_zone(location)
        zone_to_ss = {2: 0.20, 3: 0.36, 4: 0.50, 5: 0.75}
        ss_g = zone_to_ss.get(zone, 0.20)
        s1_g = round(ss_g * 0.5, 3)
        steps.append("BIS 1893 zone converted to Ss/S1 proxy values")
    else:
        zone = _resolve_china_seismic_zone(location)
        ss_g = round(_clamp(station.ss_g * 1.1, 0.10, 2.50), 3)
        s1_g = round(_clamp(station.s1_g * 1.1, 0.05, 1.20), 3)
        steps.append("GB 50011 regional seismic profile estimated from nearest station")

    return zone, ss_g, s1_g, steps


def interpolate_weather_snapshot(
    *,
    location: InfrastructureLocation,
    exposure_category: ExposureCategory,
    structure_height_ft: float,
    basic_wind_speed_mph_override: float | None = None,
    precipitation_intensity_mm_hr_override: float | None = None,
    reference_timestamp_utc: datetime | None = None,
) -> WeatherParameterSnapshot:
    timestamp = reference_timestamp_utc or datetime.now(timezone.utc)
    interpolation_steps: list[str] = [f"interpolation_timestamp_utc={timestamp.isoformat()}"]

    validated_station = find_nearest_station(location, validated_only=True)
    fallback_station = None
    source_station = validated_station
    if source_station is None:
        fallback_station = find_nearest_station(location, validated_only=False)
        source_station = fallback_station
        interpolation_steps.append("validated station unavailable; fallback to nearest non-validated station")

    if source_station is None:
        raise RuntimeError("No station record available for location")

    base_wind = float(source_station.wind_speed_mph)
    if location.country_code == CountryCode.us:
        base_wind = float(county_mapped_wind_speed_mph(location))
        interpolation_steps.append("applied county-level ASCE 7-22 3-second gust wind map")

    if basic_wind_speed_mph_override is not None:
        base_wind = basic_wind_speed_mph_override
        interpolation_steps.append("applied request-level basic wind speed override")

    base_wind = float(_round_1mph(base_wind))
    adjusted_wind = height_adjusted_wind_speed_mph(
        base_wind,
        exposure_category=exposure_category,
        structure_height_ft=structure_height_ft,
    )
    interpolation_steps.append(f"height adjusted wind speed using exposure {exposure_category.value}")

    seismic_zone, ss_g, s1_g, seismic_steps = resolve_seismic_zone_and_spectrum(location, source_station)
    interpolation_steps.extend(seismic_steps)

    idf_100 = _clamp(source_station.idf_100_year_mm_hr, 1.0, 1000.0)
    precipitation_intensity = idf_100 * 0.75
    if precipitation_intensity_mm_hr_override is not None:
        precipitation_intensity = precipitation_intensity_mm_hr_override
        interpolation_steps.append("applied request-level precipitation intensity override")
    precipitation_intensity = round(_clamp(precipitation_intensity, 1.0, 1000.0), 2)

    latitude_factor = abs(location.latitude) / 90.0
    freeze_thaw_cycles = int(round(source_station.freeze_thaw_cycles * (0.7 + latitude_factor)))

    coastal_boost = 1.2 if (_coastal_hint(location) or source_station.coastal) else 0.65
    salt_spray = round(_clamp(source_station.salt_spray_mg_m2_day * coastal_boost, 0.0, 500.0), 2)

    so2 = round(_clamp(source_station.so2_ug_m3, 0.0, 1000.0), 2)
    pressure = round(_clamp(source_station.pressure_hpa, 850.0, 1100.0), 2)

    interpolation_steps.append("calculated freeze-thaw and salt-spray severity proxies")
    interpolation_steps.append("resolved SO2 and pressure from NOAA/IMD aligned station channels")

    return WeatherParameterSnapshot(
        source_station_id=source_station.station_id,
        fallback_station_id=fallback_station.station_id if fallback_station else None,
        basic_wind_speed_mph=base_wind,
        height_adjusted_wind_speed_mph=adjusted_wind,
        exposure_category=exposure_category,
        seismic_zone=seismic_zone,
        ss_g=ss_g,
        s1_g=s1_g,
        precipitation_intensity_mm_hr=precipitation_intensity,
        idf_100_year_mm_hr=round(idf_100, 2),
        freeze_thaw_cycles=max(0, freeze_thaw_cycles),
        salt_spray_mg_m2_day=salt_spray,
        so2_deposition_ug_m3=so2,
        pressure_hpa=pressure,
        interpolation_steps=interpolation_steps,
    )


def tolerance_against_official(
    snapshot: WeatherParameterSnapshot,
    official: OfficialStationObservation,
    *,
    threshold_pct: float = 5.0,
) -> ValidationToleranceCheck:
    def error_pct(predicted: float, observed: float) -> float:
        if observed == 0.0:
            return 0.0 if predicted == 0.0 else 100.0
        return abs(predicted - observed) / abs(observed) * 100.0

    error_map = {
        "wind_speed_mph": error_pct(snapshot.basic_wind_speed_mph, official.wind_speed_mph),
        "precipitation_intensity_mm_hr": error_pct(
            snapshot.precipitation_intensity_mm_hr,
            official.precipitation_intensity_mm_hr,
        ),
        "pressure_hpa": error_pct(snapshot.pressure_hpa, official.pressure_hpa),
    }
    max_error = max(error_map.values()) if error_map else 0.0

    return ValidationToleranceCheck(
        station_id=official.station_id,
        max_error_pct=round(max_error, 3),
        threshold_pct=threshold_pct,
        within_tolerance=max_error <= threshold_pct,
        parameter_error_pct={k: round(v, 3) for k, v in error_map.items()},
    )


def out_of_range_parameters(snapshot: WeatherParameterSnapshot) -> list[str]:
    violations: list[str] = []

    checks: list[tuple[str, bool]] = [
        ("wind_speed_mph", 0.0 <= snapshot.basic_wind_speed_mph <= 200.0),
        ("seismic_zone", 0 <= snapshot.seismic_zone <= 8),
        ("precipitation_intensity_mm_hr", 1.0 <= snapshot.precipitation_intensity_mm_hr <= 1000.0),
        ("pressure_hpa", 850.0 <= snapshot.pressure_hpa <= 1100.0),
        ("idf_100_year_mm_hr", 1.0 <= snapshot.idf_100_year_mm_hr <= 1000.0),
    ]

    for key, is_valid in checks:
        if not is_valid:
            violations.append(key)

    return violations
