from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.models.common import BaseDomainModel


class DossierFormat:
    PDF = "pdf"
    JSON = "json"
    XML = "xml"

    ALL = {PDF, JSON, XML}


class DeckExportType:
    PPTX = "pptx"
    PDF = "pdf"
    MP4 = "mp4"

    ALL = {PPTX, PDF, MP4}


class ConsortiumTier:
    GLOBAL_UTILITY = "global_utility"
    ELITE_INTELLIGENCE_ORDER = "elite_intelligence_order"
    PLANETARY_CLUB = "planetary_club"

    ORDERED = [GLOBAL_UTILITY, ELITE_INTELLIGENCE_ORDER, PLANETARY_CLUB]


class ConsortiumAction:
    JOIN = "join"
    UPGRADE = "upgrade"
    DOWNGRADE = "downgrade"

    ALL = {JOIN, UPGRADE, DOWNGRADE}


class DossierRequest(BaseDomainModel):
    tenant_id: UUID
    simulation_id: UUID
    format: str = Field(default=DossierFormat.PDF, min_length=3, max_length=10)
    industry_module: str = Field(default="general_infrastructure", min_length=3, max_length=80)


class DossierResponse(BaseDomainModel):
    dossier_id: UUID
    tenant_id: UUID
    simulation_id: UUID
    format: str
    industry_module: str
    artifact_uri: str
    status: str = "generated"


class DeckRequest(BaseDomainModel):
    tenant_id: UUID
    project_id: UUID
    export_type: str = Field(default=DeckExportType.PDF, min_length=3, max_length=12)


class DeckResponse(BaseDomainModel):
    deck_id: UUID
    tenant_id: UUID
    project_id: UUID
    export_type: str
    artifact_uri: str
    status: str = "exported"


class ConsortiumRequest(BaseDomainModel):
    tenant_id: UUID
    action: str = Field(default=ConsortiumAction.JOIN, min_length=3, max_length=20)


class ConsortiumMembershipRead(BaseDomainModel):
    id: UUID
    tenant_id: UUID
    tier: str
    status: str
    created_at: datetime
    updated_at: datetime


class ConsortiumDashboardRead(BaseDomainModel):
    tenant_id: UUID
    tier: str
    compliance_status: str
    foresight_index: float
    consortium_voting_enabled: bool
    active_dossiers_30d: int
    active_decks_30d: int
    generated_at: datetime
