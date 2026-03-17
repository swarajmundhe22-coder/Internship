from __future__ import annotations

from datetime import datetime

from sqlalchemy import Select


def apply_created_range_filters(statement: Select, entity, created_from: datetime | None, created_to: datetime | None) -> Select:
    if created_from is not None:
        statement = statement.where(entity.created_at >= created_from)
    if created_to is not None:
        statement = statement.where(entity.created_at <= created_to)
    return statement


def apply_generated_range_filters(statement: Select, entity, created_from: datetime | None, created_to: datetime | None) -> Select:
    if created_from is not None:
        statement = statement.where(entity.generated_at >= created_from)
    if created_to is not None:
        statement = statement.where(entity.generated_at <= created_to)
    return statement
