from app.models.environment import EnvironmentInput, EnvironmentRiskResult
from app.algorithms.global_corrosion_model import calculate_environmental_severity, classify_environment_band


def calculate_environmental_risk(input_data: EnvironmentInput) -> EnvironmentRiskResult:
    bounded_score, rationale, _, _ = calculate_environmental_severity(input_data)
    band = classify_environment_band(bounded_score)

    return EnvironmentRiskResult(
        risk_score=bounded_score,
        risk_band=band,
        rationale=rationale,
    )
