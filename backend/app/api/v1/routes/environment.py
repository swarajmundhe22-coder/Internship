from fastapi import APIRouter

from app.algorithms.environmental_risk import calculate_environmental_risk
from app.models.environment import EnvironmentInput, EnvironmentRiskResult

router = APIRouter()


@router.post("/risk-score", response_model=EnvironmentRiskResult, summary="Compute environmental risk")
def score_environment(payload: EnvironmentInput) -> EnvironmentRiskResult:
    return calculate_environmental_risk(payload)
