from __future__ import annotations

from dataclasses import dataclass

from app.models.infrastructure import (
    CodeValidationResult,
    DesignCodeFamily,
    InfrastructureValidationRequest,
    LimitStateCheckResult,
    MaterialSystem,
    WeatherParameterSnapshot,
)

STRUCTURAL_VALIDATION_ENGINE_VERSION = "infra-structural-v2.0.0"


@dataclass(frozen=True)
class LoadState:
    dead_kN: float
    live_kN: float
    wind_kN: float
    seismic_kN: float
    snow_kN: float
    thermal_kN: float


def _round(value: float) -> float:
    return round(value, 4)


def _asce_exposure_coefficient(exposure: str, structure_height_ft: float) -> float:
    normalized_height = max(15.0, min(structure_height_ft, 1200.0))
    if exposure == "B":
        return 0.70 * ((normalized_height / 33.0) ** 0.15)
    if exposure == "D":
        return 0.95 * ((normalized_height / 33.0) ** 0.25)
    return 0.85 * ((normalized_height / 33.0) ** 0.20)


def _derive_wind_load_kN(
    request: InfrastructureValidationRequest,
    weather: WeatherParameterSnapshot,
) -> float:
    if request.loads.wind_load_kN is not None:
        return request.loads.wind_load_kN

    kd = 0.85
    kzt = 1.0
    kz = _asce_exposure_coefficient(request.exposure_category.value, request.structure_height_ft)
    qz_psf = 0.00256 * kz * kd * kzt * (weather.height_adjusted_wind_speed_mph ** 2)
    qz_kN_m2 = qz_psf * 0.047880258
    wind_kN = qz_kN_m2 * request.effective_projected_area_m2
    return _round(max(0.0, wind_kN))


def _derive_seismic_load_kN(
    request: InfrastructureValidationRequest,
    weather: WeatherParameterSnapshot,
) -> float:
    if request.loads.seismic_load_kN is not None:
        return request.loads.seismic_load_kN

    importance_factor = 1.15
    response_modification = 4.0 if request.material_system == MaterialSystem.steel else 3.0
    base_shear_coeff = max(0.02, min(1.2, (0.6 * weather.ss_g + 0.4 * weather.s1_g) * importance_factor / response_modification))
    seismic_weight = request.loads.dead_load_kN + 0.25 * request.loads.live_load_kN
    seismic_kN = base_shear_coeff * seismic_weight
    return _round(max(0.0, seismic_kN))


def _resolve_capacity_kN(
    request: InfrastructureValidationRequest,
    *,
    design_intent: str,
) -> float:
    if design_intent == "SLS":
        base_capacity = request.capacities.serviceability_capacity_kN
    else:
        base_capacity = request.capacities.ultimate_capacity_kN

    if request.capacities.member_area_mm2 and request.capacities.allowable_stress_mpa:
        stress_based_capacity = request.capacities.member_area_mm2 * request.capacities.allowable_stress_mpa / 1000.0
        if request.material_system == MaterialSystem.steel:
            stress_based_capacity *= 0.90
        else:
            stress_based_capacity *= 0.75
        base_capacity = min(base_capacity, stress_based_capacity)

    if request.material_system == MaterialSystem.concrete and design_intent == "ULS":
        base_capacity *= 0.92

    return max(0.001, _round(base_capacity))


def _evaluate_limit_state(
    *,
    request: InfrastructureValidationRequest,
    code_family: DesignCodeFamily,
    limit_state_id: str,
    expression: str,
    code_reference: str,
    design_intent: str,
    demand_kN: float,
) -> LimitStateCheckResult:
    capacity_kN = _resolve_capacity_kN(request, design_intent=design_intent)
    if demand_kN <= 0.0:
        utilization = 0.0
        margin = 999.0
    else:
        utilization = demand_kN / capacity_kN
        margin = (capacity_kN / demand_kN) - 1.0

    return LimitStateCheckResult(
        limit_state_id=limit_state_id,
        expression=expression,
        code_reference=code_reference,
        design_intent=design_intent,
        demand_kN=_round(max(0.0, demand_kN)),
        capacity_kN=capacity_kN,
        utilization_ratio=_round(max(0.0, utilization)),
        margin_of_safety=_round(margin),
        passes=utilization <= 1.0,
    )


