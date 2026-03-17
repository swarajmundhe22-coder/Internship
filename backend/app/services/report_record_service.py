from uuid import UUID

from app.models.pagination import PaginatedResponse, ReportListQuery
from app.models.report import ReportCreate, ReportRecordRead, ReportUpdate
from app.repositories.report_repository import ReportRepository


class ReportRecordService:
    """Report metadata service for persistence-oriented operations."""

    def __init__(self, repository: ReportRepository) -> None:
        self.repository = repository

    async def create_report(self, payload: ReportCreate) -> ReportRecordRead:
        return await self.repository.create(payload)

    async def get_report(self, report_id: UUID) -> ReportRecordRead:
        return await self.repository.get_by_id(report_id)

    async def list_reports(
        self,
        query: ReportListQuery,
    ) -> PaginatedResponse[ReportRecordRead]:
        return await self.repository.list_paginated(query)

    async def update_report(self, report_id: UUID, payload: ReportUpdate) -> ReportRecordRead:
        return await self.repository.update(report_id, payload)

    async def delete_report(self, report_id: UUID) -> None:
        await self.repository.delete(report_id)
