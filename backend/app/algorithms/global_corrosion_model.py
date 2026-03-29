from __future__ import annotations

from dataclasses import dataclass
from math import log10

from app.models.environment import EnvironmentInput


GLOBAL_CORROSION_MODEL_VERSION = "global-calibrated-v1.1.0"
UNCERTAINTY_CONFIDENCE_LEVEL = 0.90


@dataclass(frozen=True)
class AssetProfile:
    key: str
    initial_thickness_mm: float
    minimum_safe_thickness_mm: float
    exposure_factor: float
    buried: bool


@dataclass(frozen=True)
class MaterialCalibration:
    key: str
    base_uniform_rate_mm_per_year: float
    localized_sensitivity: float


@dataclass(frozen=True)
class RegionCalibrationPack:
    key: str
    label: str
    temperature_multiplier: float
    humidity_multiplier: float
    chloride_multiplier: float
    uv_multiplier: float
    mic_multiplier: float
    soil_multiplier: float
    severity_multiplier: float
    rate_multiplier: float
    uncertainty_sigma: float
    confidence_floor: float


ASSET_PROFILES: dict[str, AssetProfile] = {
    "pipeline_submerged": AssetProfile("pipeline_submerged", 14.0, 8.5, 1.25, True),
    "pipeline_atmospheric": AssetProfile("pipeline_atmospheric", 12.0, 7.5, 1.05, True),
    "bridge_suspension": AssetProfile("bridge_suspension", 25.0, 16.0, 1.10, False),
    "bridge_beam": AssetProfile("bridge_beam", 20.0, 13.0, 1.05, False),
    "marine_vessel_hull": AssetProfile("marine_vessel_hull", 18.0, 11.0, 1.28, False),
    "storage_tank_ast": AssetProfile("storage_tank_ast", 16.0, 10.0, 1.08, False),
    "offshore_platform_fixed": AssetProfile("offshore_platform_fixed", 28.0, 18.0, 1.32, False),
    "offshore_platform_fpso": AssetProfile("offshore_platform_fpso", 24.0, 15.0, 1.30, False),
    "cooling_tower": AssetProfile("cooling_tower", 10.0, 6.0, 1.18, False),
    "reinforced_concrete": AssetProfile("reinforced_concrete", 8.0, 4.5, 0.95, True),
    "wind_turbine_tower": AssetProfile("wind_turbine_tower", 22.0, 14.0, 1.08, False),
    "generic_asset": AssetProfile("generic_asset", 12.0, 7.5, 1.00, False),
}


MATERIAL_CALIBRATIONS: dict[str, MaterialCalibration] = {
    "carbon_steel": MaterialCalibration("carbon_steel", 0.120, 1.20),
    "stainless_304": MaterialCalibration("stainless_304", 0.018, 0.95),
    "stainless_316": MaterialCalibration("stainless_316", 0.010, 0.85),
    "duplex_2205": MaterialCalibration("duplex_2205", 0.007, 0.78),
    "aluminum_6061": MaterialCalibration("aluminum_6061", 0.035, 1.10),
    "aluminum_5083": MaterialCalibration("aluminum_5083", 0.028, 1.05),
    "copper_nickel_9010": MaterialCalibration("copper_nickel_9010", 0.014, 0.90),
    "nickel_inconel_625": MaterialCalibration("nickel_inconel_625", 0.006, 0.75),
    "titanium_grade_2": MaterialCalibration("titanium_grade_2", 0.003, 0.60),
    "galvanized_steel": MaterialCalibration("galvanized_steel", 0.090, 1.05),
    "weathering_steel": MaterialCalibration("weathering_steel", 0.080, 1.12),
    "cast_iron": MaterialCalibration("cast_iron", 0.110, 1.15),
    "ferrous": MaterialCalibration("ferrous", 0.110, 1.18),
    "austenitic_stainless": MaterialCalibration("austenitic_stainless", 0.016, 0.90),
    "duplex_stainless": MaterialCalibration("duplex_stainless", 0.008, 0.80),
    "aluminum_alloy": MaterialCalibration("aluminum_alloy", 0.030, 1.08),
    "nickel_alloy": MaterialCalibration("nickel_alloy", 0.007, 0.80),
    "titanium": MaterialCalibration("titanium", 0.0035, 0.62),
    "custom": MaterialCalibration("custom", 0.020, 1.00),
}


