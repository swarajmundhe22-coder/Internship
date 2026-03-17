from __future__ import annotations

from datetime import datetime
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=25, ge=1, le=200)


class MaterialListQuery(PaginationParams):
    created_from: datetime | None = None
    created_to: datetime | None = None


class EnvironmentListQuery(PaginationParams):
    created_from: datetime | None = None
    created_to: datetime | None = None


class SimulationListQuery(PaginationParams):
    material_id: UUID | None = None
    environment_id: UUID | None = None
    risk_level: str | None = Field(default=None, min_length=2, max_length=40)
    created_from: datetime | None = None
    created_to: datetime | None = None


class ReportListQuery(PaginationParams):
    simulation_id: UUID | None = None
    created_from: datetime | None = None
    created_to: datetime | None = None


class ProjectSimulationListQuery(PaginationParams):
    material_id: UUID | None = None
    environment_id: UUID | None = None
    risk_level: str | None = Field(default=None, min_length=2, max_length=40)
    created_from: datetime | None = None
    created_to: datetime | None = None


class ProjectReportListQuery(PaginationParams):
    simulation_id: UUID | None = None
    risk_level: str | None = Field(default=None, min_length=2, max_length=40)
    created_from: datetime | None = None
    created_to: datetime | None = None


class ProjectPredictionListQuery(PaginationParams):
    simulation_id: UUID | None = None
    created_from: datetime | None = None
    created_to: datetime | None = None


class AuditLogListQuery(PaginationParams):
    event_type: str | None = Field(default=None, min_length=3, max_length=60)
    tenant_id: UUID | None = None
    user_id: UUID | None = None
    user_email: str | None = Field(default=None, min_length=5, max_length=255)
    created_from: datetime | None = None
    created_to: datetime | None = None


class PaginatedResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    items: list[T]
    total: int
    page: int
    page_size: int