def _asce_limit_states(request: InfrastructureValidationRequest, loads: LoadState) -> list[LimitStateCheckResult]:
    combinations = [
        (
            "ASCE-ULS-1",
            "1.4D",
            "ASCE 7-22 Chapter 2, Sec 2.3.1",
            "ULS",
            1.4 * loads.dead_kN,
        ),
        (
            "ASCE-ULS-2",
            "1.2D + 1.6L + 0.5S + 0.5T",
            "ASCE 7-22 Chapter 2, Sec 2.3.2",
            "ULS",
            1.2 * loads.dead_kN + 1.6 * loads.live_kN + 0.5 * loads.snow_kN + 0.5 * loads.thermal_kN,
        ),
        (
            "ASCE-ULS-3",
            "1.2D + 1.0W + 1.0L + 0.5S + 0.2T",
            "ASCE 7-22 Chapters 26-31",
            "ULS",
            1.2 * loads.dead_kN + 1.0 * loads.wind_kN + 1.0 * loads.live_kN + 0.5 * loads.snow_kN + 0.2 * loads.thermal_kN,
        ),
        (
            "ASCE-ULS-4",
            "0.9D + 1.0W",
            "ASCE 7-22 Chapters 26-31",
            "ULS",
            0.9 * loads.dead_kN + 1.0 * loads.wind_kN,
        ),
        (
            "ASCE-ULS-5",
            "1.2D + 1.0E + 0.5L + 0.2S",
            "ASCE 7-22 Chapter 12",
            "ULS",
            1.2 * loads.dead_kN + 1.0 * loads.seismic_kN + 0.5 * loads.live_kN + 0.2 * loads.snow_kN,
        ),
        (
            "ASCE-SLS-1",
            "1.0D + 1.0L",
            "ASCE 7-22 Chapter 2, Sec 2.4",
            "SLS",
            1.0 * loads.dead_kN + 1.0 * loads.live_kN,
        ),
        (
            "ASCE-SLS-2",
            "1.0D + 0.7W + 0.5L",
            "ASCE 7-22 Chapter 2, Sec 2.4",
            "SLS",
            1.0 * loads.dead_kN + 0.7 * loads.wind_kN + 0.5 * loads.live_kN,
        ),
    ]

    return [
        _evaluate_limit_state(
            request=request,
            code_family=DesignCodeFamily.asce7_22,
            limit_state_id=limit_state_id,
            expression=expression,
            code_reference=code_reference,
            design_intent=design_intent,
            demand_kN=demand_kN,
        )
        for limit_state_id, expression, code_reference, design_intent, demand_kN in combinations
    ]


def _eurocode_limit_states(request: InfrastructureValidationRequest, loads: LoadState) -> list[LimitStateCheckResult]:
    gamma_g = 1.35 if request.material_system == MaterialSystem.steel else 1.40
    gamma_q = 1.50

    # India National Annex style companion factors.
    psi0_live = 0.70
    psi0_wind = 0.60
    psi0_snow = 0.50
    psi0_thermal = 0.60

    psi1_live = 0.50
    psi1_wind = 0.20
    psi1_snow = 0.20

    psi2_live = 0.30
    psi2_wind = 0.00
    psi2_snow = 0.00
    psi2_thermal = 0.30

    combinations = [
        (
            "EC-ULS-FUND",
            "gammaG*G + gammaQ*Q + gammaQ*psi0,w*W + gammaQ*psi0,s*S + gammaQ*psi0,t*T",
            "EN 1990 + EN 1991 + EN 1993/1992 (India NA)",
            "ULS",
            gamma_g * loads.dead_kN
            + gamma_q * loads.live_kN
            + gamma_q * psi0_wind * loads.wind_kN
            + gamma_q * psi0_snow * loads.snow_kN
            + gamma_q * psi0_thermal * loads.thermal_kN,
        ),
        (
            "EC-ULS-SEIS",
            "gammaG*G + E + psi2,l*Q + psi2,s*S",
            "EN 1998 seismic combination (India NA)",
            "ULS",
            gamma_g * loads.dead_kN + 1.0 * loads.seismic_kN + psi2_live * loads.live_kN + psi2_snow * loads.snow_kN,
        ),
        (
            "EC-SLS-RARE",
            "G + Q + psi0,w*W + psi0,s*S + psi0,t*T",
            "EN 1990 SLS rare",
            "SLS",
            loads.dead_kN
            + loads.live_kN
            + psi0_wind * loads.wind_kN
            + psi0_snow * loads.snow_kN
            + psi0_thermal * loads.thermal_kN,
        ),
        (
            "EC-SLS-FREQ",
            "G + psi1,l*Q + psi1,w*W + psi1,s*S",
            "EN 1990 SLS frequent",
            "SLS",
            loads.dead_kN
            + psi1_live * loads.live_kN
            + psi1_wind * loads.wind_kN
            + psi1_snow * loads.snow_kN,
        ),
        (
            "EC-SLS-QUASI",
            "G + psi2,l*Q + psi2,w*W + psi2,s*S + psi2,t*T",
            "EN 1990 SLS quasi-permanent",
            "SLS",
            loads.dead_kN
            + psi2_live * loads.live_kN
            + psi2_wind * loads.wind_kN
            + psi2_snow * loads.snow_kN
            + psi2_thermal * loads.thermal_kN,
        ),
        (
            "EC-ULS-FIRE-ROBUST",
            "1.0G + 0.7Q + 0.6T",
            "EN 1990 accidental/robustness envelope",
            "ULS",
            1.0 * loads.dead_kN + 0.7 * loads.live_kN + 0.6 * loads.thermal_kN,
        ),
    ]

    return [
        _evaluate_limit_state(
            request=request,
            code_family=DesignCodeFamily.eurocode_in_na,
            limit_state_id=limit_state_id,
            expression=expression,
            code_reference=code_reference,
            design_intent=design_intent,
            demand_kN=demand_kN,
        )
        for limit_state_id, expression, code_reference, design_intent, demand_kN in combinations
    ]