REGION_CALIBRATION_PACKS: dict[str, RegionCalibrationPack] = {
    "global_default": RegionCalibrationPack(
        "global_default",
        "Global Default",
        1.00,
        1.00,
        1.00,
        1.00,
        1.00,
        1.00,
        1.00,
        1.00,
        0.18,
        0.72,
    ),
    "temperate_industrial": RegionCalibrationPack(
        "temperate_industrial",
        "Temperate Industrial",
        1.02,
        1.03,
        1.04,
        0.98,
        1.02,
        1.00,
        1.02,
        1.03,
        0.13,
        0.84,
    ),
    "north_sea_offshore": RegionCalibrationPack(
        "north_sea_offshore",
        "North Sea Offshore",
        0.96,
        1.05,
        1.18,
        0.92,
        1.08,
        1.03,
        1.08,
        1.12,
        0.14,
        0.82,
    ),
    "gulf_tropical_marine": RegionCalibrationPack(
        "gulf_tropical_marine",
        "Gulf Tropical Marine",
        1.14,
        1.10,
        1.21,
        1.12,
        1.07,
        1.00,
        1.15,
        1.19,
        0.16,
        0.79,
    ),
    "monsoon_coastal": RegionCalibrationPack(
        "monsoon_coastal",
        "Monsoon Coastal",
        1.10,
        1.16,
        1.14,
        1.03,
        1.18,
        1.04,
        1.13,
        1.15,
        0.17,
        0.77,
    ),
    "arid_desert_industrial": RegionCalibrationPack(
        "arid_desert_industrial",
        "Arid Desert Industrial",
        1.16,
        0.82,
        0.95,
        1.20,
        0.88,
        1.00,
        0.98,
        1.02,
        0.14,
        0.78,
    ),
    "arctic_subarctic": RegionCalibrationPack(
        "arctic_subarctic",
        "Arctic Subarctic",
        0.78,
        0.93,
        1.01,
        0.86,
        0.90,
        1.08,
        0.88,
        0.90,
        0.19,
        0.70,
    ),
    "equatorial_humid_urban": RegionCalibrationPack(
        "equatorial_humid_urban",
        "Equatorial Humid Urban",
        1.12,
        1.18,
        1.10,
        1.08,
        1.14,
        1.06,
        1.12,
        1.13,
        0.17,
        0.76,
    ),
}


DEFAULT_REGION_KEY = "temperate_industrial"


def clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(max_value, value))


def _contains_any(text: str, tokens: tuple[str, ...]) -> bool:
    return any(token in text for token in tokens)


def canonicalize_asset_type(asset_type: str | None) -> str:
    normalized = (asset_type or "").strip().lower()

    if "pipeline" in normalized and "submerged" in normalized:
        return "pipeline_submerged"
    if "pipeline" in normalized and "atmospheric" in normalized:
        return "pipeline_atmospheric"
    if "bridge" in normalized and "suspension" in normalized:
        return "bridge_suspension"
    if "bridge" in normalized and "beam" in normalized:
        return "bridge_beam"
    if _contains_any(normalized, ("vessel", "hull", "ship")):
        return "marine_vessel_hull"
    if _contains_any(normalized, ("tank", "ast", "storage")):
        return "storage_tank_ast"
    if "offshore" in normalized and "fixed" in normalized:
        return "offshore_platform_fixed"
    if "fpso" in normalized:
        return "offshore_platform_fpso"
    if _contains_any(normalized, ("cooling tower",)):
        return "cooling_tower"
    if _contains_any(normalized, ("reinforced concrete", "concrete")):
        return "reinforced_concrete"
    if _contains_any(normalized, ("wind turbine", "turbine tower")):
        return "wind_turbine_tower"

    return "generic_asset"


