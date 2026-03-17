from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import secrets
from uuid import UUID

from app.models.integration import ApiTokenCreateRequest, ApiTokenCreateResponse, ApiTokenRead
from app.repositories.api_token_repository import ApiTokenRepository


class ApiTokenService:
    def __init__(self, repository: ApiTokenRepository) -> None:
        self.repository = repository

    async def create_token(self, *, user_id: UUID, payload: ApiTokenCreateRequest) -> ApiTokenCreateResponse:
        raw_token = f"olk_{secrets.token_urlsafe(32)}"
        token_prefix = raw_token[:16]
        token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        expires_at = None
        if payload.expires_in_days is not None:
            expires_at = datetime.now(timezone.utc) + timedelta(days=payload.expires_in_days)

        entity = await self.repository.create(
            user_id=user_id,
            name=payload.name,
            token_prefix=token_prefix,
            token_hash=token_hash,
            scopes=payload.scopes,
            expires_at=expires_at,
        )
        return ApiTokenCreateResponse(
            id=entity.id,
            token=raw_token,
            token_prefix=entity.token_prefix,
            name=entity.name,
            scopes=[value for value in entity.scopes.split(",") if value],
            expires_at=entity.expires_at,
            created_at=entity.created_at,
        )

    async def list_tokens(self, *, user_id: UUID) -> list[ApiTokenRead]:
        entities = await self.repository.list_for_user(user_id)
        return [
            ApiTokenRead(
                id=entity.id,
                token_prefix=entity.token_prefix,
                name=entity.name,
                scopes=[value for value in entity.scopes.split(",") if value],
                is_active=entity.is_active,
                expires_at=entity.expires_at,
                created_at=entity.created_at,
                revoked_at=entity.revoked_at,
            )
            for entity in entities
        ]

    async def revoke_token(self, *, user_id: UUID, token_id: UUID) -> None:
        if not await self.repository.revoke(user_id=user_id, token_id=token_id):
            raise ValueError("API token not found")
