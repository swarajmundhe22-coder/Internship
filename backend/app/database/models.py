from datetime import datetime, timezone
import uuid

from sqlalchemy import Boolean, CheckConstraint, DateTime, Float, ForeignKey, Index, Integer, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class MaterialEntity(Base):
    __tablename__ = "materials"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    alloy_group: Mapped[str] = mapped_column(String(120), nullable=False)
    density_kg_m3: Mapped[float] = mapped_column(Float, nullable=False)
    electrochemical_potential_v: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    __table_args__ = (
        UniqueConstraint("name", name="uq_materials_name"),
        CheckConstraint("density_kg_m3 > 0", name="ck_material_density_positive"),
        Index("ix_materials_name", "name"),
    )


class EnvironmentEntity(Base):
    __tablename__ = "environment"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    profile_name: Mapped[str] = mapped_column(String(80), nullable=False)
    temperature_c: Mapped[float] = mapped_column(Float, nullable=False)
    relative_humidity_pct: Mapped[float] = mapped_column(Float, nullable=False)
    chloride_ppm: Mapped[float] = mapped_column(Float, nullable=False)
    ph: Mapped[float] = mapped_column(Float, nullable=False)
    dissolved_oxygen_mg_l: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    __table_args__ = (
        UniqueConstraint("profile_name", name="uq_environment_profile_name"),
        CheckConstraint("relative_humidity_pct >= 0 AND relative_humidity_pct <= 100", name="ck_environment_rh_range"),
        CheckConstraint("ph >= 0 AND ph <= 14", name="ck_environment_ph_range"),
        CheckConstraint("chloride_ppm >= 0", name="ck_environment_chloride_nonnegative"),
        CheckConstraint("dissolved_oxygen_mg_l >= 0", name="ck_environment_do_nonnegative"),
        Index("ix_environment_profile_name", "profile_name"),
        Index("ix_environment_created_at", "created_at"),
    )


