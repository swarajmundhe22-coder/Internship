from __future__ import annotations

import csv
from io import BytesIO, StringIO
from uuid import UUID

from openpyxl import Workbook

from app.models.pagination import PaginatedResponse, ProjectPredictionListQuery
from app.models.prediction import PredictionTimelinePoint, ProjectPredictionCreateRequest, ProjectPredictionRead
from app.repositories.prediction_repository import PredictionRepository
from app.repositories.project_repository import ProjectRepository


class PredictionService:
    def __init__(self, *, project_repository: ProjectRepository, prediction_repository: PredictionRepository) -> None:
        self.project_repository = project_repository
        self.prediction_repository = prediction_repository

    async def generate_prediction(
        self,
        *,
        user_id: UUID,
        project_id: UUID,
        payload: ProjectPredictionCreateRequest,
    ) -> ProjectPredictionRead:
        project = await self.project_repository.get_by_id_for_user(project_id=project_id, user_id=user_id)
        if project is None:
            raise ValueError("Project not found")

        simulation = None
        if payload.simulation_id is not None:
            simulation = await self.project_repository.get_project_simulation(
                project_id=project_id,
                simulation_id=payload.simulation_id,
            )
            if simulation is None:
                raise ValueError("Simulation not found in project")
        else:
            simulation = await self.project_repository.get_latest_project_simulation(project_id=project_id)

        if simulation is None:
            raise ValueError("Project has no simulations to predict")

        timeline = self._forecast_timeline(
            base_corrosion_rate=simulation.corrosion_rate_mm_per_year,
            base_lifespan=simulation.estimated_lifespan_years,
            base_risk=simulation.risk_classification,
            horizon_hours=payload.horizon_hours,
            step_hours=payload.step_hours,
        )

        model_name = "trend-v1"
        summary = self._build_summary(timeline, simulation.risk_classification)
        return await self.prediction_repository.create_prediction(
            project_id=project_id,
            simulation_id=simulation.id,
            model_name=model_name,
            horizon_hours=payload.horizon_hours,
            step_hours=payload.step_hours,
            summary=summary,
            timeline=timeline,
        )

    async def list_predictions(
        self,
        *,
        user_id: UUID,
        project_id: UUID,
        query: ProjectPredictionListQuery,
    ) -> PaginatedResponse[ProjectPredictionRead]:
        project = await self.project_repository.get_by_id_for_user(project_id=project_id, user_id=user_id)
        if project is None:
            raise ValueError("Project not found")

        return await self.prediction_repository.list_predictions(project_id=project_id, query=query)

    async def export_predictions(
        self,
        *,
        user_id: UUID,
        project_id: UUID,
        format: str,
    ) -> tuple[str, str, bytes]:
        project = await self.project_repository.get_by_id_for_user(project_id=project_id, user_id=user_id)
        if project is None:
            raise ValueError("Project not found")

        page = await self.prediction_repository.list_predictions(
            project_id=project_id,
            query=ProjectPredictionListQuery(page=1, page_size=200),
        )
        rows: list[dict[str, object]] = []
        for prediction in page.items:
            for point in prediction.timeline:
                rows.append(
                    {
                        "prediction_id": str(prediction.id),
                        "project_id": str(prediction.project_id),
                        "simulation_id": str(prediction.simulation_id) if prediction.simulation_id else "",
                        "model_name": prediction.model_name,
                        "created_at": prediction.created_at.isoformat(),
                        "offset_hours": point.offset_hours,
                        "corrosion_rate_mm_per_year": point.corrosion_rate_mm_per_year,
                        "estimated_lifespan_years": point.estimated_lifespan_years,
                        "risk_score": point.risk_score,
                        "risk_classification": point.risk_classification,
                    }
                )

        if format.lower() == "csv":
            return self._export_csv(project_id=project_id, rows=rows)
        if format.lower() in {"xlsx", "excel"}:
            return self._export_xlsx(project_id=project_id, rows=rows)
        raise ValueError("Unsupported export format")

    def _export_csv(self, *, project_id: UUID, rows: list[dict[str, object]]) -> tuple[str, str, bytes]:
        buffer = StringIO()
        fieldnames = [
            "prediction_id",
            "project_id",
            "simulation_id",
            "model_name",
            "created_at",
            "offset_hours",
            "corrosion_rate_mm_per_year",
            "estimated_lifespan_years",
            "risk_score",
            "risk_classification",
        ]
        writer = csv.DictWriter(buffer, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
        return (
            f"project-{project_id}-predictions.csv",
            "text/csv",
            buffer.getvalue().encode("utf-8"),
        )

    def _export_xlsx(self, *, project_id: UUID, rows: list[dict[str, object]]) -> tuple[str, str, bytes]:
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Predictions"
        headers = [
            "prediction_id",
            "project_id",
            "simulation_id",
            "model_name",
            "created_at",
            "offset_hours",
            "corrosion_rate_mm_per_year",
            "estimated_lifespan_years",
            "risk_score",
            "risk_classification",
        ]
        sheet.append(headers)
        for row in rows:
            sheet.append([row[key] for key in headers])

        output = BytesIO()
        workbook.save(output)
        return (
            f"project-{project_id}-predictions.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            output.getvalue(),
        )

    def _forecast_timeline(
        self,
        *,
        base_corrosion_rate: float,
        base_lifespan: float,
        base_risk: str,
        horizon_hours: int,
        step_hours: int,
    ) -> list[PredictionTimelinePoint]:
        points: list[PredictionTimelinePoint] = []
        steps = max(1, horizon_hours // step_hours)

        for index in range(steps + 1):
            offset_hours = index * step_hours
            ratio = index / max(1, steps)

            # Lightweight exponential drift approximates gradual corrosion acceleration over time.
            projected_corrosion = max(0.0, base_corrosion_rate * (1.0 + (0.18 * ratio) + (0.06 * ratio * ratio)))
            projected_lifespan = max(0.0, base_lifespan - (base_lifespan * 0.45 * ratio))
            risk_score = min(100.0, max(0.0, projected_corrosion * 420.0 + (100.0 - projected_lifespan * 6.0)))
            risk_classification = self._classify_risk(risk_score, base_risk)

            points.append(
                PredictionTimelinePoint(
                    offset_hours=offset_hours,
                    corrosion_rate_mm_per_year=projected_corrosion,
                    estimated_lifespan_years=projected_lifespan,
                    risk_score=risk_score,
                    risk_classification=risk_classification,
                )
            )

        return points

    def _classify_risk(self, risk_score: float, fallback: str) -> str:
        if risk_score >= 80:
            return "critical"
        if risk_score >= 60:
            return "high"
        if risk_score >= 35:
            return "moderate"
        if risk_score >= 15:
            return "low"
        return fallback.lower()

    def _build_summary(self, timeline: list[PredictionTimelinePoint], baseline_risk: str) -> str:
        start = timeline[0]
        end = timeline[-1]
        return (
            f"Forecast from {baseline_risk.lower()} baseline to {end.risk_classification} over "
            f"{end.offset_hours} hours. Corrosion shifts {start.corrosion_rate_mm_per_year:.4f} -> "
            f"{end.corrosion_rate_mm_per_year:.4f} mm/year."
        )
