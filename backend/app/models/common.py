from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class BaseDomainModel(BaseModel):
    """Base model with strict validation and ORM-compat config."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)


class AuditMetadata(BaseDomainModel):
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
