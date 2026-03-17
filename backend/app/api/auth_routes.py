from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID

from app.api.dependencies import get_audit_log_repository, get_refresh_session_repository, get_user_repository
from app.core.config import get_settings
from app.models.auth import (
    AuthTokenResponse,
    LoginOtpRequest,
    LoginOtpVerifyRequest,
    LogoutRequest,
    RegistrationOtpChallengeResponse,
    RegistrationOtpRequest,
    RegistrationOtpVerifyRequest,
    RefreshTokenRequest,
    UserRole,
    UserLoginRequest,
    UserRegisterRequest,
)
from app.models.integration import SsoExchangeRequest
from app.repositories.audit_log_repository import AuditLogRepository
from app.repositories.refresh_session_repository import RefreshSessionRepository
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


def get_auth_service(
    repository: UserRepository = Depends(get_user_repository),
    refresh_repository: RefreshSessionRepository = Depends(get_refresh_session_repository),
) -> AuthService:
    return AuthService(repository=repository, refresh_repository=refresh_repository)


@router.post("/register/request-otp", response_model=RegistrationOtpChallengeResponse)
async def request_registration_otp(
    payload: RegistrationOtpRequest,
    service: AuthService = Depends(get_auth_service),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> RegistrationOtpChallengeResponse:
    try:
        challenge = await service.request_registration_otp(payload.email, payload.password, payload.role)
        await audit_logs.create(
            event_type="auth.register.otp.request",
            success=True,
            user_email=payload.email,
            detail=f"expires_in={challenge.expires_in_seconds}s",
        )
        return challenge
    except ValueError as exc:
        await audit_logs.create(
            event_type="auth.register.otp.request",
            success=False,
            user_email=payload.email,
            detail=str(exc),
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/register/verify-otp", response_model=AuthTokenResponse)
async def verify_registration_otp(
    payload: RegistrationOtpVerifyRequest,
    service: AuthService = Depends(get_auth_service),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> AuthTokenResponse:
    try:
        tokens = await service.verify_registration_otp(payload.email, payload.otp)
        principal = service.decode_access_token(tokens.access_token)
        await audit_logs.create(
            event_type="auth.register.otp.verify",
            success=True,
            user_id=principal.user_id,
            user_email=principal.email,
            detail=f"role={principal.role.value}",
        )
        return tokens
    except ValueError as exc:
        await audit_logs.create(
            event_type="auth.register.otp.verify",
            success=False,
            user_email=payload.email,
            detail=str(exc),
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/register", response_model=AuthTokenResponse)
async def register(
    payload: UserRegisterRequest,
    service: AuthService = Depends(get_auth_service),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> AuthTokenResponse:
    try:
        tokens = await service.register(payload.email, payload.password, payload.role)
        principal = service.decode_access_token(tokens.access_token)
        await audit_logs.create(
            event_type="auth.register",
            success=True,
            user_id=principal.user_id,
            user_email=principal.email,
            detail=f"role={principal.role.value}",
        )
        return tokens
    except ValueError as exc:
        await audit_logs.create(
            event_type="auth.register",
            success=False,
            user_email=payload.email,
            detail=str(exc),
        )
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post("/login", response_model=AuthTokenResponse)
async def login(
    payload: UserLoginRequest,
    service: AuthService = Depends(get_auth_service),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> AuthTokenResponse:
    try:
        tokens = await service.login(payload.email, payload.password)
        principal = service.decode_access_token(tokens.access_token)
        await audit_logs.create(
            event_type="auth.login",
            success=True,
            user_id=principal.user_id,
            user_email=principal.email,
            detail=f"role={principal.role.value}",
        )
        return tokens
    except ValueError as exc:
        await audit_logs.create(
            event_type="auth.login",
            success=False,
            user_email=payload.email,
            detail=str(exc),
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


@router.post("/login/request-otp", response_model=RegistrationOtpChallengeResponse)
async def request_login_otp(
    payload: LoginOtpRequest,
    service: AuthService = Depends(get_auth_service),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> RegistrationOtpChallengeResponse:
    try:
        challenge = await service.request_login_otp(payload.email, payload.password)
        await audit_logs.create(
            event_type="auth.login.otp.request",
            success=True,
            user_email=payload.email,
            detail=f"expires_in={challenge.expires_in_seconds}s",
        )
        return challenge
    except ValueError as exc:
        await audit_logs.create(
            event_type="auth.login.otp.request",
            success=False,
            user_email=payload.email,
            detail=str(exc),
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


@router.post("/login/verify-otp", response_model=AuthTokenResponse)
async def verify_login_otp(
    payload: LoginOtpVerifyRequest,
    service: AuthService = Depends(get_auth_service),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> AuthTokenResponse:
    try:
        tokens = await service.verify_login_otp(payload.email, payload.otp)
        principal = service.decode_access_token(tokens.access_token)
        await audit_logs.create(
            event_type="auth.login.otp.verify",
            success=True,
            user_id=principal.user_id,
            user_email=principal.email,
            detail=f"role={principal.role.value}",
        )
        return tokens
    except ValueError as exc:
        await audit_logs.create(
            event_type="auth.login.otp.verify",
            success=False,
            user_email=payload.email,
            detail=str(exc),
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


@router.post("/refresh", response_model=AuthTokenResponse)
async def refresh_tokens(
    payload: RefreshTokenRequest,
    service: AuthService = Depends(get_auth_service),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> AuthTokenResponse:
    try:
        tokens = await service.refresh(payload.refresh_token)
        principal = service.decode_access_token(tokens.access_token)
        await audit_logs.create(
            event_type="auth.refresh",
            success=True,
            user_id=principal.user_id,
            user_email=principal.email,
            detail="rotated",
        )
        return tokens
    except ValueError as exc:
        await audit_logs.create(
            event_type="auth.refresh",
            success=False,
            detail=str(exc),
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


@router.post("/logout")
async def logout(
    payload: LogoutRequest,
    service: AuthService = Depends(get_auth_service),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> dict[str, str]:
    try:
        claims = service.decode_token_claims(payload.refresh_token, expected_type="refresh")
        await service.logout(payload.refresh_token)
        await audit_logs.create(
            event_type="auth.logout",
            success=True,
            user_id=UUID(str(claims["sub"])),
            user_email=str(claims.get("email", "")) or None,
            detail="session_revoked",
        )
        return {"status": "logged_out"}
    except ValueError as exc:
        await audit_logs.create(
            event_type="auth.logout",
            success=False,
            detail=str(exc),
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc


@router.post("/sso/exchange", response_model=AuthTokenResponse)
async def sso_exchange(
    payload: SsoExchangeRequest,
    service: AuthService = Depends(get_auth_service),
    users: UserRepository = Depends(get_user_repository),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> AuthTokenResponse:
    settings = get_settings()
    allowed_domains = {item.strip().lower() for item in settings.sso_allowed_domains.split(",") if item.strip()}
    if "@" not in payload.email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid SSO email")

    domain = payload.email.split("@", 1)[1].lower()
    if allowed_domains and domain not in allowed_domains:
        await audit_logs.create(
            event_type="auth.sso.exchange",
            success=False,
            user_email=payload.email,
            detail="domain_not_allowed",
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="SSO domain not allowed")

    user = await users.get_by_email(payload.email)
    if user is None:
        temp_password = service.hash_password(f"sso::{payload.provider}::{payload.external_subject}")
        user = await users.create(
            email=payload.email,
            hashed_password=temp_password,
            role="engineer",
            auth_method="sso",
        )

    tokens = await service.issue_tokens(user_id=user.id, email=user.email, role=UserRole(user.role))
    await audit_logs.create(
        event_type="auth.sso.exchange",
        success=True,
        user_id=user.id,
        user_email=user.email,
        detail=f"provider={payload.provider}",
    )
    return tokens