def get_asset_profile(asset_type: str | None) -> AssetProfile:
    key = canonicalize_asset_type(asset_type)
    return ASSET_PROFILES.get(key, ASSET_PROFILES["generic_asset"])


def canonicalize_material(material_name: str, alloy_group: str) -> str:
    name = (material_name or "").strip().lower()
    group = (alloy_group or "").strip().lower()

    if _contains_any(name, ("carbon steel", "a36", "a516")):
        return "carbon_steel"
    if _contains_any(name, ("304",)) and "stainless" in name:
        return "stainless_304"
    if _contains_any(name, ("316", "316l")) and "stainless" in name:
        return "stainless_316"
    if _contains_any(name, ("duplex", "2205")):
        return "duplex_2205"
    if _contains_any(name, ("6061",)) and _contains_any(name, ("aluminum", "aluminium")):
        return "aluminum_6061"
    if _contains_any(name, ("5083",)) and _contains_any(name, ("aluminum", "aluminium")):
        return "aluminum_5083"
    if _contains_any(name, ("copper-nickel", "90/10", "cu-ni")):
        return "copper_nickel_9010"
    if _contains_any(name, ("inconel", "625", "nickel alloy")):
        return "nickel_inconel_625"
    if _contains_any(name, ("titanium", "grade 2")):
        return "titanium_grade_2"
    if _contains_any(name, ("galvanized", "galvanised")):
        return "galvanized_steel"
    if _contains_any(name, ("weathering", "corten")):
        return "weathering_steel"
    if _contains_any(name, ("cast iron", "ductile")):
        return "cast_iron"

    if "ferrous" in group:
        return "ferrous"
    if "austenitic" in group:
        return "austenitic_stainless"
    if "duplex" in group:
        return "duplex_stainless"
    if "aluminum" in group or "aluminium" in group:
        return "aluminum_alloy"
    if "nickel" in group:
        return "nickel_alloy"
    if "titanium" in group:
        return "titanium"

    return "custom"


def get_material_calibration(material_name: str, alloy_group: str) -> MaterialCalibration:
    key = canonicalize_material(material_name, alloy_group)
    return MATERIAL_CALIBRATIONS.get(key, MATERIAL_CALIBRATIONS["custom"])


def normalize_mic_activity(mic_activity: str | None) -> str:
    normalized = (mic_activity or "low").strip().lower()
    if normalized.startswith("high"):
        return "high"
    if normalized.startswith("med"):
        return "medium"
    return "low"


def normalize_criticality(criticality: str | None) -> str:
    normalized = (criticality or "high").strip().lower()
    if "mission" in normalized:
        return "mission_critical"
    if normalized.startswith("high"):
        return "high"
    if normalized.startswith("med"):
        return "medium"
    return "low"


def canonicalize_region_key(region_hint: str | None) -> str | None:
    normalized = (region_hint or "").strip().lower()
    if not normalized:
        return None

    normalized_key = normalized.replace("-", "_").replace(" ", "_")
    if normalized_key in REGION_CALIBRATION_PACKS:
        return normalized_key

    if _contains_any(normalized, ("auto", "model selection", "auto-detect", "autodetect", "default")):
        return None
    if _contains_any(normalized, ("north sea", "north atlantic", "ukcs", "norway")):
        return "north_sea_offshore"
    if _contains_any(normalized, ("gulf", "arabian", "tropical marine", "persian")):
        return "gulf_tropical_marine"
    if _contains_any(normalized, ("monsoon", "south asia coastal", "bay of bengal")):
        return "monsoon_coastal"
    if _contains_any(normalized, ("arid", "desert", "dry industrial")):
        return "arid_desert_industrial"
    if _contains_any(normalized, ("arctic", "subarctic", "polar")):
        return "arctic_subarctic"
    if _contains_any(normalized, ("equatorial", "humid urban", "tropical urban")):
        return "equatorial_humid_urban"
    if _contains_any(normalized, ("temperate", "industrial", "continental")):
        return "temperate_industrial"

    return None


