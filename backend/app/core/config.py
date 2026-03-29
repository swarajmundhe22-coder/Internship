from functools import lru_cache

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
    jwt_secret_key: str = Field(default="change-me-in-production")
    jwt_algorithm: str = Field(default="HS256")
    jwt_expire_minutes: int = Field(default=60)
    jwt_refresh_expire_minutes: int = Field(default=60 * 24 * 14)
    jwt_issuer: str = Field(default="the-on-looker")
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

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


@lru_cache
def get_settings() -> Settings:
    return Settings()
