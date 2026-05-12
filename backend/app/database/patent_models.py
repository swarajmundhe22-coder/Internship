"""SQLAlchemy ORM models for Patent Platform."""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    VARCHAR,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class PatentModel(Base):
    """Core Patent application ORM model."""
    __tablename__ = "patents"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    title = Column(String(500), nullable=False)
    abstract = Column(Text, nullable=False)
    technical_field = Column(String(255), nullable=False)

    # Status and type
    status = Column(String(50), nullable=False, default="DRAFT")
    patent_type = Column(String(50), nullable=False, default="UTILITY")

    # Content
    embodiments = Column(JSON, nullable=False, default=list)
    claims_summary = Column(Text, nullable=True)
    detailed_description = Column(Text, nullable=True)

    # Jurisdictions (stored as JSON list)
    jurisdictions = Column(JSON, nullable=False, default=list)

    # FEA file reference
    fea_file_id = Column(PG_UUID(as_uuid=True), nullable=True)
    fea_file_name = Column(String(255), nullable=True)

    # Filing numbers
    uspto_application_number = Column(String(50), nullable=True, unique=True)
    indian_ipo_application_number = Column(String(50), nullable=True, unique=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    filed_at = Column(DateTime(timezone=True), nullable=True)

    # Multi-tenancy
    tenant_id = Column(PG_UUID(as_uuid=True), nullable=True)

    # Relationships
    inventors = relationship("InventorModel", back_populates="patent", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLogEntryModel", back_populates="patent", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_patents_tenant_id", "tenant_id"),
        Index("ix_patents_status", "status"),
        Index("ix_patents_created_at", "created_at"),
    )


class InventorModel(Base):
    """Inventor/Applicant ORM model."""
    __tablename__ = "inventors"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    patent_id = Column(PG_UUID(as_uuid=True), ForeignKey("patents.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    country = Column(String(2), nullable=False)  # ISO 3166-1 alpha-2
    role = Column(String(50), nullable=False, default="PRIMARY")

    # Relationship
    patent = relationship("PatentModel", back_populates="inventors")

    __table_args__ = (
        Index("ix_inventors_patent_id", "patent_id"),
        Index("ix_inventors_email", "email"),
    )


class MaterialModel(Base):
    """Material properties database ORM model."""
    __tablename__ = "materials"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False, unique=True)
    material_type = Column(String(50), nullable=False)  # metal, composite, polymer

    # Mechanical properties
    density = Column(Float, nullable=False)  # kg/m³
    youngs_modulus = Column(Float, nullable=False)  # GPa
    tensile_strength = Column(Float, nullable=False)  # MPa
    yield_strength = Column(Float, nullable=True)  # MPa
    elongation_at_break = Column(Float, nullable=True)  # %

    # Environmental properties
    corrosion_resistance = Column(String(50), nullable=False)  # excellent, good, fair, poor
    temperature_range_min = Column(Float, nullable=True)  # °C
    temperature_range_max = Column(Float, nullable=True)  # °C

    # Electrochemistry (for corrosion prediction)
    corrosion_potential = Column(Float, nullable=True)  # mV vs SHE
    corrosion_current_density = Column(Float, nullable=True)  # µA/cm²

    # Metadata
    source = Column(String(255), nullable=False)  # MatWeb, etc.
    source_url = Column(String(1024), nullable=True)
    datasheet_url = Column(String(1024), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_materials_type", "material_type"),
        Index("ix_materials_corrosion_resistance", "corrosion_resistance"),
    )


class AuditLogEntryModel(Base):
    """Audit trail for patent operations."""
    __tablename__ = "patent_audit_logs"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    patent_id = Column(PG_UUID(as_uuid=True), ForeignKey("patents.id", ondelete="CASCADE"), nullable=False)
    action = Column(String(255), nullable=False)  # CREATED, UPDATED, FILED, etc.
    actor = Column(String(255), nullable=False)  # User email or system
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    # Multi-tenancy
    tenant_id = Column(PG_UUID(as_uuid=True), nullable=True)

    # Relationship
    patent = relationship("PatentModel", back_populates="audit_logs")

    __table_args__ = (
        Index("ix_patent_audit_logs_patent_id", "patent_id"),
        Index("ix_patent_audit_logs_timestamp", "timestamp"),
        Index("ix_patent_audit_logs_action", "action"),
    )