def auto_select_region_key(
    input_data: EnvironmentInput,
    *,
    asset_profile: AssetProfile,
    uv_index: float | None,
    mic_activity: str | None,
    soil_resistivity_ohm_cm: float | None,
) -> str:
    chloride = input_data.chloride_ppm
    temperature = input_data.temperature_c
    humidity = input_data.relative_humidity_pct
    uv = uv_index or 5.0
    mic = normalize_mic_activity(mic_activity)
    normalized_asset = asset_profile.key

    if chloride >= 22000 and temperature <= 12 and _contains_any(normalized_asset, ("offshore", "marine")):
        return "north_sea_offshore"
    if chloride >= 20000 and temperature >= 24 and humidity >= 72:
        return "gulf_tropical_marine"
    if humidity >= 78 and temperature >= 20 and mic in ("medium", "high"):
        return "monsoon_coastal"
    if temperature <= -5:
        return "arctic_subarctic"
    if humidity <= 35 and temperature >= 30 and uv >= 8:
        return "arid_desert_industrial"
    if (asset_profile.buried and (soil_resistivity_ohm_cm or 5000.0) < 1800) or (
        humidity >= 78 and temperature >= 25 and chloride >= 6000
    ):
        return "equatorial_humid_urban"
    return DEFAULT_REGION_KEY


def get_region_pack(
    input_data: EnvironmentInput,
    *,
    asset_profile: AssetProfile,
    region_hint: str | None,
    uv_index: float | None,
    mic_activity: str | None,
    soil_resistivity_ohm_cm: float | None,
) -> RegionCalibrationPack:
    explicit_region_key = canonicalize_region_key(region_hint)
    selected_region_key = explicit_region_key or auto_select_region_key(
        input_data,
        asset_profile=asset_profile,
        uv_index=uv_index,
        mic_activity=mic_activity,
        soil_resistivity_ohm_cm=soil_resistivity_ohm_cm,
    )
    return REGION_CALIBRATION_PACKS.get(selected_region_key, REGION_CALIBRATION_PACKS["global_default"])


def compliance_factor(compliance_standard: str | None) -> float:
    normalized = (compliance_standard or "").strip().lower()
    if "norsok" in normalized:
        return 0.84
    if "nace" in normalized:
        return 0.86
    if "iso 12944" in normalized:
        return 0.89
    if "astm" in normalized:
        return 0.93
    return 1.00


def criticality_factor(criticality: str | None) -> float:
    level = normalize_criticality(criticality)
    if level == "mission_critical":
        return 1.20
    if level == "high":
        return 1.12
    if level == "medium":
        return 1.05
    return 1.00


def _mic_factor(mic_activity: str | None) -> float:
    level = normalize_mic_activity(mic_activity)
    if level == "high":
        return 1.55
    if level == "medium":
        return 1.25
    return 1.00


def _temperature_factor(temperature_c: float) -> float:
    # Arrhenius-style Q10 scaling around 20 C.
    return clamp(2 ** ((temperature_c - 20.0) / 10.0), 0.35, 5.50)


def _humidity_factor(relative_humidity_pct: float) -> float:
    rh = clamp(relative_humidity_pct, 0.0, 100.0)
    if rh < 40:
        return 0.45
    if rh < 60:
        return 0.45 + ((rh - 40.0) / 20.0) * 0.45
    if rh < 80:
        return 0.90 + ((rh - 60.0) / 20.0) * 0.60
    return 1.50 + ((rh - 80.0) / 20.0) * 1.10


def _chloride_factor(chloride_ppm: float) -> float:
    return clamp(1.0 + (log10(max(chloride_ppm, 0.0) + 1.0) / 2.2), 1.0, 3.2)


