from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import UserEntity


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_email(self, email: str) -> UserEntity | None:
        statement = select(UserEntity).where(UserEntity.email == email)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: UUID) -> UserEntity | None:
        return await self.session.get(UserEntity, user_id)

    async def create(
        self,
        email: str,
        hashed_password: str,
        role: str = "engineer",
        auth_method: str = "local",
    ) -> UserEntity:
        user = UserEntity(email=email, hashed_password=hashed_password, role=role, auth_method=auth_method)
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user
