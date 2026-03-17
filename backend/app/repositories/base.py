from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

from app.repositories.exceptions import ConflictError, PersistenceError

EntityT = TypeVar("EntityT", bound=DeclarativeBase)
CreateSchemaT = TypeVar("CreateSchemaT", bound=BaseModel)
UpdateSchemaT = TypeVar("UpdateSchemaT", bound=BaseModel)
ReadSchemaT = TypeVar("ReadSchemaT", bound=BaseModel)


class BaseRepository(Generic[EntityT, CreateSchemaT, UpdateSchemaT, ReadSchemaT]):
    """Generic async repository with SQLAlchemy 2.0 patterns and safe error mapping."""

    def __init__(
        self,
        session: AsyncSession,
        entity_type: type[EntityT],
        read_schema: type[ReadSchemaT],
    ) -> None:
        self.session = session
        self.entity_type = entity_type
        self.read_schema = read_schema

    async def _flush_refresh(self, entity: EntityT) -> None:
        """Flush and refresh to guarantee server defaults and timestamps are available."""
        try:
            await self.session.flush()
            await self.session.refresh(entity)
        except IntegrityError as exc:
            raise ConflictError(str(exc.orig)) from exc
        except SQLAlchemyError as exc:
            raise PersistenceError(str(exc)) from exc

    async def _commit_or_rollback(self) -> None:
        try:
            await self.session.commit()
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError(str(exc.orig)) from exc
        except SQLAlchemyError as exc:
            await self.session.rollback()
            raise PersistenceError(str(exc)) from exc

    @staticmethod
    def _entity_to_read_model(entity: EntityT, read_schema: type[ReadSchemaT]) -> ReadSchemaT:
        return read_schema.model_validate(entity)

    @staticmethod
    def _payload_dict(payload: BaseModel) -> dict[str, Any]:
        return payload.model_dump(exclude_unset=True)

    @staticmethod
    def _entities_to_read_models(
        entities: Sequence[EntityT], read_schema: type[ReadSchemaT]
    ) -> list[ReadSchemaT]:
        return [read_schema.model_validate(item) for item in entities]
