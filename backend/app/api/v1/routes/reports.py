from fastapi import APIRouter

from app.models.report import ReportRead
from app.models.simulation import SimulationResult
from app.services.report_service import ReportService

router = APIRouter()
service = ReportService()


@router.post("/generate", response_model=ReportRead, summary="Generate simulation report")
def generate_report(payload: SimulationResult) -> ReportRead:
    return service.create_report(payload)
