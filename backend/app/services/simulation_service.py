from datetime import datetime, timedelta, timezone

from app.algorithms.global_corrosion_model import (
    GLOBAL_CORROSION_MODEL_VERSION,
    calculate_environmental_severity,
    classify_environment_band,
    classify_failure_risk_from_score,
    compute_calibration_confidence,
    compute_corrosion_rates,
    compute_risk_score,
    compute_uncertainty_bands,
    estimate_lifespan_years,
    get_asset_profile,
    get_material_calibration,
)
from app.algorithms.recommendations import prevention_recommendation
from app.core.config import get_settings
from app.models.environment import EnvironmentRiskResult
from app.models.simulation import (
    MetricConfidenceInterval,
    SimulationRequest,
    SimulationResult,
    SimulationUncertaintyBands,
)


class SimulationService:
    """Coordinates scientific algorithms for corrosion simulation pipelines."""

    def __init__(self) -> None:
        self.settings = get_settings()

    def run_simulation(self, payload: SimulationRequest) -> SimulationResult:
        asset_profile = get_asset_profile(payload.asset_type)
        material_profile = get_material_calibration(payload.material.name, payload.material.alloy_group)

        severity_score, severity_rationale, multipliers, region_pack = calculate_environmental_severity(
            payload.environment,
            uv_index=payload.uv_index,
            mic_activity=payload.mic_activity,
            soil_resistivity_ohm_cm=payload.soil_resistivity_ohm_cm,
            asset_type=payload.asset_type,
            region_hint=payload.region,
        )
        environment_risk = EnvironmentRiskResult(
            risk_score=severity_score,
            risk_band=classify_environment_band(severity_score),
            rationale=severity_rationale,
        )

        corrosion_rate, design_corrosion_rate = compute_corrosion_rates(
            material=material_profile,
            multipliers=multipliers,
            asset_profile=asset_profile,
            region_pack=region_pack,
            compliance_standard=payload.compliance_standard,
            criticality=payload.criticality,
        )

        estimated_lifespan = estimate_lifespan_years(asset_profile, design_corrosion_rate)
        risk_score = compute_risk_score(
            environment_severity_score=severity_score,
            uniform_corrosion_rate_mm_per_year=corrosion_rate,
            lifespan_years=estimated_lifespan,
            criticality=payload.criticality,
        )
        risk_level = classify_failure_risk_from_score(risk_score)
        calibration_confidence = compute_calibration_confidence(
            region_pack=region_pack,
            material=material_profile,
            severity_score=severity_score,
            criticality=payload.criticality,
        )
        uncertainty = compute_uncertainty_bands(
            uniform_corrosion_rate_mm_per_year=corrosion_rate,
            design_corrosion_rate_mm_per_year=design_corrosion_rate,
            lifespan_years=estimated_lifespan,
            risk_score=risk_score,
            calibration_confidence=calibration_confidence,
            region_pack=region_pack,
            severity_score=severity_score,
            asset_profile=asset_profile,
        )

        def build_interval(metric_name: str) -> MetricConfidenceInterval:
            lower, upper, confidence_level = uncertainty[metric_name]
            return MetricConfidenceInterval(
                lower=lower,
                upper=upper,
                confidence_level=confidence_level,
            )

        uncertainty_bands = SimulationUncertaintyBands(
            corrosion_rate_mm_per_year=build_interval("corrosion_rate_mm_per_year"),
            design_corrosion_rate_mm_per_year=build_interval("design_corrosion_rate_mm_per_year"),
            estimated_lifespan_years=build_interval("estimated_lifespan_years"),
            composite_risk_score=build_interval("composite_risk_score"),
        )

        fallback_applied = False
        fallback_reason: str | None = None
        if calibration_confidence < self.settings.model_confidence_fallback_threshold:
            fallback_applied = True
            fallback_reason = (
                "Calibration confidence dropped below threshold; conservative fallback policy applied. "
                f"confidence={calibration_confidence:.3f} threshold={self.settings.model_confidence_fallback_threshold:.3f}"
            )

            design_corrosion_rate = max(
                design_corrosion_rate,
                uncertainty_bands.design_corrosion_rate_mm_per_year.upper,
            )
            estimated_lifespan = estimate_lifespan_years(asset_profile, design_corrosion_rate)
            risk_score = min(
                max(
                    risk_score,
                    uncertainty_bands.composite_risk_score.upper,
                    self.settings.model_risk_floor_score,
                ),
                100.0,
            )
            risk_level = classify_failure_risk_from_score(risk_score)

            uncertainty = compute_uncertainty_bands(
                uniform_corrosion_rate_mm_per_year=corrosion_rate,
                design_corrosion_rate_mm_per_year=design_corrosion_rate,
                lifespan_years=estimated_lifespan,
                risk_score=risk_score,
                calibration_confidence=calibration_confidence,
                region_pack=region_pack,
                severity_score=severity_score,
                asset_profile=asset_profile,
            )
            uncertainty_bands = SimulationUncertaintyBands(
                corrosion_rate_mm_per_year=MetricConfidenceInterval(
                    lower=uncertainty["corrosion_rate_mm_per_year"][0],
                    upper=uncertainty["corrosion_rate_mm_per_year"][1],
                    confidence_level=uncertainty["corrosion_rate_mm_per_year"][2],
                ),
                design_corrosion_rate_mm_per_year=MetricConfidenceInterval(
                    lower=uncertainty["design_corrosion_rate_mm_per_year"][0],
                    upper=uncertainty["design_corrosion_rate_mm_per_year"][1],
                    confidence_level=uncertainty["design_corrosion_rate_mm_per_year"][2],
                ),
                estimated_lifespan_years=MetricConfidenceInterval(
                    lower=uncertainty["estimated_lifespan_years"][0],
                    upper=uncertainty["estimated_lifespan_years"][1],
                    confidence_level=uncertainty["estimated_lifespan_years"][2],
                ),
                composite_risk_score=MetricConfidenceInterval(
                    lower=uncertainty["composite_risk_score"][0],
                    upper=uncertainty["composite_risk_score"][1],
                    confidence_level=uncertainty["composite_risk_score"][2],
                ),
            )

        recommendation = prevention_recommendation(risk_level)
        if fallback_applied:
            recommendation = f"{recommendation} Conservative fallback policy is active until recalibration completes."

        recalibration_due_by = datetime.now(timezone.utc) + timedelta(days=self.settings.recalibration_cadence_days)

        return SimulationResult(
            environment_risk=environment_risk,
            corrosion_rate_mm_per_year=corrosion_rate,
            design_corrosion_rate_mm_per_year=design_corrosion_rate,
            composite_risk_score=risk_score,
            estimated_lifespan_years=estimated_lifespan,
            risk_classification=risk_level,
            recommendation_summary=recommendation,
            model_version=GLOBAL_CORROSION_MODEL_VERSION,
            asset_profile=asset_profile.key,
            region_key=region_pack.key,
            region_name=region_pack.label,
            initial_thickness_mm=asset_profile.initial_thickness_mm,
            minimum_safe_thickness_mm=asset_profile.minimum_safe_thickness_mm,
            calibration_confidence=calibration_confidence,
            uncertainty_bands=uncertainty_bands,
            fallback_applied=fallback_applied,
            fallback_reason=fallback_reason,
            recalibration_due_by=recalibration_due_by,
        )