def _ph_factor(ph: float) -> float:
    deviation = abs(clamp(ph, 0.0, 14.0) - 7.0)
    return clamp(1.0 + (deviation ** 1.25) * 0.12, 1.0, 2.4)


def _oxygen_factor(dissolved_oxygen_mg_l: float) -> float:
    return clamp(1.0 + (dissolved_oxygen_mg_l - 4.5) * 0.07, 0.75, 1.7)


def _uv_factor(uv_index: float | None) -> float:
    if uv_index is None:
        return 1.0
    normalized = clamp((uv_index - 3.0) / 8.0, 0.0, 1.5)
    return 1.0 + normalized * 0.22


def _soil_factor(soil_resistivity_ohm_cm: float | None, buried: bool) -> float:
    if not buried:
        return 1.0

    resistivity = max(soil_resistivity_ohm_cm or 5000.0, 200.0)
    return clamp((7000.0 / resistivity) ** 0.30, 0.75, 1.9)


def compute_environment_multipliers(
    input_data: EnvironmentInput,
    *,
    uv_index: float | None,
    mic_activity: str | None,
    soil_resistivity_ohm_cm: float | None,
    asset_profile: AssetProfile,
    region_pack: RegionCalibrationPack,
) -> dict[str, float]:
    temperature_multiplier = clamp(
        _temperature_factor(input_data.temperature_c) * region_pack.temperature_multiplier,
        0.30,
        6.00,
    )
    humidity_multiplier = clamp(
        _humidity_factor(input_data.relative_humidity_pct) * region_pack.humidity_multiplier,
        0.35,
        3.20,
    )
    chloride_multiplier = clamp(
        _chloride_factor(input_data.chloride_ppm) * region_pack.chloride_multiplier,
        0.90,
        3.60,
    )
    uv_multiplier = clamp(_uv_factor(uv_index) * region_pack.uv_multiplier, 0.80, 1.80)
    mic_multiplier = clamp(_mic_factor(mic_activity) * region_pack.mic_multiplier, 0.90, 2.10)
    soil_multiplier = clamp(
        _soil_factor(soil_resistivity_ohm_cm, asset_profile.buried) * region_pack.soil_multiplier,
        0.70,
        2.10,
    )

    return {
        "temperature": temperature_multiplier,
        "humidity": humidity_multiplier,
        "chloride": chloride_multiplier,
        "ph": _ph_factor(input_data.ph),
        "oxygen": _oxygen_factor(input_data.dissolved_oxygen_mg_l),
        "uv": uv_multiplier,
        "mic": mic_multiplier,
        "soil": soil_multiplier,
    }


def classify_environment_band(severity_score: float) -> str:
    if severity_score >= 80:
        return "critical"
    if severity_score >= 60:
        return "high"
    if severity_score >= 35:
        return "moderate"
    return "low"