class SimulationEntity(Base):
    __tablename__ = "simulation"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    material_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("materials.id", ondelete="RESTRICT"), nullable=False
    )
    environment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("environment.id", ondelete="RESTRICT"), nullable=False
    )
    exposed_area_m2: Mapped[float] = mapped_column(Float, nullable=False)
    exposure_time_hours: Mapped[float] = mapped_column(Float, nullable=False)
    corrosion_rate_mm_per_year: Mapped[float] = mapped_column(Float, nullable=False)
    estimated_lifespan_years: Mapped[float] = mapped_column(Float, nullable=False)
    accuracy_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_classification: Mapped[str] = mapped_column(String(40), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    __table_args__ = (
        CheckConstraint("exposed_area_m2 > 0", name="ck_simulation_area_positive"),
        CheckConstraint("exposure_time_hours > 0", name="ck_simulation_time_positive"),
        CheckConstraint("corrosion_rate_mm_per_year >= 0", name="ck_simulation_corrosion_nonnegative"),
        CheckConstraint("estimated_lifespan_years >= 0", name="ck_simulation_lifespan_nonnegative"),
        CheckConstraint(
            "accuracy_score IS NULL OR (accuracy_score >= 0 AND accuracy_score <= 1)",
            name="ck_simulation_accuracy_score_range",
        ),
        CheckConstraint("version > 0", name="ck_simulation_version_positive"),
        Index("ix_simulation_material_id", "material_id"),
        Index("ix_simulation_environment_id", "environment_id"),
        Index("ix_simulation_risk_classification", "risk_classification"),
        Index("ix_simulation_created_at", "created_at"),
    )


class ReportEntity(Base):
    __tablename__ = "reports"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    simulation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("simulation.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(30), default="pending", nullable=False)
    report_uri: Mapped[str] = mapped_column(Text, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

    __table_args__ = (
        CheckConstraint("version > 0", name="ck_reports_version_positive"),
        Index("ix_reports_simulation_id", "simulation_id"),
        Index("ix_reports_generated_at", "generated_at"),
        Index("ix_reports_status", "status"),
    )


class UserEntity(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="engineer")
    auth_method: Mapped[str] = mapped_column(String(30), nullable=False, default="local")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    __table_args__ = (Index("ix_users_email", "email"),)


class RefreshSessionEntity(Base):
    __tablename__ = "refresh_sessions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    token_jti: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    __table_args__ = (
        Index("ix_refresh_sessions_user_id", "user_id"),
        Index("ix_refresh_sessions_token_jti", "token_jti"),
    )


class ProjectEntity(Base):
    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    metadata_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    __table_args__ = (
        Index("ix_projects_user_id", "user_id"),
        Index("ix_projects_tenant_id", "tenant_id"),
    )


class TenantEntity(Base):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    org_name: Mapped[str] = mapped_column(String(180), nullable=False, unique=True)
    subscription_tier: Mapped[str] = mapped_column(String(40), nullable=False, default="free")
    subscription_status: Mapped[str] = mapped_column(String(40), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    __table_args__ = (
        Index("ix_tenants_org_name", "org_name"),
        Index("ix_tenants_subscription_tier", "subscription_tier"),
        Index("ix_tenants_subscription_status", "subscription_status"),
    )


class TenantUserEntity(Base):
    __tablename__ = "tenant_users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(30), nullable=False, default="viewer")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    __table_args__ = (
        UniqueConstraint("tenant_id", "user_id", name="uq_tenant_user"),
        Index("ix_tenant_users_tenant_id", "tenant_id"),
        Index("ix_tenant_users_user_id", "user_id"),
    )


class TenantSimulationEntity(Base):
    __tablename__ = "tenant_simulations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    simulation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("simulation.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    __table_args__ = (
        UniqueConstraint("tenant_id", "simulation_id", name="uq_tenant_simulation"),
        Index("ix_tenant_simulations_tenant_id", "tenant_id"),
        Index("ix_tenant_simulations_simulation_id", "simulation_id"),
    )


class ProjectSimulationEntity(Base):
    __tablename__ = "project_simulations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    simulation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("simulation.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    __table_args__ = (
        UniqueConstraint("project_id", "simulation_id", name="uq_project_simulation"),
        Index("ix_project_simulations_project_id", "project_id"),
        Index("ix_project_simulations_simulation_id", "simulation_id"),
        Index("ix_project_simulations_created_at", "created_at"),
    )


class ProjectPredictionEntity(Base):
    __tablename__ = "project_predictions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    simulation_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("simulation.id", ondelete="SET NULL"), nullable=True
    )
    model_name: Mapped[str] = mapped_column(String(80), nullable=False)
    horizon_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    step_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    timeline_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    __table_args__ = (
        CheckConstraint("horizon_hours > 0", name="ck_project_predictions_horizon_positive"),
        CheckConstraint("step_hours > 0", name="ck_project_predictions_step_positive"),
        Index("ix_project_predictions_project_id", "project_id"),
        Index("ix_project_predictions_simulation_id", "simulation_id"),
        Index("ix_project_predictions_created_at", "created_at"),
    )


class ApiTokenEntity(Base):
    __tablename__ = "api_tokens"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    token_prefix: Mapped[str] = mapped_column(String(32), nullable=False)
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    scopes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_api_tokens_user_id", "user_id"),
        Index("ix_api_tokens_created_at", "created_at"),
        Index("ix_api_tokens_is_active", "is_active"),
    )


class WebhookSubscriptionEntity(Base):
    __tablename__ = "webhook_subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    target_url: Mapped[str] = mapped_column(Text, nullable=False)
    signing_secret: Mapped[str] = mapped_column(String(128), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    __table_args__ = (
        Index("ix_webhook_subscriptions_user_id", "user_id"),
        Index("ix_webhook_subscriptions_event_type", "event_type"),
        Index("ix_webhook_subscriptions_is_active", "is_active"),
    )


class WebhookDeliveryLogEntity(Base):
    __tablename__ = "webhook_delivery_logs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    webhook_subscription_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("webhook_subscriptions.id", ondelete="CASCADE"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(80), nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    first_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    __table_args__ = (
        CheckConstraint("attempt_count >= 0", name="ck_webhook_delivery_attempt_count_nonnegative"),
        CheckConstraint("max_attempts > 0", name="ck_webhook_delivery_max_attempts_positive"),
        Index("ix_webhook_delivery_logs_subscription_id", "webhook_subscription_id"),
        Index("ix_webhook_delivery_logs_event_type", "event_type"),
        Index("ix_webhook_delivery_logs_created_at", "created_at"),
        Index("ix_webhook_delivery_logs_success", "success"),
    )


