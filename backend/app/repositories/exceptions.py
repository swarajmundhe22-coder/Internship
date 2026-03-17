from __future__ import annotations

from uuid import UUID


class RepositoryError(Exception):
    """Base exception for repository-layer failures."""


class EntityNotFoundError(RepositoryError):
    """Raised when an entity cannot be found by primary key."""

    def __init__(self, entity_name: str, entity_id: UUID) -> None:
        super().__init__(f"{entity_name} with id '{entity_id}' was not found")


class ConflictError(RepositoryError):
    """Raised when a persistence operation violates a constraint."""


class PersistenceError(RepositoryError):
    """Raised when data cannot be persisted due to database failures."""


class ConcurrencyError(RepositoryError):
    """Raised when optimistic locking detects a stale client version."""

