from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import ApiTokenEntity


class ApiTokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        *,
        user_id: UUID,
        name: str,
        token_prefix: str,
        token_hash: str,
        scopes: list[str],
        expires_at: datetime | None,
    ) -> ApiTokenEntity:
        entity = ApiTokenEntity(
            user_id=user_id,
            name=name,
            token_prefix=token_prefix,
            token_hash=token_hash,
            scopes=",".join(scopes),
            expires_at=expires_at,
        )
        self.session.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        return entity

    async def list_for_user(self, user_id: UUID) -> list[ApiTokenEntity]:
        statement = (
            select(ApiTokenEntity)
            .where(ApiTokenEntity.user_id == user_id)
            .order_by(ApiTokenEntity.created_at.desc())
        )
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def revoke(self, *, user_id: UUID, token_id: UUID) -> bool:
        entity = await self.session.get(ApiTokenEntity, token_id)
        if entity is None or entity.user_id != user_id:
            return False
        entity.is_active = False
        entity.revoked_at = datetime.now(timezone.utc)
        await self.session.commit()
        return True
