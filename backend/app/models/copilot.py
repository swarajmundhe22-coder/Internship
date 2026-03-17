from __future__ import annotations

from uuid import UUID

from pydantic import Field

from app.models.common import BaseDomainModel


class CopilotRequest(BaseDomainModel):
    tenant_id: UUID | None = None
    user_input: str = Field(min_length=1, max_length=8000)


class CopilotResponse(BaseDomainModel):
    response: str
    model: str