def _gb_limit_states(request: InfrastructureValidationRequest, loads: LoadState) -> list[LimitStateCheckResult]:
    combinations = [
        (
            "GB-ULS-1",
            "1.2D + 1.4L",
            "GB 50009-2012 load combination",
            "ULS",
            1.2 * loads.dead_kN + 1.4 * loads.live_kN,
        ),
        (
            "GB-ULS-2",
            "1.2D + 1.4W + 0.7L",
            "GB 50009-2012 wind governed",
            "ULS",
            1.2 * loads.dead_kN + 1.4 * loads.wind_kN + 0.7 * loads.live_kN,
        ),
        (
            "GB-ULS-3",
            "1.2D + 1.3E + 0.5L",
            "GB 50011-2010 seismic governed",
            "ULS",
            1.2 * loads.dead_kN + 1.3 * loads.seismic_kN + 0.5 * loads.live_kN,
        ),
        (
            "GB-SLS-1",
            "D + L + 0.6W",
            "GB 50009-2012 serviceability",
            "SLS",
            loads.dead_kN + loads.live_kN + 0.6 * loads.wind_kN,
        ),
        (
            "GB-SLS-2",
            "D + 0.7L + 0.7S + 0.6T",
            "GB 50009-2012 variable load serviceability",
            "SLS",
            loads.dead_kN + 0.7 * loads.live_kN + 0.7 * loads.snow_kN + 0.6 * loads.thermal_kN,
        ),
        (
            "GB-STEEL-50017",
            "1.1D + 1.1L + 1.1W",
            "GB 50017-2017 steel member stability envelope",
            "ULS",
            1.1 * loads.dead_kN + 1.1 * loads.live_kN + 1.1 * loads.wind_kN,
        ),
    ]

    return [
        _evaluate_limit_state(
            request=request,
            code_family=DesignCodeFamily.gb_500,
            limit_state_id=limit_state_id,
            expression=expression,
            code_reference=code_reference,
            design_intent=design_intent,
            demand_kN=demand_kN,
        )
        for limit_state_id, expression, code_reference, design_intent, demand_kN in combinations
    ]


def _build_load_state(
    request: InfrastructureValidationRequest,
    weather: WeatherParameterSnapshot,
) -> LoadState:
    return LoadState(
        dead_kN=request.loads.dead_load_kN,
        live_kN=request.loads.live_load_kN,
        wind_kN=_derive_wind_load_kN(request, weather),
        seismic_kN=_derive_seismic_load_kN(request, weather),
        snow_kN=request.loads.snow_load_kN,
        thermal_kN=request.loads.thermal_load_kN,
    )


def validate_code_family(
    request: InfrastructureValidationRequest,
    weather: WeatherParameterSnapshot,
    code_family: DesignCodeFamily,
) -> CodeValidationResult:
    loads = _build_load_state(request, weather)

    if code_family == DesignCodeFamily.asce7_22:
        limit_states = _asce_limit_states(request, loads)
    elif code_family == DesignCodeFamily.eurocode_in_na:
        limit_states = _eurocode_limit_states(request, loads)
    else:
        limit_states = _gb_limit_states(request, loads)

    governing = max(limit_states, key=lambda item: item.utilization_ratio)
    return CodeValidationResult(
        code_family=code_family,
        material_system=request.material_system,
        governing_limit_state_id=governing.limit_state_id,
        passes=all(item.passes for item in limit_states),
        limit_states=limit_states,
    )


def validate_all_codes(
    request: InfrastructureValidationRequest,
    weather: WeatherParameterSnapshot,
) -> list[CodeValidationResult]:
    return [validate_code_family(request, weather, code_family) for code_family in request.design_codes]
