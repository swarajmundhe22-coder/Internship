from functools import lru_cache
import os

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "The On Looker API"
    app_version: str = "0.1.0"
    environment: str = Field(default="development")
    api_v1_prefix: str = "/api/v1"
    auto_initialize_db: bool = Field(default=True)

    # PostgreSQL connection string for async SQLAlchemy engine.
    database_url: str = Field(
        default="postgresql+asyncpg://onlooker:onlooker@localhost:5432/onlooker"
    )
    db_pool_size: int = Field(default=max(4, (os.cpu_count() or 2) * 2), ge=1)
    db_pool_max_overflow: int = Field(default=max(2, os.cpu_count() or 2), ge=0)
    db_pool_timeout_seconds: int = Field(default=5, ge=1)
    db_pool_max_lifetime_seconds: int = Field(default=30, ge=1)
    db_pool_leak_detection_threshold_seconds: int = Field(default=5, ge=1)

    redis_url: str | None = Field(default=None)
    redis_readthrough_hard_ttl_seconds: int = Field(default=30, ge=1)
    redis_readthrough_refresh_ttl_ms: int = Field(default=10, ge=1)
    redis_target_hit_rate: float = Field(default=0.95, ge=0, le=1)

    audit_async_enabled: bool = Field(default=True)
    audit_batch_queue_size: int = Field(default=10000, ge=100)
    kafka_async_batching_enabled: bool = Field(default=False)
    kafka_batch_size_bytes: int = Field(default=65536, ge=1024)
    kafka_linger_ms: int = Field(default=5, ge=0)

    jwt_secret_key: str = Field(default="change-me-in-production")
    jwt_algorithm: str = Field(default="HS256")
    jwt_expire_minutes: int = Field(default=60)
    jwt_refresh_expire_minutes: int = Field(default=60 * 24 * 14)
    jwt_issuer: str = Field(default="the-on-looker")
    auth_session_active_cache_ttl_seconds: float = Field(default=5.0, ge=0)
    auth_session_active_cache_max_entries: int = Field(default=10000, ge=100)
    auth_login_verify_cache_ttl_seconds: float = Field(default=15.0, ge=0)
    auth_login_verify_cache_max_entries: int = Field(default=20000, ge=100)
    registration_otp_expire_minutes: int = Field(default=10)
    registration_otp_max_attempts: int = Field(default=5)
    login_otp_expire_minutes: int = Field(default=5)
    sso_allowed_domains: str = Field(default="example.com,company.com")
    smtp_host: str | None = Field(default=None)
    smtp_port: int = Field(default=587)
    smtp_username: str | None = Field(default=None)
    smtp_password: str | None = Field(default=None)
    smtp_from_email: str | None = Field(default=None)
    smtp_use_tls: bool = Field(default=True)
    otp_admin_notification_email: str | None = Field(default=None)
    nvidia_api_key: str | None = Field(default=None)
    paypal_client_id: str | None = Field(default=None)
    paypal_secret: str | None = Field(default=None)
    paypal_webhook_secret: str | None = Field(default=None)
    report_cache_ttl_seconds: int = Field(default=120)
    pdf_retry_attempts: int = Field(default=3)
    webhook_retry_attempts: int = Field(default=3)
    webhook_retry_base_delay_ms: int = Field(default=200)
    intelligence_rate_limit_per_minute: int = Field(default=120)
    intelligence_retry_attempts: int = Field(default=3)
    intelligence_retry_base_delay_ms: int = Field(default=300)

    model_confidence_fallback_threshold: float = Field(default=0.75, ge=0, le=1)
    model_risk_floor_score: float = Field(default=55.0, ge=0, le=100)
    recalibration_cadence_days: int = Field(default=30, ge=1)
    drift_alert_relative_threshold: float = Field(default=0.20, ge=0, le=1)

    simulation_slo_p95_ms: int = Field(default=1200, ge=100)
    simulation_slo_p99_ms: int = Field(default=2000, ge=100)
    simulation_error_budget_rate: float = Field(default=0.02, ge=0, le=1)
    simulation_slo_low_load_p99_ms: int = Field(default=100, ge=1)
    simulation_slo_medium_load_p99_ms: int = Field(default=150, ge=1)
    simulation_slo_high_load_p99_ms: int = Field(default=200, ge=1)
    simulation_slo_spike_ceiling_ms: int = Field(default=250, ge=1)
    simulation_slo_normal_load_p99_ms: int = Field(default=75, ge=1)
    simulation_slo_sustained_80_user_p99_ms: int = Field(default=100, ge=1)
    simulation_slo_sustained_80_user_error_rate: float = Field(default=0.0, ge=0, le=1)
    performance_window_seconds: int = Field(default=1800, ge=60)
    performance_max_samples: int = Field(default=50000, ge=1000)
    performance_min_samples_for_alerts: int = Field(default=50, ge=1)

    resilience_enabled: bool = Field(default=True)
    resilience_max_inflight_requests: int = Field(default=4096, ge=10)
    resilience_retry_after_seconds: int = Field(default=2, ge=1)
    resilience_protected_paths: str = Field(default="/api/v1/simulation/simulate,/api/v1/auth/login")

    circuit_breaker_window_seconds: int = Field(default=30, ge=5)
    circuit_breaker_min_requests: int = Field(default=120, ge=5)
    circuit_breaker_failure_rate_threshold: float = Field(default=0.50, ge=0.01, le=1.0)
    circuit_breaker_open_seconds: int = Field(default=15, ge=5)
    circuit_breaker_half_open_max_requests: int = Field(default=20, ge=1)
    circuit_breaker_latency_failure_threshold_ms: int = Field(default=1000, ge=1)

    prometheus_metrics_enabled: bool = Field(default=True)

    mqtt_broker_url: str | None = Field(default=None)
    mqtt_topic: str | None = Field(default=None)
    mqtt_username: str | None = Field(default=None)
    mqtt_password: str | None = Field(default=None)
    mqtt_tls_enabled: bool = Field(default=False)

    kafka_bootstrap_servers: str | None = Field(default=None)
    kafka_topic: str | None = Field(default=None)
    kafka_group_id: str = Field(default="onlooker-phase9")
    kafka_security_protocol: str = Field(default="PLAINTEXT")
    kafka_sasl_mechanism: str | None = Field(default=None)
    kafka_sasl_username: str | None = Field(default=None)
    kafka_sasl_password: str | None = Field(default=None)

    device_gateway_url: str | None = Field(default=None)
    device_gateway_api_key: str | None = Field(default=None)
    device_gateway_hmac_secret: str | None = Field(default=None)

    satellite_provider_base_url: str | None = Field(default=None)
    satellite_provider_api_key: str | None = Field(default=None)
    satellite_provider_hmac_secret: str | None = Field(default=None)
    satellite_provider_timeout_seconds: int = Field(default=10)
    satellite_provider_mock_mode: bool = Field(default=True)

    export_artifacts_dir: str = Field(default="artifacts/visualization_exports")
    export_mp4_duration_seconds: int = Field(default=8)
    demo_booking_url: str = Field(default="https://calendly.com")

    oauth_state_ttl_seconds: int = Field(default=300)
    oauth_frontend_callback_url: str = Field(default="http://localhost:3000/auth/oauth/callback")

    oauth_google_client_id: str | None = Field(default=None)
    oauth_google_client_secret: str | None = Field(default=None)
    oauth_google_redirect_uri: str | None = Field(default=None)
    oauth_google_authorize_url: str = Field(default="https://accounts.google.com/o/oauth2/v2/auth")
    oauth_google_token_url: str = Field(default="https://oauth2.googleapis.com/token")
    oauth_google_userinfo_url: str = Field(default="https://www.googleapis.com/oauth2/v3/userinfo")

    oauth_apple_client_id: str | None = Field(default=None)
    oauth_apple_client_secret: str | None = Field(default=None)
    oauth_apple_redirect_uri: str | None = Field(default=None)
    oauth_apple_authorize_url: str = Field(default="https://appleid.apple.com/auth/authorize")
    oauth_apple_token_url: str = Field(default="https://appleid.apple.com/auth/token")

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"),
        env_file_encoding="utf-8"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
