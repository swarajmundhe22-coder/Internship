from __future__ import annotations

from collections.abc import Generator
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlparse

import httpx
import jwt
import pytest
from httpx import AsyncClient

from app.core.config import get_settings


@pytest.fixture
def configured_google_oauth() -> Generator[None, None, None]:
    settings = get_settings()
    original = {
        "oauth_google_client_id": settings.oauth_google_client_id,
        "oauth_google_client_secret": settings.oauth_google_client_secret,
        "oauth_google_redirect_uri": settings.oauth_google_redirect_uri,
        "oauth_frontend_callback_url": settings.oauth_frontend_callback_url,
    }

    settings.oauth_google_client_id = "google-client-id.apps.googleusercontent.com"
    settings.oauth_google_client_secret = "google-client-secret"
    settings.oauth_google_redirect_uri = "http://localhost:8000/api/v1/auth/oauth/google/callback"
    settings.oauth_frontend_callback_url = "http://localhost:3000/auth/oauth/callback"

    try:
        yield
    finally:
        settings.oauth_google_client_id = original["oauth_google_client_id"]
        settings.oauth_google_client_secret = original["oauth_google_client_secret"]
        settings.oauth_google_redirect_uri = original["oauth_google_redirect_uri"]
        settings.oauth_frontend_callback_url = original["oauth_frontend_callback_url"]


def _query_value(url: str, key: str) -> str:
    values = parse_qs(urlparse(url).query).get(key, [])
    return values[0] if values else ""


def _decode_state_nonce(state: str) -> str:
    settings = get_settings()
    payload = jwt.decode(
        state,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
        issuer=settings.jwt_issuer,
    )
    return str(payload.get("nonce", ""))


async def _authorize_google(api_client: AsyncClient) -> tuple[str, str]:
    response = await api_client.get(
        "/api/v1/auth/oauth/google/authorize",
        params={"return_to": "http://localhost:3000/auth/oauth/callback?next=%2Fdashboard"},
    )
    assert response.status_code == 200
    authorization_url = response.json()["authorization_url"]
    state = _query_value(authorization_url, "state")
    assert state
    return authorization_url, state


@pytest.mark.asyncio
async def test_oauth_authorize_reports_missing_google_configuration(api_client: AsyncClient) -> None:
    settings = get_settings()
    original_client_id = settings.oauth_google_client_id
    original_client_secret = settings.oauth_google_client_secret
    original_redirect_uri = settings.oauth_google_redirect_uri

    settings.oauth_google_client_id = None
    settings.oauth_google_client_secret = None
    settings.oauth_google_redirect_uri = None

    try:
        response = await api_client.get("/api/v1/auth/oauth/google/authorize")
        assert response.status_code == 503
        payload = response.json()
        detail = payload.get("detail", {})
        assert detail.get("code") == "oauth_provider_not_configured"
        assert set(detail.get("missing_fields", [])) == {"client_id", "client_secret", "redirect_uri"}
    finally:
        settings.oauth_google_client_id = original_client_id
        settings.oauth_google_client_secret = original_client_secret
        settings.oauth_google_redirect_uri = original_redirect_uri


