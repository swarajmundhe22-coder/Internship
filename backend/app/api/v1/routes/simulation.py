from fastapi import APIRouter

from app.models.simulation import SimulationRequest, SimulationResult
from app.services.simulation_service import SimulationService

router = APIRouter()
service = SimulationService()


@router.post("/run", response_model=SimulationResult, summary="Run corrosion simulation")
def run_simulation(payload: SimulationRequest) -> SimulationResult:
    return service.run_simulation(payload)
