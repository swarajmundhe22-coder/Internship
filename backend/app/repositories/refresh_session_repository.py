from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import RefreshSessionEntity


class RefreshSessionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, user_id: UUID, token_jti: str, expires_at: datetime) -> RefreshSessionEntity:
        entity = RefreshSessionEntity(user_id=user_id, token_jti=token_jti, expires_at=expires_at)
        self.session.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        return entity

    async def get_by_jti(self, token_jti: str) -> RefreshSessionEntity | None:
        statement = select(RefreshSessionEntity).where(RefreshSessionEntity.token_jti == token_jti)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_id(self, session_id: UUID) -> RefreshSessionEntity | None:
        statement = select(RefreshSessionEntity).where(RefreshSessionEntity.id == session_id)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def rotate(self, session_id: UUID, token_jti: str, expires_at: datetime) -> RefreshSessionEntity | None:
        statement = select(RefreshSessionEntity).where(RefreshSessionEntity.id == session_id)
        result = await self.session.execute(statement)
        entity = result.scalar_one_or_none()
        if entity is None:
            return None

        entity.token_jti = token_jti
        entity.expires_at = expires_at
        entity.revoked_at = None
        await self.session.commit()
        await self.session.refresh(entity)
        return entity

    async def revoke_by_jti(self, token_jti: str) -> bool:
        entity = await self.get_by_jti(token_jti)
        if entity is None:
            return False
        entity.revoked_at = datetime.now(timezone.utc)
        await self.session.commit()
        return True

    async def is_active(self, token_jti: str) -> bool:
        entity = await self.get_by_jti(token_jti)
        if entity is None:
            return False
        return entity.revoked_at is None and self._is_future(entity.expires_at)

    async def is_session_active(self, session_id: UUID) -> bool:
        entity = await self.get_by_id(session_id)
        if entity is None:
            return False
        return entity.revoked_at is None and self._is_future(entity.expires_at)

    def _is_future(self, value: datetime) -> bool:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value > datetime.now(timezone.utc)
