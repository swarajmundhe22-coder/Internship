from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from app.models.common import BaseDomainModel


class IoTIngestRequest(BaseDomainModel):
    tenant_id: UUID
    sensor_id: str = Field(min_length=2, max_length=120)
    payload: dict[str, Any]


class SatelliteIngestRequest(BaseDomainModel):
    tenant_id: UUID
    region: str = Field(min_length=2, max_length=160)
    imagery_source: str = Field(min_length=2, max_length=120)


class AtlasRequest(BaseDomainModel):
    tenant_id: UUID
    region: str = Field(min_length=2, max_length=160)
    export_type: str = Field(min_length=3, max_length=32)


class AtlasLatestQuery(BaseDomainModel):
    tenant_id: UUID
    region: str = Field(min_length=2, max_length=160)


class MaintenanceScheduleRequest(BaseDomainModel):
    tenant_id: UUID
    asset_id: str = Field(min_length=2, max_length=120)
    risk_score: float = Field(ge=0, le=1)


class IoTIngestResponse(BaseDomainModel):
    tenant_id: UUID
    sensor_id: str
    status: str = "ingested"


class SatelliteIngestResponse(BaseDomainModel):
    tenant_id: UUID
    region: str
    status: str = "imagery_ingested"


class AtlasGenerateResponse(BaseDomainModel):
    tenant_id: UUID
    region: str
    atlas: str = "risk_overlay"
    metadata: dict[str, Any]
    status: str = "generated"


class AtlasExportResponse(BaseDomainModel):
    tenant_id: UUID
    region: str
    export_type: str
    metadata: dict[str, Any]
    status: str = "exported"


class MaintenanceScheduleResponse(BaseDomainModel):
    tenant_id: UUID
    asset_id: str
    recommendation: str


class IoTConnectorEvent(BaseDomainModel):
    sensor_id: str = Field(min_length=2, max_length=120)
    payload: dict[str, Any]


class IoTStreamIngestRequest(BaseDomainModel):
    tenant_id: UUID
    connector_type: str = Field(min_length=3, max_length=30)
    events: list[IoTConnectorEvent] = Field(default_factory=list)
    topic: str | None = Field(default=None, min_length=1, max_length=240)
    max_events: int = Field(default=50, ge=1, le=500)


class IoTStreamIngestResponse(BaseDomainModel):
    tenant_id: UUID
    connector_type: str
    accepted_events: int
    dead_lettered_events: int
    status: str = "processed"


class SatelliteProviderSyncRequest(BaseDomainModel):
    tenant_id: UUID
    region: str = Field(min_length=2, max_length=160)
    provider: str = Field(min_length=2, max_length=40)


class SatelliteProviderSyncResponse(BaseDomainModel):
    tenant_id: UUID
    region: str
    provider: str
    frames_ingested: int
    status: str = "synced"


class AtlasExportJobRequest(BaseDomainModel):
    tenant_id: UUID
    region: str = Field(min_length=2, max_length=160)
    export_type: str = Field(min_length=3, max_length=32)


class AtlasExportJobResponse(BaseDomainModel):
    job_id: UUID
    tenant_id: UUID
    region: str
    export_type: str
    status: str
    attempt_count: int
    max_attempts: int
    output_uri: str | None = None
    last_error: str | None = None


class OpsSloResponse(BaseDomainModel):
    tenant_id: UUID
    window_hours: int
    iot_ingestion_events: int
    satellite_ingestion_events: int
    atlas_exports_completed: int
    atlas_exports_failed: int
    dead_letter_events: int
    success_ratio: float


class IoTDataRead(BaseDomainModel):
    id: UUID
    tenant_id: UUID
    sensor_id: str
    payload: dict[str, Any]
    created_at: datetime


class SatelliteDataRead(BaseDomainModel):
    id: UUID
    tenant_id: UUID
    region: str
    imagery_source: str
    metadata: dict[str, Any]
    created_at: datetime


class AtlasRead(BaseDomainModel):
    id: UUID
    tenant_id: UUID
    region: str
    atlas_key: str
    export_type: str
    metadata: dict[str, Any]
    created_at: datetime


class AtlasLatestResponse(BaseDomainModel):
    tenant_id: UUID
    region: str
    atlas: str
    export_type: str
    metadata: dict[str, Any]
    created_at: datetime


class MaintenanceScheduleRead(BaseDomainModel):
    id: UUID
    tenant_id: UUID
    asset_id: str
    risk_score: float
    recommendation: str
    metadata: dict[str, Any]
    created_at: datetime
