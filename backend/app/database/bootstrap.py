from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncEngine

from app.database.base import Base
from app.database.seed import seed_baseline_data
from app.database.session import AsyncSessionLocal


async def initialize_database(engine: AsyncEngine) -> None:
    """Initialize schema for local/dev startup and apply idempotent seed records."""
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        await seed_baseline_data(session)
