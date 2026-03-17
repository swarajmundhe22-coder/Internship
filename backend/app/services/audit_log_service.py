from __future__ import annotations

from app.models.audit import AuditLogRead
from app.models.pagination import AuditLogListQuery, PaginatedResponse
from app.repositories.audit_log_repository import AuditLogRepository


class AuditLogService:
    def __init__(self, repository: AuditLogRepository) -> None:
        self.repository = repository

    async def list_logs(self, query: AuditLogListQuery) -> PaginatedResponse[AuditLogRead]:
        return await self.repository.list_paginated(query)
