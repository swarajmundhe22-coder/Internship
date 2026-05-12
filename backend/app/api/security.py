from __future__ import annotations

from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.api.dependencies import get_refresh_session_repository, get_user_repository
from app.core.auth_session_cache import (
    is_session_marked_active,
    mark_session_inactive,
    remember_active_session,
)
from app.models.auth import AuthPrincipal, UserRole
from app.repositories.refresh_session_repository import RefreshSessionRepository
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService

bearer_scheme = HTTPBearer()


async def _is_session_active_cached(
    refresh_repository: RefreshSessionRepository,
    session_id: UUID,
) -> bool:
    if is_session_marked_active(session_id):
        return True

    is_active = await refresh_repository.is_session_active(session_id)
    if is_active:
        remember_active_session(session_id)
    else:
        mark_session_inactive(session_id)
    return is_active


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    user_repository: UserRepository = Depends(get_user_repository),
    refresh_repository: RefreshSessionRepository = Depends(get_refresh_session_repository),
) -> AuthPrincipal:
    auth_service = AuthService(user_repository, refresh_repository=refresh_repository)
    try:
        principal = auth_service.decode_access_token(credentials.credentials)
        if not await _is_session_active_cached(refresh_repository, principal.session_id):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")
        return principal
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc


def require_roles(*roles: UserRole):
    async def _role_guard(principal: AuthPrincipal = Depends(get_current_user)) -> AuthPrincipal:
        if principal.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role privileges")
        return principal

    return _role_guard
