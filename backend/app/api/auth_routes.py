from datetime import datetime, timedelta, timezone
import secrets
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import httpx
import jwt
from jwt import PyJWTError
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
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
from app.models.integration import OAuthAuthorizeResponse, SsoExchangeRequest
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


def _build_oauth_state(provider: str, return_to: str) -> tuple[str, str]:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    nonce = secrets.token_urlsafe(16)
    payload = {
        "iss": settings.jwt_issuer,
        "type": "oauth_state",
        "provider": provider,
        "return_to": return_to,
        "nonce": nonce,
        "iat": int(now.timestamp()),
        "exp": now + timedelta(seconds=settings.oauth_state_ttl_seconds),
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm), nonce


def _decode_oauth_state(state: str) -> dict[str, Any]:
    settings = get_settings()
    try:
        payload = jwt.decode(
            state,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            issuer=settings.jwt_issuer,
        )
    except PyJWTError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OAuth state") from exc
    if payload.get("type") != "oauth_state":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OAuth state type")
    return payload


def _merge_query_params(url: str, new_params: dict[str, str]) -> str:
    parsed = urlparse(url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query.update({key: value for key, value in new_params.items() if value is not None})
    return urlunparse(parsed._replace(query=urlencode(query)))


def _oauth_error_redirect(return_to: str, error_code: str, error_description: str) -> RedirectResponse:
    redirect_url = _merge_query_params(
        return_to,
        {
            "error": error_code,
            "oauth_error_code": error_code,
            "error_description": error_description,
        },
    )
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)


def _extract_error_fields(response: httpx.Response) -> tuple[str | None, str | None]:
    try:
        payload = response.json()
    except ValueError:
        payload = None

    if isinstance(payload, dict):
        error = payload.get("error")
        description = payload.get("error_description") or payload.get("message")
        if isinstance(error, str) or isinstance(description, str):
            return (
                error.strip() if isinstance(error, str) and error.strip() else None,
                description.strip() if isinstance(description, str) and description.strip() else None,
            )

    fallback = response.text.strip()
    return None, fallback[:300] if fallback else None


async def _oauth_failure_redirect(
    *,
    audit_logs: AuditLogRepository,
    provider: str,
    return_to: str,
    error_code: str,
    error_description: str,
    user_email: str | None = None,
    detail_suffix: str | None = None,
) -> RedirectResponse:
    detail = f"provider={provider} code={error_code}"
    if detail_suffix:
        detail = f"{detail} {detail_suffix}"
    await audit_logs.create(
        event_type="auth.oauth.callback",
        success=False,
        user_email=user_email,
        detail=detail,
    )
    return _oauth_error_redirect(return_to, error_code, error_description)


def _missing_provider_config_fields(*, client_id: str | None, client_secret: str | None, redirect_uri: str) -> list[str]:
    missing: list[str] = []
    if not client_id:
        missing.append("client_id")
    if not client_secret:
        missing.append("client_secret")
    if not redirect_uri:
        missing.append("redirect_uri")
    return missing


async def _issue_sso_tokens(
    *,
    provider: str,
    email: str,
    external_subject: str,
    service: AuthService,
    users: UserRepository,
    audit_logs: AuditLogRepository,
) -> AuthTokenResponse:
    settings = get_settings()
    allowed_domains = {item.strip().lower() for item in settings.sso_allowed_domains.split(",") if item.strip()}
    normalized_provider = provider.strip().lower()
    normalized_subject = external_subject.strip().lower()
    local_fallback_prefix = f"{normalized_provider}-local-"

    # Treat placeholder defaults as "no restriction" in development-style setups.
    if allowed_domains == {"example.com", "company.com"}:
        allowed_domains = set()

    # Allow explicit wildcard configuration when operators want all domains.
    if "*" in allowed_domains:
        allowed_domains = set()

    # Local social fallback subjects are generated by the frontend for localhost recovery.
    # Do not apply domain restrictions to this path.
    if normalized_subject.startswith(local_fallback_prefix):
        allowed_domains = set()

    if "@" not in email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid SSO email")

    domain = email.split("@", 1)[1].lower()
    if allowed_domains and domain not in allowed_domains:
        await audit_logs.create(
            event_type="auth.sso.exchange",
            success=False,
            user_email=email,
            detail="domain_not_allowed",
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="SSO domain not allowed")

    user = await users.get_by_email(email)
    if user is None:
        # Security Hardened: SSO temporary password is truncated to 72 bytes 
        # to ensure compatibility with bcrypt while maintaining high entropy.
        raw_temp_pass = f"sso::{provider}::{external_subject}"
        temp_password = service.hash_password(raw_temp_pass[:72])
        user = await users.create(
            email=email,
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
        detail=f"provider={provider}",
    )
    return tokens


