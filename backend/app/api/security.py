from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.api.dependencies import get_refresh_session_repository, get_user_repository
from app.models.auth import AuthPrincipal, UserRole
from app.repositories.refresh_session_repository import RefreshSessionRepository
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    user_repository: UserRepository = Depends(get_user_repository),
    refresh_repository: RefreshSessionRepository = Depends(get_refresh_session_repository),
) -> AuthPrincipal:
    auth_service = AuthService(user_repository, refresh_repository=refresh_repository)
    try:
        principal = auth_service.decode_access_token(credentials.credentials)
        if not await refresh_repository.is_session_active(principal.session_id):
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