def calculate_environmental_severity(
    input_data: EnvironmentInput,
    *,
    uv_index: float | None = None,
    mic_activity: str | None = None,
    soil_resistivity_ohm_cm: float | None = None,
    asset_type: str | None = None,
    region_hint: str | None = None,
) -> tuple[float, str, dict[str, float], RegionCalibrationPack]:
    asset_profile = get_asset_profile(asset_type)
    region_pack = get_region_pack(
        input_data,
        asset_profile=asset_profile,
        region_hint=region_hint,
        uv_index=uv_index,
        mic_activity=mic_activity,
        soil_resistivity_ohm_cm=soil_resistivity_ohm_cm,
    )
    multipliers = compute_environment_multipliers(
        input_data,
        uv_index=uv_index,
        mic_activity=mic_activity,
        soil_resistivity_ohm_cm=soil_resistivity_ohm_cm,
        asset_profile=asset_profile,
        region_pack=region_pack,
    )

    temperature_score = clamp((input_data.temperature_c + 20.0) / 80.0 * 100.0, 0.0, 100.0)
    humidity_score = clamp(input_data.relative_humidity_pct, 0.0, 100.0)
    chloride_score = clamp(log10(input_data.chloride_ppm + 1.0) * 25.0, 0.0, 100.0)
    ph_score = clamp(abs(input_data.ph - 7.0) * 16.0, 0.0, 100.0)
    oxygen_score = clamp(input_data.dissolved_oxygen_mg_l * 10.0, 0.0, 100.0)
    uv_score = clamp((uv_index or 0.0) * 9.0, 0.0, 100.0)
    mic_score = {"low": 20.0, "medium": 55.0, "high": 85.0}[normalize_mic_activity(mic_activity)]
    soil_score = clamp((6000.0 - (soil_resistivity_ohm_cm or 5000.0)) / 60.0, 0.0, 100.0)

    if asset_profile.buried:
        severity = (
            0.16 * temperature_score
            + 0.18 * humidity_score
            + 0.25 * chloride_score
            + 0.12 * ph_score
            + 0.09 * oxygen_score
            + 0.02 * uv_score
            + 0.08 * mic_score
            + 0.10 * soil_score
        )
    else:
        severity = (
            0.18 * temperature_score
            + 0.20 * humidity_score
            + 0.28 * chloride_score
            + 0.14 * ph_score
            + 0.10 * oxygen_score
            + 0.05 * uv_score
            + 0.05 * mic_score
        )

    severity *= region_pack.severity_multiplier

    bounded = clamp(severity, 0.0, 100.0)
    rationale = (
        "Global calibrated aggressiveness model (ISO 9223-style atmospheric drivers, "
        "chloride load, pH deviation, oxygen kinetics, MIC and soil resistivity factors). "
        f"Regional pack applied: {region_pack.label}."
    )
    return bounded, rationale, multipliers, region_pack


def compute_corrosion_rates(
    *,
    material: MaterialCalibration,
    multipliers: dict[str, float],
    asset_profile: AssetProfile,
    region_pack: RegionCalibrationPack,
    compliance_standard: str | None,
    criticality: str | None,
) -> tuple[float, float]:
    environment_multiplier = (
        0.22 * multipliers["temperature"]
        + 0.18 * multipliers["humidity"]
        + 0.25 * multipliers["chloride"]
        + 0.15 * multipliers["ph"]
        + 0.08 * multipliers["oxygen"]
        + 0.04 * multipliers["uv"]
        + 0.05 * multipliers["mic"]
        + 0.03 * multipliers["soil"]
    )

    uniform_rate = (
        material.base_uniform_rate_mm_per_year
        * environment_multiplier
        * asset_profile.exposure_factor
        * region_pack.rate_multiplier
        * compliance_factor(compliance_standard)
    )
    uniform_rate = clamp(uniform_rate, 0.0005, 1.5)

    localized_factor = 1.0 + (multipliers["chloride"] - 1.0) * 0.45
    localized_factor += (multipliers["mic"] - 1.0) * 0.35
    localized_factor += (multipliers["ph"] - 1.0) * 0.25
    localized_factor += material.localized_sensitivity * 0.10
    localized_factor = clamp(localized_factor, 1.0, 2.6)

    design_rate = uniform_rate * localized_factor * criticality_factor(criticality)
    design_rate = clamp(design_rate, uniform_rate, 2.2)

    return uniform_rate, design_rate


def estimate_lifespan_years(asset_profile: AssetProfile, design_corrosion_rate_mm_per_year: float) -> float:
    consumable_thickness_mm = max(
        asset_profile.initial_thickness_mm - asset_profile.minimum_safe_thickness_mm,
        0.1,
    )
    if design_corrosion_rate_mm_per_year <= 0:
        return 120.0

    lifespan = consumable_thickness_mm / design_corrosion_rate_mm_per_year
    return clamp(lifespan, 0.3, 120.0)