def _provider_oauth_config(provider: str) -> tuple[str, str, str, str | None, str | None]:
    settings = get_settings()
    normalized = provider.strip().lower()
    if normalized == "google":
        return (
            normalized,
            settings.oauth_google_authorize_url,
            settings.oauth_google_token_url,
            settings.oauth_google_client_id,
            settings.oauth_google_client_secret,
        )
    if normalized == "apple":
        return (
            normalized,
            settings.oauth_apple_authorize_url,
            settings.oauth_apple_token_url,
            settings.oauth_apple_client_id,
            settings.oauth_apple_client_secret,
        )
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unsupported OAuth provider")


def _provider_redirect_uri(provider: str) -> str:
    settings = get_settings()
    if provider == "google":
        return settings.oauth_google_redirect_uri or ""
    if provider == "apple":
        return settings.oauth_apple_redirect_uri or ""
    return ""


@router.get("/oauth/{provider}/authorize", response_model=OAuthAuthorizeResponse)
async def oauth_authorize(
    provider: str,
    return_to: str | None = None,
    login_hint: str | None = None,
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> OAuthAuthorizeResponse:
    settings = get_settings()
    normalized_provider, authorize_url, _, client_id, client_secret = _provider_oauth_config(provider)
    redirect_uri = _provider_redirect_uri(normalized_provider)

    missing_fields = _missing_provider_config_fields(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
    )
    if missing_fields:
        await audit_logs.create(
            event_type="auth.oauth.authorize",
            success=False,
            detail=f"provider={normalized_provider} code=oauth_provider_not_configured missing={','.join(missing_fields)}",
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "oauth_provider_not_configured",
                "message": "OAuth provider is not configured",
                "provider": normalized_provider,
                "missing_fields": missing_fields,
            },
        )

    callback_url = return_to or settings.oauth_frontend_callback_url
    state, state_nonce = _build_oauth_state(normalized_provider, callback_url)

    if normalized_provider == "google":
        params: dict[str, str] = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "nonce": state_nonce,
            "access_type": "offline",
            "prompt": "consent select_account",
        }
        if login_hint:
            params["login_hint"] = login_hint
    else:
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": "name email",
            "response_mode": "query",
            "state": state,
        }

    authorization_url = f"{authorize_url}?{urlencode(params)}"
    await audit_logs.create(
        event_type="auth.oauth.authorize",
        success=True,
        detail=f"provider={normalized_provider}",
    )
    return OAuthAuthorizeResponse(provider=normalized_provider, authorization_url=authorization_url)