@pytest.mark.asyncio
async def test_oauth_google_callback_success_returns_valid_backend_jwt(
    api_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    configured_google_oauth: None,
) -> None:
    _, state = await _authorize_google(api_client)
    nonce = _decode_state_nonce(state)
    settings = get_settings()

    original_post = httpx.AsyncClient.post
    original_get = httpx.AsyncClient.get

    async def fake_post(*args, **kwargs):  # type: ignore[no-untyped-def]
        url = ""
        if len(args) >= 2:
            url = str(args[1])
        elif "url" in kwargs:
            url = str(kwargs["url"])

        if url == settings.oauth_google_token_url:
            request = httpx.Request("POST", url)
            id_token = jwt.encode(
                {
                    "iss": "https://accounts.google.com",
                    "sub": "google-subject-123",
                    "email": "prod.user@example.com",
                    "aud": settings.oauth_google_client_id,
                    "nonce": nonce,
                    "exp": int((datetime.now(timezone.utc) + timedelta(minutes=10)).timestamp()),
                },
                "google-test-key",
                algorithm="HS256",
            )
            return httpx.Response(
                status_code=200,
                request=request,
                json={
                    "access_token": "google-access-token",
                    "id_token": id_token,
                    "token_type": "Bearer",
                },
            )

        return await original_post(*args, **kwargs)

    async def fake_get(*args, **kwargs):  # type: ignore[no-untyped-def]
        url = ""
        if len(args) >= 2:
            url = str(args[1])
        elif "url" in kwargs:
            url = str(kwargs["url"])

        if url == settings.oauth_google_userinfo_url:
            raise AssertionError("Google userinfo should not be called when id_token claims are complete")
        return await original_get(*args, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)
    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)

    callback = await api_client.get(
        "/api/v1/auth/oauth/google/callback",
        params={"state": state, "code": "auth-code"},
        follow_redirects=False,
    )
    assert callback.status_code == 307
    location = callback.headers["location"]
    assert "access_token=" in location

    access_token = _query_value(location, "access_token")
    refresh_token = _query_value(location, "refresh_token")
    assert access_token
    assert refresh_token

    claims = jwt.decode(
        access_token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
        issuer=settings.jwt_issuer,
    )
    assert claims["email"] == "prod.user@example.com"
    assert claims["type"] == "access"


@pytest.mark.asyncio
async def test_oauth_google_callback_handles_invalid_grant(
    api_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    configured_google_oauth: None,
) -> None:
    _, state = await _authorize_google(api_client)
    settings = get_settings()

    original_post = httpx.AsyncClient.post

    async def fake_post(*args, **kwargs):  # type: ignore[no-untyped-def]
        url = ""
        if len(args) >= 2:
            url = str(args[1])
        elif "url" in kwargs:
            url = str(kwargs["url"])

        if url == settings.oauth_google_token_url:
            request = httpx.Request("POST", url)
            return httpx.Response(
                status_code=400,
                request=request,
                json={
                    "error": "invalid_grant",
                    "error_description": "Token has been expired or revoked",
                },
            )

        return await original_post(*args, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

    callback = await api_client.get(
        "/api/v1/auth/oauth/google/callback",
        params={"state": state, "code": "auth-code"},
        follow_redirects=False,
    )

    assert callback.status_code == 307
    location = callback.headers["location"]
    assert _query_value(location, "oauth_error_code") == "oauth_invalid_grant"


@pytest.mark.asyncio
async def test_oauth_google_callback_handles_token_exchange_timeout(
    api_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
    configured_google_oauth: None,
) -> None:
    _, state = await _authorize_google(api_client)
    settings = get_settings()

    original_post = httpx.AsyncClient.post

    async def fake_post(*args, **kwargs):  # type: ignore[no-untyped-def]
        url = ""
        if len(args) >= 2:
            url = str(args[1])
        elif "url" in kwargs:
            url = str(kwargs["url"])

        if url == settings.oauth_google_token_url:
            raise httpx.ReadTimeout("Token exchange timed out")

        return await original_post(*args, **kwargs)

    monkeypatch.setattr(httpx.AsyncClient, "post", fake_post)

    callback = await api_client.get(
        "/api/v1/auth/oauth/google/callback",
        params={"state": state, "code": "auth-code"},
        follow_redirects=False,
    )

    assert callback.status_code == 307
    location = callback.headers["location"]
    assert _query_value(location, "oauth_error_code") == "oauth_token_timeout"


@pytest.mark.asyncio
async def test_oauth_google_callback_rejects_state_provider_mismatch(
    api_client: AsyncClient,
    configured_google_oauth: None,
) -> None:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    forged_state = jwt.encode(
        {
            "iss": settings.jwt_issuer,
            "type": "oauth_state",
            "provider": "apple",
            "return_to": "http://localhost:3000/auth/oauth/callback",
            "nonce": "state-mismatch-nonce",
            "iat": int(now.timestamp()),
            "exp": now + timedelta(minutes=5),
        },
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    callback = await api_client.get(
        "/api/v1/auth/oauth/google/callback",
        params={"state": forged_state, "code": "auth-code"},
        follow_redirects=False,
    )

    assert callback.status_code == 307
    location = callback.headers["location"]
    assert _query_value(location, "oauth_error_code") == "oauth_state_provider_mismatch"
