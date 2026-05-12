"""Patent and patent-filing domain models for Phase 0 MVP."""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class PatentJurisdiction(str, Enum):
    """Supported patent jurisdictions."""
    USPTO = "USPTO"
    INDIAN_IPO = "INDIAN_IPO"


class PatentType(str, Enum):
    """Patent application types."""
    PROVISIONAL = "PROVISIONAL"
    UTILITY = "UTILITY"
    DESIGN = "DESIGN"


class PatentStatus(str, Enum):
    """Status of patent application workflow."""
    DRAFT = "DRAFT"
    READY_FOR_FILING = "READY_FOR_FILING"
    FILED = "FILED"
    REJECTED = "REJECTED"
    ABANDONED = "ABANDONED"


class InventorRole(str, Enum):
    """Role of inventor in patent."""
    PRIMARY = "PRIMARY"
    COINVENTOR = "COINVENTOR"


class PatentBase(BaseModel):
    """Base patent model with strict validation."""
    model_config = ConfigDict(extra="forbid", from_attributes=True)


class Inventor(PatentBase):
    """Inventor/applicant information."""
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    country: str = Field(..., min_length=2, max_length=2)  # ISO 3166-1 alpha-2
    role: InventorRole = Field(default=InventorRole.PRIMARY)


class Patent(PatentBase):
    """Core patent application model."""
    id: UUID = Field(default_factory=uuid4)
    title: str = Field(..., min_length=5, max_length=500)
    abstract: str = Field(..., min_length=10, max_length=5000)
    technical_field: str = Field(..., min_length=5, max_length=255)

    # Jurisdictions and types
    jurisdictions: list[PatentJurisdiction] = Field(default_factory=list)
    patent_type: PatentType = Field(default=PatentType.UTILITY)

    # Patent content
    embodiments: list[str] = Field(default_factory=list)  # Key technical embodiments
    claims_summary: Optional[str] = Field(None, max_length=5000)
    detailed_description: Optional[str] = Field(None)

    # Filing metadata
    status: PatentStatus = Field(default=PatentStatus.DRAFT)
    inventors: list[Inventor] = Field(default_factory=list)

    # FEA/technical file references
    fea_file_id: Optional[UUID] = None
    fea_file_name: Optional[str] = None

    # Timestamps
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    filed_at: Optional[datetime] = None

    # Filing receipts
    uspto_application_number: Optional[str] = None
    indian_ipo_application_number: Optional[str] = None

    # Tenant context
    tenant_id: Optional[UUID] = None


class PatentFilingRequest(PatentBase):
    """Request to file patent with USPTO/Indian IPO."""
    patent_id: UUID
    jurisdiction: PatentJurisdiction = Field(default=PatentJurisdiction.USPTO)
    filing_xml_preview: Optional[str] = None  # Generated XML for review


class Material(PatentBase):
    """Material properties database record."""
    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1, max_length=255)
    material_type: str = Field(..., max_length=50)  # "metal", "composite", "polymer", etc.

    # Mechanical properties
    density: float = Field(..., gt=0)  # kg/m³
    youngs_modulus: float = Field(..., gt=0)  # GPa
    tensile_strength: float = Field(..., gt=0)  # MPa
    yield_strength: Optional[float] = Field(None, gt=0)
    elongation_at_break: Optional[float] = Field(None, ge=0)  # %

    # Environmental properties
    corrosion_resistance: str = Field(..., max_length=50)  # "excellent", "good", "fair", "poor"
    temperature_range_min: Optional[float] = None  # °C
    temperature_range_max: Optional[float] = None  # °C

    # Electrochemical properties (for corrosion prediction)
    corrosion_potential: Optional[float] = None  # mV vs SHE
    corrosion_current_density: Optional[float] = None  # µA/cm²

    # Metadata
    source: str = Field(..., max_length=255)  # Data source (MatWeb, internal, etc.)
    source_url: Optional[str] = None
    datasheet_url: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class PatentFilingTemplateUSA(PatentBase):
    """USPTO form with jurisdiction-specific fields."""
    form_sn: str = Field(default="SN2019-01")  # USPTO form serial number
    filing_fee: float = Field(default=330.0)  # USD, subject to change
    claims_required: int = Field(default=1)
    claims_per_dependent: int = Field(default=1)
    claim_fee_per_additional: float = Field(default=55.0)  # Per additional claim


class PatentFilingTemplateIndia(PatentBase):
    """Indian Patent Office form with jurisdiction-specific fields."""
    form_number: str = Field(default="Form 2")
    filing_fee: float = Field(default=1600.0)  # INR for small entity
    claims_required: int = Field(default=1)


class AuditLogEntry(PatentBase):
    """Audit trail for patent filing operations."""
    id: UUID = Field(default_factory=uuid4)
    patent_id: UUID
    action: str = Field(..., max_length=255)  # "CREATED", "UPDATED", "FILED", etc.
    actor: str = Field(..., max_length=255)  # User email or system
    details: Optional[dict] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    tenant_id: Optional[UUID] = None