def compute_calibration_confidence(
    *,
    region_pack: RegionCalibrationPack,
    material: MaterialCalibration,
    severity_score: float,
    criticality: str | None,
) -> float:
    material_bonus = 0.06 if material.key != "custom" else 0.02
    severity_penalty = max(0.0, severity_score - 70.0) * 0.0017
    criticality_penalty = {
        "low": 0.0,
        "medium": 0.01,
        "high": 0.022,
        "mission_critical": 0.04,
    }[normalize_criticality(criticality)]

    confidence = region_pack.confidence_floor + material_bonus - severity_penalty - criticality_penalty
    return clamp(confidence, 0.62, 0.96)


def compute_uncertainty_bands(
    *,
    uniform_corrosion_rate_mm_per_year: float,
    design_corrosion_rate_mm_per_year: float,
    lifespan_years: float,
    risk_score: float,
    calibration_confidence: float,
    region_pack: RegionCalibrationPack,
    severity_score: float,
    asset_profile: AssetProfile,
) -> dict[str, tuple[float, float, float]]:
    relative_spread = (
        region_pack.uncertainty_sigma
        + (severity_score / 100.0) * 0.08
        + (1.0 - calibration_confidence) * 0.22
    )
    relative_spread = clamp(relative_spread, 0.08, 0.45)

    uniform_lower = clamp(uniform_corrosion_rate_mm_per_year * (1.0 - relative_spread), 0.0001, 3.0)
    uniform_upper = clamp(uniform_corrosion_rate_mm_per_year * (1.0 + relative_spread), uniform_lower, 3.0)

    design_lower = clamp(design_corrosion_rate_mm_per_year * (1.0 - relative_spread), uniform_lower, 3.2)
    design_upper = clamp(design_corrosion_rate_mm_per_year * (1.0 + relative_spread), design_lower, 3.2)

    consumable_thickness_mm = max(
        asset_profile.initial_thickness_mm - asset_profile.minimum_safe_thickness_mm,
        0.1,
    )
    lifespan_lower = clamp(consumable_thickness_mm / max(design_upper, 0.0001), 0.3, 120.0)
    lifespan_upper = clamp(consumable_thickness_mm / max(design_lower, 0.0001), lifespan_lower, 120.0)

    risk_delta = relative_spread * 35.0
    risk_lower = clamp(risk_score - risk_delta, 0.0, 100.0)
    risk_upper = clamp(risk_score + risk_delta, risk_lower, 100.0)

    return {
        "corrosion_rate_mm_per_year": (uniform_lower, uniform_upper, UNCERTAINTY_CONFIDENCE_LEVEL),
        "design_corrosion_rate_mm_per_year": (design_lower, design_upper, UNCERTAINTY_CONFIDENCE_LEVEL),
        "estimated_lifespan_years": (lifespan_lower, lifespan_upper, UNCERTAINTY_CONFIDENCE_LEVEL),
        "composite_risk_score": (risk_lower, risk_upper, UNCERTAINTY_CONFIDENCE_LEVEL),
    }


def compute_risk_score(
    *,
    environment_severity_score: float,
    uniform_corrosion_rate_mm_per_year: float,
    lifespan_years: float,
    criticality: str | None,
) -> float:
    rate_score = clamp((uniform_corrosion_rate_mm_per_year / 0.40) * 100.0, 0.0, 100.0)
    life_score = clamp((1.0 - min(lifespan_years, 80.0) / 80.0) * 100.0, 0.0, 100.0)

    criticality_boost = {
        "low": 0.0,
        "medium": 4.0,
        "high": 8.0,
        "mission_critical": 14.0,
    }[normalize_criticality(criticality)]

    composite = (
        0.40 * environment_severity_score
        + 0.35 * rate_score
        + 0.25 * life_score
        + criticality_boost
    )
    return clamp(composite, 0.0, 100.0)


def classify_failure_risk_from_score(risk_score: float) -> str:
    if risk_score >= 85:
        return "critical"
    if risk_score >= 65:
        return "high"
    if risk_score >= 40:
        return "moderate"
    return "low"