class AuditLogEntity(Base):
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    event_type: Mapped[str] = mapped_column(String(60), nullable=False)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    user_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    success: Mapped[bool] = mapped_column(nullable=False, default=True)
    detail: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    __table_args__ = (
        Index("ix_audit_logs_event_type", "event_type"),
        Index("ix_audit_logs_tenant_id", "tenant_id"),
        Index("ix_audit_logs_user_id", "user_id"),
        Index("ix_audit_logs_created_at", "created_at"),
    )


class IoTDataEntity(Base):
    __tablename__ = "iot_data"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    sensor_id: Mapped[str] = mapped_column(String(120), nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    __table_args__ = (
        Index("ix_iot_data_tenant_id", "tenant_id"),
        Index("ix_iot_data_sensor_id", "sensor_id"),
        Index("ix_iot_data_created_at", "created_at"),
    )


class SatelliteDataEntity(Base):
    __tablename__ = "satellite_data"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    region: Mapped[str] = mapped_column(String(160), nullable=False)
    imagery_source: Mapped[str] = mapped_column(String(120), nullable=False)
    metadata_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    __table_args__ = (
        Index("ix_satellite_data_tenant_id", "tenant_id"),
        Index("ix_satellite_data_region", "region"),
        Index("ix_satellite_data_source", "imagery_source"),
        Index("ix_satellite_data_created_at", "created_at"),
    )


class AtlasEntity(Base):
    __tablename__ = "atlas"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    region: Mapped[str] = mapped_column(String(160), nullable=False)
    atlas_key: Mapped[str] = mapped_column(String(80), nullable=False, default="risk_overlay")
    export_type: Mapped[str] = mapped_column(String(32), nullable=False)
    metadata_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    __table_args__ = (
        Index("ix_atlas_tenant_id", "tenant_id"),
        Index("ix_atlas_region", "region"),
        Index("ix_atlas_export_type", "export_type"),
        Index("ix_atlas_created_at", "created_at"),
    )


class MaintenanceScheduleEntity(Base):
    __tablename__ = "maintenance_schedules"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    asset_id: Mapped[str] = mapped_column(String(120), nullable=False)
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    recommendation: Mapped[str] = mapped_column(String(160), nullable=False)
    metadata_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    __table_args__ = (
        CheckConstraint("risk_score >= 0 AND risk_score <= 1", name="ck_maintenance_schedules_risk_score"),
        Index("ix_maintenance_schedules_tenant_id", "tenant_id"),
        Index("ix_maintenance_schedules_asset_id", "asset_id"),
        Index("ix_maintenance_schedules_created_at", "created_at"),
    )


class AtlasExportJobEntity(Base):
    __tablename__ = "atlas_export_jobs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    region: Mapped[str] = mapped_column(String(160), nullable=False)
    export_type: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="queued")
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    output_uri: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    last_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    __table_args__ = (
        CheckConstraint("attempt_count >= 0", name="ck_atlas_export_jobs_attempt_count_nonnegative"),
        CheckConstraint("max_attempts > 0", name="ck_atlas_export_jobs_max_attempts_positive"),
        Index("ix_atlas_export_jobs_tenant_id", "tenant_id"),
        Index("ix_atlas_export_jobs_region", "region"),
        Index("ix_atlas_export_jobs_status", "status"),
        Index("ix_atlas_export_jobs_created_at", "created_at"),
    )


