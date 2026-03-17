from app.models.environment import EnvironmentInput, EnvironmentRiskResult


def calculate_environmental_risk(input_data: EnvironmentInput) -> EnvironmentRiskResult:
    """
    Placeholder environmental risk scoring.

    Production implementation should incorporate weighted hazard terms:
    - moisture and electrolyte availability
    - chloride ion aggressiveness
    - pH-driven acidity/alkalinity effects
    - dissolved oxygen effects on cathodic kinetics
    """
    score = (
        0.30 * input_data.relative_humidity_pct
        + 0.25 * min(input_data.chloride_ppm / 10.0, 100)
        + 0.20 * (abs(7 - input_data.ph) * 10)
        + 0.25 * min(input_data.dissolved_oxygen_mg_l * 8, 100)
    )
    bounded_score = max(0.0, min(score, 100.0))

    if bounded_score < 35:
        band = "low"
    elif bounded_score < 70:
        band = "moderate"
    else:
        band = "high"

    return EnvironmentRiskResult(
        risk_score=bounded_score,
        risk_band=band,
        rationale="Preliminary weighted composite environmental aggressiveness score.",
    )
