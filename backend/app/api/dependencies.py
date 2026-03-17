from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.repositories.comparison_set_repository import ComparisonSetRepository
from app.repositories.api_token_repository import ApiTokenRepository
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.environment_repository import EnvironmentRepository
from app.repositories.consortium_repository import ConsortiumRepository
from app.repositories.deck_repository import DeckRepository
from app.repositories.dossier_repository import DossierRepository
from app.repositories.intelligence_repository import IntelligenceRepository
from app.repositories.material_repository import MaterialRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.prediction_repository import PredictionRepository
from app.repositories.report_repository import ReportRepository
from app.repositories.refresh_session_repository import RefreshSessionRepository
from app.repositories.simulation_repository import SimulationRepository
from app.repositories.tenant_repository import TenantRepository
from app.repositories.analytics_repository import AnalyticsRepository
from app.repositories.webhook_repository import WebhookRepository
from app.repositories.user_repository import UserRepository
from app.repositories.visualization_repository import VisualizationRepository


def get_material_repository(
    session: AsyncSession = Depends(get_db_session),
) -> MaterialRepository:
    return MaterialRepository(session=session)


def get_environment_repository(
    session: AsyncSession = Depends(get_db_session),
) -> EnvironmentRepository:
    return EnvironmentRepository(session=session)


def get_simulation_repository(
    session: AsyncSession = Depends(get_db_session),
) -> SimulationRepository:
    return SimulationRepository(session=session)


def get_report_repository(
    session: AsyncSession = Depends(get_db_session),
) -> ReportRepository:
    return ReportRepository(session=session)


def get_user_repository(
    session: AsyncSession = Depends(get_db_session),
) -> UserRepository:
    return UserRepository(session=session)


def get_refresh_session_repository(
    session: AsyncSession = Depends(get_db_session),
) -> RefreshSessionRepository:
    return RefreshSessionRepository(session=session)


def get_project_repository(
    session: AsyncSession = Depends(get_db_session),
) -> ProjectRepository:
    return ProjectRepository(session=session)


def get_prediction_repository(
    session: AsyncSession = Depends(get_db_session),
) -> PredictionRepository:
    return PredictionRepository(session=session)


def get_comparison_set_repository(
    session: AsyncSession = Depends(get_db_session),
) -> ComparisonSetRepository:
    return ComparisonSetRepository(session=session)


def get_audit_log_repository(
    session: AsyncSession = Depends(get_db_session),
) -> AuditLogRepository:
    return AuditLogRepository(session=session)


def get_intelligence_repository(
    session: AsyncSession = Depends(get_db_session),
) -> IntelligenceRepository:
    return IntelligenceRepository(session=session)


def get_analytics_repository(
    session: AsyncSession = Depends(get_db_session),
) -> AnalyticsRepository:
    return AnalyticsRepository(session=session)


def get_api_token_repository(
    session: AsyncSession = Depends(get_db_session),
) -> ApiTokenRepository:
    return ApiTokenRepository(session=session)


def get_webhook_repository(
    session: AsyncSession = Depends(get_db_session),
) -> WebhookRepository:
    return WebhookRepository(session=session)


def get_tenant_repository(
    session: AsyncSession = Depends(get_db_session),
) -> TenantRepository:
    return TenantRepository(session=session)


def get_visualization_repository(
    session: AsyncSession = Depends(get_db_session),
) -> VisualizationRepository:
    return VisualizationRepository(session=session)


def get_dossier_repository(
    session: AsyncSession = Depends(get_db_session),
) -> DossierRepository:
    return DossierRepository(session=session)


def get_deck_repository(
    session: AsyncSession = Depends(get_db_session),
) -> DeckRepository:
    return DeckRepository(session=session)


def get_consortium_repository(
    session: AsyncSession = Depends(get_db_session),
) -> ConsortiumRepository:
    return ConsortiumRepository(session=session)