class DeadLetterEventEntity(Base):
    __tablename__ = "dead_letter_events"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True
    )
    event_source: Mapped[str] = mapped_column(String(80), nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    error_message: Mapped[str] = mapped_column(Text, nullable=False)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    __table_args__ = (
        CheckConstraint("retry_count >= 0", name="ck_dead_letter_events_retry_nonnegative"),
        Index("ix_dead_letter_events_tenant_id", "tenant_id"),
        Index("ix_dead_letter_events_event_source", "event_source"),
        Index("ix_dead_letter_events_created_at", "created_at"),
    )


class DossierEntity(Base):
    __tablename__ = "dossiers"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    simulation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("simulation.id", ondelete="CASCADE"), nullable=False
    )
    format: Mapped[str] = mapped_column(String(10), nullable=False)
    industry_module: Mapped[str] = mapped_column(String(80), nullable=False)
    artifact_uri: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    __table_args__ = (
        Index("ix_dossiers_tenant_id", "tenant_id"),
        Index("ix_dossiers_simulation_id", "simulation_id"),
        Index("ix_dossiers_format", "format"),
        Index("ix_dossiers_created_at", "created_at"),
    )


class DeckEntity(Base):
    __tablename__ = "decks"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    export_type: Mapped[str] = mapped_column(String(12), nullable=False)
    artifact_uri: Mapped[str] = mapped_column(Text, nullable=False)
    narrative_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    __table_args__ = (
        Index("ix_decks_tenant_id", "tenant_id"),
        Index("ix_decks_project_id", "project_id"),
        Index("ix_decks_export_type", "export_type"),
        Index("ix_decks_created_at", "created_at"),
    )


class ConsortiumMembershipEntity(Base):
    __tablename__ = "consortium_memberships"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    tier: Mapped[str] = mapped_column(String(40), nullable=False, default="global_utility")
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", name="uq_consortium_memberships_tenant_id"),
        Index("ix_consortium_memberships_tenant_id", "tenant_id"),
        Index("ix_consortium_memberships_tier", "tier"),
        Index("ix_consortium_memberships_created_at", "created_at"),
    )


class ComparisonSetEntity(Base):
    __tablename__ = "comparison_sets"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(140), nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    __table_args__ = (Index("ix_comparison_sets_project_id", "project_id"),)


class ComparisonSetSimulationEntity(Base):
    __tablename__ = "comparison_set_simulations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    comparison_set_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("comparison_sets.id", ondelete="CASCADE"), nullable=False
    )
    simulation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("simulation.id", ondelete="CASCADE"), nullable=False
    )
    ordering: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    __table_args__ = (
        UniqueConstraint("comparison_set_id", "simulation_id", name="uq_comparison_set_simulation"),
        UniqueConstraint("comparison_set_id", "ordering", name="uq_comparison_set_ordering"),
        CheckConstraint("ordering >= 0", name="ck_comparison_set_ordering_nonnegative"),
        Index("ix_comparison_set_simulations_set_id", "comparison_set_id"),
        Index("ix_comparison_set_simulations_simulation_id", "simulation_id"),
    )


class VisualizationEntity(Base):
    __tablename__ = "visualizations"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    simulation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("simulation.id", ondelete="CASCADE"), nullable=False
    )
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True
    )
    mode: Mapped[str] = mapped_column(String(20), nullable=False, default="twin")
    metadata_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    status: Mapped[str] = mapped_column(String(40), nullable=False, default="generated")
    overlay_accuracy: Mapped[float] = mapped_column(Float, nullable=False, default=0.95)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )

    __table_args__ = (
        CheckConstraint("overlay_accuracy >= 0 AND overlay_accuracy <= 1", name="ck_visualizations_overlay_accuracy"),
        Index("ix_visualizations_simulation_id", "simulation_id"),
        Index("ix_visualizations_tenant_id", "tenant_id"),
        Index("ix_visualizations_mode", "mode"),
        Index("ix_visualizations_created_at", "created_at"),
    )


class VisualizationExportEntity(Base):
    __tablename__ = "visualization_exports"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    visualization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("visualizations.id", ondelete="CASCADE"), nullable=False
    )
    tenant_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("tenants.id", ondelete="SET NULL"), nullable=True
    )
    file_type: Mapped[str] = mapped_column(String(20), nullable=False)
    file_uri: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)

    __table_args__ = (
        Index("ix_visualization_exports_visualization_id", "visualization_id"),
        Index("ix_visualization_exports_tenant_id", "tenant_id"),
        Index("ix_visualization_exports_file_type", "file_type"),
        Index("ix_visualization_exports_created_at", "created_at"),
    )
