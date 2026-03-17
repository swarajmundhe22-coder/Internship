from uuid import uuid4

from app.models.report import ReportRead
from app.models.simulation import SimulationResult


class ReportService:
    """Generates report metadata and placeholder references for report artifacts."""

    def create_report(self, simulation_result: SimulationResult) -> ReportRead:
        report_id = uuid4()
        return ReportRead(
            report_id=report_id,
            simulation_id=simulation_result.simulation_id,
            report_uri=f"s3://the-on-looker/reports/{report_id}.pdf",
            status="generated",
        )
