from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.models.common import BaseDomainModel


class VisualizationMode:
    TWIN = "twin"
    AR = "ar"
    VR = "vr"

    ALL = {TWIN, AR, VR}


class VisualizationRequest(BaseDomainModel):
    simulation_id: UUID
    tenant_id: UUID
    mode: str = Field(default=VisualizationMode.TWIN)


class TwinHotspot(BaseDomainModel):
    name: str
    severity: str
    x: float
    y: float
    z: float


class TwinMetadata(BaseDomainModel):
    asset_type: str
    scene_profile: str
    hotspots: list[TwinHotspot]
    timeline_frames: list[dict[str, object]]


class VisualizationRead(BaseDomainModel):
    id: UUID
    simulation_id: UUID
    tenant_id: UUID | None
    mode: str
    status: str
    overlay_accuracy: float
    metadata: dict[str, object]
    created_at: datetime
    updated_at: datetime


class VisualizationPlaybackResponse(BaseDomainModel):
    visualization: VisualizationRead
    tenant_id: UUID
    simulation_id: UUID
    mode: str
    timeline_frames: list[dict[str, object]]
    playback_hud: dict[str, object]
    status: str = "playback_ready"


class VisualizationExportRequest(BaseDomainModel):
    simulation_id: UUID
    tenant_id: UUID
    mode: str = Field(default=VisualizationMode.TWIN)
    file_type: str = Field(default="mp4")


class VisualizationExportRead(BaseDomainModel):
    id: UUID
    visualization_id: UUID
    tenant_id: UUID | None
    file_type: str
    file_uri: str
    created_at: datetime


class VisualizationExportResponse(BaseDomainModel):
    tenant_id: UUID
    simulation_id: UUID
    mode: str
    export: VisualizationExportRead
    status: str = "exported"
