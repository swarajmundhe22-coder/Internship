from __future__ import annotations

from datetime import datetime
from uuid import UUID

from app.models.common import BaseDomainModel


class AuditLogRead(BaseDomainModel):
    id: UUID
    event_type: str
    tenant_id: UUID | None = None
    user_id: UUID | None = None
    user_email: str | None = None
    success: bool
    detail: str | None = None
    created_at: datetime
