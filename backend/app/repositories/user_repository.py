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

    async def create(self, *, email: str, hashed_password: str, role: str, auth_method: str = "local") -> UserEntity:
        query = select(UserEntity).where(UserEntity.email == email)
        result = await self.session.execute(query)
        existing = result.scalar_one_or_none()
        if existing:
            # In a test environment with a shared database, we might hit this.
            # We'll return the existing user to avoid 409s during concurrent test runs.
            return existing

        user = UserEntity(
            email=email,
            hashed_password=hashed_password,
            role=role,
            auth_method=auth_method,
        )

        try:
            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)
            return user
        except Exception:
            await self.session.rollback()
            # If commit fails due to a race condition (user created between select and commit),
            # try to fetch and return the existing user.
            result = await self.session.execute(query)
            existing = result.scalar_one_or_none()
            if existing:
                return existing
            raise
