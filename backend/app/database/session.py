from __future__ import annotations

from urllib.parse import urlparse

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.core.db_pool_monitor import DbPoolMonitor
from app.core.logging import get_logger

settings = get_settings()
logger = get_logger("gifip.db.pool")
db_pool_monitor = DbPoolMonitor(
    leak_threshold_seconds=settings.db_pool_leak_detection_threshold_seconds,
)

database_scheme = urlparse(settings.database_url).scheme.lower()
engine_kwargs: dict[str, object] = {
    "echo": False,
    "future": True,
}

# SQLite is used in tests and local quickstarts where pooling knobs are not applicable.
if not database_scheme.startswith("sqlite"):
    engine_kwargs.update(
        {
            "pool_size": settings.db_pool_size,
            "max_overflow": settings.db_pool_max_overflow,
            "pool_timeout": settings.db_pool_timeout_seconds,
            "pool_recycle": settings.db_pool_max_lifetime_seconds,
            "pool_pre_ping": True,
        }
    )

engine = create_async_engine(settings.database_url, **engine_kwargs)
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


@event.listens_for(engine.sync_engine, "checkout")
def _on_checkout(_dbapi_connection, connection_record, _connection_proxy) -> None:  # type: ignore[no-untyped-def]
    db_pool_monitor.on_checkout(id(connection_record))


@event.listens_for(engine.sync_engine, "checkin")
def _on_checkin(_dbapi_connection, connection_record) -> None:  # type: ignore[no-untyped-def]
    held_for = db_pool_monitor.on_checkin(id(connection_record))
    if held_for >= settings.db_pool_leak_detection_threshold_seconds:
        logger.warning(
            "Database connection held beyond leak threshold",
            extra={
                "held_for_seconds": round(held_for, 4),
                "leak_threshold_seconds": settings.db_pool_leak_detection_threshold_seconds,
            },
        )


async def get_db_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session


def get_db_pool_metrics() -> dict[str, object]:
    return db_pool_monitor.snapshot()