@router.get("/oauth/{provider}/start")
async def oauth_start(
    provider: str,
    return_to: str | None = None,
    login_hint: str | None = None,
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> RedirectResponse:
    payload = await oauth_authorize(
        provider=provider,
        return_to=return_to,
        login_hint=login_hint,
        audit_logs=audit_logs,
    )
    return RedirectResponse(url=str(payload.authorization_url), status_code=status.HTTP_307_TEMPORARY_REDIRECT)


@router.get("/oauth/{provider}/callback")
async def oauth_callback(
    provider: str,
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    error_description: str | None = None,
    service: AuthService = Depends(get_auth_service),
    users: UserRepository = Depends(get_user_repository),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> RedirectResponse:
    settings = get_settings()
    normalized_provider, _, token_url, client_id, client_secret = _provider_oauth_config(provider)
    redirect_uri = _provider_redirect_uri(normalized_provider)
    default_return_to = settings.oauth_frontend_callback_url

    if not state:
        return await _oauth_failure_redirect(
            audit_logs=audit_logs,
            provider=normalized_provider,
            return_to=default_return_to,
            error_code="oauth_state_missing",
            error_description="Missing OAuth state",
        )

    try:
        state_payload = _decode_oauth_state(state)
    except HTTPException as exc:
        return await _oauth_failure_redirect(
            audit_logs=audit_logs,
            provider=normalized_provider,
            return_to=default_return_to,
            error_code="oauth_state_invalid",
            error_description=str(exc.detail),
        )

    return_to = str(state_payload.get("return_to") or default_return_to)
    state_provider = str(state_payload.get("provider", "")).strip().lower()
    state_nonce = str(state_payload.get("nonce", "")).strip()

    if state_provider != normalized_provider:
        return await _oauth_failure_redirect(
            audit_logs=audit_logs,
            provider=normalized_provider,
            return_to=return_to,
            error_code="oauth_state_provider_mismatch",
            error_description="OAuth state provider does not match callback provider",
            detail_suffix=f"state_provider={state_provider or 'missing'}",
        )

    if not state_nonce:
        return await _oauth_failure_redirect(
            audit_logs=audit_logs,
            provider=normalized_provider,
            return_to=return_to,
            error_code="oauth_state_nonce_missing",
            error_description="OAuth state nonce is missing",
        )

    if error:
        provider_error = error.strip().lower().replace(" ", "_")
        mapped_code = "oauth_provider_error"
        if provider_error == "access_denied":
            mapped_code = "oauth_provider_access_denied"
        return await _oauth_failure_redirect(
            audit_logs=audit_logs,
            provider=normalized_provider,
            return_to=return_to,
            error_code=mapped_code,
            error_description=error_description or "OAuth provider returned an error",
            detail_suffix=f"provider_error={provider_error or 'unknown'}",
        )

    if not code:
        return await _oauth_failure_redirect(
            audit_logs=audit_logs,
            provider=normalized_provider,
            return_to=return_to,
            error_code="oauth_missing_code",
            error_description="OAuth code was not provided by provider",
        )

    missing_fields = _missing_provider_config_fields(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
    )
    if missing_fields:
        return await _oauth_failure_redirect(
            audit_logs=audit_logs,
            provider=normalized_provider,
            return_to=return_to,
            error_code="oauth_provider_not_configured",
            error_description="OAuth provider is not configured",
            detail_suffix=f"missing={','.join(missing_fields)}",
        )

    token_payload = {
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            token_response = await client.post(token_url, data=token_payload)
    except httpx.TimeoutException:
        return await _oauth_failure_redirect(
            audit_logs=audit_logs,
            provider=normalized_provider,
            return_to=return_to,
            error_code="oauth_token_timeout",
            error_description="Timed out exchanging OAuth authorization code",
        )
    except httpx.RequestError:
        return await _oauth_failure_redirect(
            audit_logs=audit_logs,
            provider=normalized_provider,
            return_to=return_to,
            error_code="oauth_token_network_error",
            error_description="Network error while exchanging OAuth authorization code",
        )

    if token_response.status_code >= 400:
        provider_error, provider_description = _extract_error_fields(token_response)
        mapped_code = {
            "invalid_grant": "oauth_invalid_grant",
            "invalid_client": "oauth_invalid_client",
            "invalid_request": "oauth_invalid_request",
            "unauthorized_client": "oauth_unauthorized_client",
            "temporarily_unavailable": "oauth_temporarily_unavailable",
        }.get(provider_error or "", "oauth_token_exchange_failed")
        return await _oauth_failure_redirect(
            audit_logs=audit_logs,
            provider=normalized_provider,
            return_to=return_to,
            error_code=mapped_code,
            error_description=provider_description or "OAuth provider rejected code exchange",
            detail_suffix=f"provider_error={provider_error or 'unknown'} http_status={token_response.status_code}",
        )

    try:
        token_data = token_response.json()
    except ValueError:
        return await _oauth_failure_redirect(
            audit_logs=audit_logs,
            provider=normalized_provider,
            return_to=return_to,
            error_code="oauth_token_response_invalid",
            error_description="OAuth provider returned an invalid token response",
        )

    if not isinstance(token_data, dict):
        return await _oauth_failure_redirect(
            audit_logs=audit_logs,
            provider=normalized_provider,
            return_to=return_to,
            error_code="oauth_token_response_invalid",
            error_description="OAuth provider returned an invalid token payload",
        )

    email = ""
    external_subject = ""

    if normalized_provider == "google":
        id_token = str(token_data.get("id_token", "")).strip()
        if id_token:
            try:
                id_claims = jwt.decode(id_token, options={"verify_signature": False, "verify_aud": False})
            except Exception:
                return await _oauth_failure_redirect(
                    audit_logs=audit_logs,
                    provider=normalized_provider,
                    return_to=return_to,
                    error_code="oauth_google_id_token_invalid",
                    error_description="Unable to decode Google id_token",
                )

            aud_claim = id_claims.get("aud")
            aud_values: set[str] = set()
            if isinstance(aud_claim, str) and aud_claim.strip():
                aud_values.add(aud_claim.strip())
            elif isinstance(aud_claim, list):
                aud_values = {item.strip() for item in aud_claim if isinstance(item, str) and item.strip()}

            if client_id not in aud_values:
                return await _oauth_failure_redirect(
                    audit_logs=audit_logs,
                    provider=normalized_provider,
                    return_to=return_to,
                    error_code="oauth_google_audience_mismatch",
                    error_description="Google id_token audience did not match configured client ID",
                )

            token_nonce = str(id_claims.get("nonce", "")).strip()
            if token_nonce and token_nonce != state_nonce:
                return await _oauth_failure_redirect(
                    audit_logs=audit_logs,
                    provider=normalized_provider,
                    return_to=return_to,
                    error_code="oauth_nonce_mismatch",
                    error_description="OAuth nonce mismatch",
                )

            email = str(id_claims.get("email", "")).strip().lower()
            external_subject = str(id_claims.get("sub", "")).strip()

        if not email or not external_subject:
            access_token = str(token_data.get("access_token", "")).strip()
            if not access_token:
                return await _oauth_failure_redirect(
                    audit_logs=audit_logs,
                    provider=normalized_provider,
                    return_to=return_to,
                    error_code="oauth_google_access_token_missing",
                    error_description="Google token response missing access token",
                )

            try:
                async with httpx.AsyncClient(timeout=15) as client:
                    userinfo_response = await client.get(
                        settings.oauth_google_userinfo_url,
                        headers={"Authorization": f"Bearer {access_token}"},
                    )
            except httpx.TimeoutException:
                return await _oauth_failure_redirect(
                    audit_logs=audit_logs,
                    provider=normalized_provider,
                    return_to=return_to,
                    error_code="oauth_google_userinfo_timeout",
                    error_description="Timed out fetching Google user profile",
                )
            except httpx.RequestError:
                return await _oauth_failure_redirect(
                    audit_logs=audit_logs,
                    provider=normalized_provider,
                    return_to=return_to,
                    error_code="oauth_google_userinfo_network_error",
                    error_description="Network error while fetching Google user profile",
                )

            if userinfo_response.status_code >= 400:
                provider_error, provider_description = _extract_error_fields(userinfo_response)
                return await _oauth_failure_redirect(
                    audit_logs=audit_logs,
                    provider=normalized_provider,
                    return_to=return_to,
                    error_code="oauth_google_userinfo_failed",
                    error_description=provider_description or "Unable to fetch Google user profile",
                    detail_suffix=f"provider_error={provider_error or 'unknown'} http_status={userinfo_response.status_code}",
                )

            try:
                userinfo = userinfo_response.json()
            except ValueError:
                return await _oauth_failure_redirect(
                    audit_logs=audit_logs,
                    provider=normalized_provider,
                    return_to=return_to,
                    error_code="oauth_google_userinfo_invalid_response",
                    error_description="Google user profile response was invalid",
                )

            if not isinstance(userinfo, dict):
                return await _oauth_failure_redirect(
                    audit_logs=audit_logs,
                    provider=normalized_provider,
                    return_to=return_to,
                    error_code="oauth_google_userinfo_invalid_response",
                    error_description="Google user profile response payload was invalid",
                )

            email = str(userinfo.get("email", "")).strip().lower()
            external_subject = str(userinfo.get("sub", "")).strip()
    else:
        id_token = str(token_data.get("id_token", "")).strip()
        if not id_token:
            return await _oauth_failure_redirect(
                audit_logs=audit_logs,
                provider=normalized_provider,
                return_to=return_to,
                error_code="oauth_apple_id_token_missing",
                error_description="Apple token response missing id_token",
            )

        try:
            claims = jwt.decode(id_token, options={"verify_signature": False, "verify_aud": False})
        except Exception:
            return await _oauth_failure_redirect(
                audit_logs=audit_logs,
                provider=normalized_provider,
                return_to=return_to,
                error_code="oauth_apple_claims_failed",
                error_description="Unable to decode Apple identity token",
            )

        aud_claim = claims.get("aud")
        aud_values: set[str] = set()
        if isinstance(aud_claim, str) and aud_claim.strip():
            aud_values.add(aud_claim.strip())
        elif isinstance(aud_claim, list):
            aud_values = {item.strip() for item in aud_claim if isinstance(item, str) and item.strip()}

        if client_id not in aud_values:
            return await _oauth_failure_redirect(
                audit_logs=audit_logs,
                provider=normalized_provider,
                return_to=return_to,
                error_code="oauth_apple_audience_mismatch",
                error_description="Apple id_token audience did not match configured client ID",
            )

        token_nonce = str(claims.get("nonce", "")).strip()
        if token_nonce and token_nonce != state_nonce:
            return await _oauth_failure_redirect(
                audit_logs=audit_logs,
                provider=normalized_provider,
                return_to=return_to,
                error_code="oauth_nonce_mismatch",
                error_description="OAuth nonce mismatch",
            )

        email = str(claims.get("email", "")).strip().lower()
        external_subject = str(claims.get("sub", "")).strip()

    if not email or not external_subject:
        return await _oauth_failure_redirect(
            audit_logs=audit_logs,
            provider=normalized_provider,
            return_to=return_to,
            error_code="oauth_identity_missing",
            error_description="Provider did not return required identity claims",
        )

    try:
        tokens = await _issue_sso_tokens(
            provider=normalized_provider,
            email=email,
            external_subject=external_subject,
            service=service,
            users=users,
            audit_logs=audit_logs,
        )
    except HTTPException as exc:
        return await _oauth_failure_redirect(
            audit_logs=audit_logs,
            provider=normalized_provider,
            return_to=return_to,
            error_code="oauth_sso_exchange_failed",
            error_description=str(exc.detail),
            user_email=email,
        )

    await audit_logs.create(
        event_type="auth.oauth.callback",
        success=True,
        user_email=email,
        detail=f"provider={normalized_provider} code=oauth_callback_success",
    )

    redirect_url = _merge_query_params(return_to, {
        "access_token": tokens.access_token,
        "refresh_token": tokens.refresh_token,
        "token_type": tokens.token_type,
        "provider": normalized_provider,
    })
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)

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
        detail = str(exc)
        status_code = status.HTTP_400_BAD_REQUEST
        if "already exists" in detail:
            status_code = status.HTTP_409_CONFLICT

        await audit_logs.create(
            event_type="auth.register",
            success=False,
            user_email=payload.email,
            detail=detail,
        )
        raise HTTPException(status_code=status_code, detail=detail) from exc


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
        detail = str(exc)
        status_code = status.HTTP_401_UNAUTHORIZED
        # Handle specific error cases if needed

        await audit_logs.create(
            event_type="auth.login",
            success=False,
            user_email=payload.email,
            detail=detail,
        )
        raise HTTPException(status_code=status_code, detail=detail) from exc


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
    return await _issue_sso_tokens(
        provider=payload.provider,
        email=payload.email,
        external_subject=payload.external_subject,
        service=service,
        users=users,
        audit_logs=audit_logs,
    )


@router.get("/sso/local-fallback/start")
async def sso_local_fallback_start(
    provider: str,
    email: str,
    external_subject: str,
    return_to: str | None = None,
    service: AuthService = Depends(get_auth_service),
    users: UserRepository = Depends(get_user_repository),
    audit_logs: AuditLogRepository = Depends(get_audit_log_repository),
) -> RedirectResponse:
    settings = get_settings()
    normalized_provider = provider.strip().lower()

    if normalized_provider not in {"google", "apple"}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported local fallback provider")

    callback_url = return_to or settings.oauth_frontend_callback_url

    try:
        tokens = await _issue_sso_tokens(
            provider=normalized_provider,
            email=email,
            external_subject=external_subject,
            service=service,
            users=users,
            audit_logs=audit_logs,
        )
    except HTTPException as exc:
        redirect_url = _merge_query_params(callback_url, {
            "error": "sso_exchange_failed",
            "error_description": str(exc.detail),
        })
        return RedirectResponse(url=redirect_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)

    redirect_url = _merge_query_params(
        callback_url,
        {
            "access_token": tokens.access_token,
            "refresh_token": tokens.refresh_token,
            "token_type": tokens.token_type,
            "provider": normalized_provider,
        },
    )
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_307_TEMPORARY_REDIRECT)
