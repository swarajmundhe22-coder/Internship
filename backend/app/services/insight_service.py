from __future__ import annotations

from uuid import UUID

from app.models.insight import InsightAnomaly, ProjectInsightRead, ProjectInsightReportExport
from app.models.pagination import ProjectPredictionListQuery
from app.repositories.prediction_repository import PredictionRepository
from app.repositories.project_repository import ProjectRepository


class InsightService:
    def __init__(self, *, project_repository: ProjectRepository, prediction_repository: PredictionRepository) -> None:
        self.project_repository = project_repository
        self.prediction_repository = prediction_repository

    async def get_project_insights(self, *, user_id: UUID, project_id: UUID) -> ProjectInsightRead:
        project = await self.project_repository.get_by_id_for_user(project_id=project_id, user_id=user_id)
        if project is None:
            raise ValueError("Project not found")

        predictions = await self.prediction_repository.list_predictions(
            project_id=project_id,
            query=ProjectPredictionListQuery(page=1, page_size=5),
        )
        if not predictions.items:
            return ProjectInsightRead(
                project_id=project_id,
                summary="No predictive runs yet. Generate prediction playback to unlock AI insights.",
                recommendations=[
                    "Generate at least one project prediction from a saved simulation.",
                    "Run monthly prediction intervals to detect acceleration trends.",
                ],
                anomalies=[],
            )

        latest = predictions.items[0]
        first_point = latest.timeline[0]
        last_point = latest.timeline[-1]

        anomalies: list[InsightAnomaly] = []
        if last_point.risk_score >= 80:
            anomalies.append(
                InsightAnomaly(
                    code="RISK_SPIKE",
                    severity="critical",
                    message="Forecast indicates critical risk band before horizon completion.",
                )
            )
        if last_point.corrosion_rate_mm_per_year > first_point.corrosion_rate_mm_per_year * 1.2:
            anomalies.append(
                InsightAnomaly(
                    code="CORROSION_ACCELERATION",
                    severity="high",
                    message="Corrosion trend accelerates by more than 20% across the forecast window.",
                )
            )

        recommendations = [
            "Schedule targeted inspections at 30% and 60% of forecast horizon.",
            "Prioritize mitigation for assets crossing high-risk threshold in the next interval.",
            "Attach this insight package to executive report exports for audit visibility.",
        ]

        summary = (
            f"AI insight from model {latest.model_name}: risk shifts {first_point.risk_classification} to "
            f"{last_point.risk_classification} with corrosion {first_point.corrosion_rate_mm_per_year:.4f} -> "
            f"{last_point.corrosion_rate_mm_per_year:.4f} mm/year."
        )
        return ProjectInsightRead(
            project_id=project_id,
            summary=summary,
            recommendations=recommendations,
            anomalies=anomalies,
        )

    async def export_insight_report(self, *, user_id: UUID, project_id: UUID) -> ProjectInsightReportExport:
        insight = await self.get_project_insights(user_id=user_id, project_id=project_id)
        anomalies = "\n".join([f"- [{item.severity.upper()}] {item.code}: {item.message}" for item in insight.anomalies])
        if not anomalies:
            anomalies = "- None detected"
        recommendations = "\n".join([f"- {item}" for item in insight.recommendations])

        content = (
            f"The On Looker - AI Insights Report\\n"
            f"Project: {insight.project_id}\\n"
            f"Generated: {insight.generated_at.isoformat()}\\n\\n"
            f"Summary\\n{insight.summary}\\n\\n"
            f"Recommendations\\n{recommendations}\\n\\n"
            f"Anomalies\\n{anomalies}\\n"
        )
        return ProjectInsightReportExport(
            filename=f"insights-{project_id}.txt",
            content=content,
        )
