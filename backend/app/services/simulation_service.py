from app.algorithms.degradation import corrosion_rate_mm_per_year
from app.algorithms.environmental_risk import calculate_environmental_risk
from app.algorithms.recommendations import prevention_recommendation
from app.algorithms.risk_classification import classify_failure_risk
from app.models.simulation import SimulationRequest, SimulationResult


class SimulationService:
    """Coordinates scientific algorithms for corrosion simulation pipelines."""

    def run_simulation(self, payload: SimulationRequest) -> SimulationResult:
        environment_risk = calculate_environmental_risk(payload.environment)

        # Placeholder mass loss proxy. Replace with Faraday + electrochemical model outputs.
        mass_loss_g = (environment_risk.risk_score / 100.0) * payload.exposure_time_hours * 0.02

        # Convert SI inputs to corrosion rate equation units.
        area_cm2 = payload.exposed_area_m2 * 10000.0
        density_g_cm3 = payload.material.density_kg_m3 / 1000.0
        corrosion_rate = corrosion_rate_mm_per_year(
            mass_loss_g=mass_loss_g,
            density_g_cm3=density_g_cm3,
            area_cm2=area_cm2,
            exposure_time_h=payload.exposure_time_hours,
        )

        # Baseline thickness assumptions are placeholders until asset profile ingestion is added.
        initial_thickness_mm = 12.0
        minimum_safe_thickness_mm = 7.5
        estimated_lifespan = (
            (initial_thickness_mm - minimum_safe_thickness_mm) / corrosion_rate
            if corrosion_rate > 0
            else 9999.0
        )

        risk_level = classify_failure_risk(corrosion_rate, estimated_lifespan)
        recommendation = prevention_recommendation(risk_level)

        return SimulationResult(
            environment_risk=environment_risk,
            corrosion_rate_mm_per_year=corrosion_rate,
            estimated_lifespan_years=estimated_lifespan,
            risk_classification=risk_level,
            recommendation_summary=recommendation,
        )
