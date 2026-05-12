"""Repository for Patent and related database operations."""

from typing import Optional
from uuid import UUID

from sqlalchemy import and_, inspect, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.patent_models import (
    AuditLogEntryModel,
    InventorModel,
    MaterialModel,
    PatentModel,
)
from app.models.patent import (
    AuditLogEntry,
    Inventor,
    Material,
    Patent,
    PatentJurisdiction,
    PatentStatus,
    PatentType,
)


class PatentRepository:
    """Repository for Patent CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_patent(self, patent: Patent) -> Patent:
        """Create new patent application."""
        db_patent = PatentModel(
            title=patent.title,
            abstract=patent.abstract,
            technical_field=patent.technical_field,
            status=patent.status.value,
            patent_type=patent.patent_type.value,
            embodiments=patent.embodiments,
            claims_summary=patent.claims_summary,
            detailed_description=patent.detailed_description,
            jurisdictions=[j.value for j in patent.jurisdictions],
            fea_file_id=patent.fea_file_id,
            fea_file_name=patent.fea_file_name,
            tenant_id=patent.tenant_id,
        )

        self.session.add(db_patent)
        await self.session.flush()

        # Add inventors
        for inventor in patent.inventors:
            inv = InventorModel(
                patent_id=db_patent.id,
                name=inventor.name,
                email=inventor.email,
                country=inventor.country,
                role=inventor.role.value,
            )
            self.session.add(inv)

        await self.session.commit()
        reloaded = await self._get_patent_model_by_id(db_patent.id)
        if reloaded is None:
            raise ValueError(f"Unable to load newly created patent {db_patent.id}")
        return self._to_domain(reloaded)

    async def get_patent_by_id(self, patent_id: UUID) -> Optional[Patent]:
        """Retrieve patent by ID."""
        db_patent = await self._get_patent_model_by_id(patent_id)
        if not db_patent:
            return None
        return self._to_domain(db_patent)

    async def list_patents(
        self,
        tenant_id: Optional[UUID] = None,
        status: Optional[PatentStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Patent]:
        """List patents with optional filtering."""
        filters = []
        if tenant_id:
            filters.append(PatentModel.tenant_id == tenant_id)
        if status:
            filters.append(PatentModel.status == status.value)

        query = select(PatentModel).options(selectinload(PatentModel.inventors))
        if filters:
            query = query.where(and_(*filters))

        query = query.limit(limit).offset(offset)
        result = await self.session.execute(query)
        patents = result.scalars().all()
        return [self._to_domain(p) for p in patents]

    async def update_patent(self, patent_id: UUID, updates: dict) -> Optional[Patent]:
        """Update patent fields."""
        db_patent = await self._get_patent_model_by_id(patent_id)
        if not db_patent:
            return None

        # Update allowed fields
        allowed_fields = {
            "title",
            "abstract",
            "technical_field",
            "status",
            "claims_summary",
            "detailed_description",
            "embodiments",
        }
        for key, value in updates.items():
            if key in allowed_fields:
                setattr(db_patent, key, value)

        await self.session.commit()
        refreshed = await self._get_patent_model_by_id(patent_id)
        if refreshed is None:
            return None
        return self._to_domain(refreshed)

    async def mark_as_filed(
        self,
        patent_id: UUID,
        jurisdiction: str,
        application_number: str,
    ) -> Optional[Patent]:
        """Mark patent as filed with USPTO/IPO."""
        db_patent = await self._get_patent_model_by_id(patent_id)
        if not db_patent:
            return None

        db_patent.status = PatentStatus.FILED.value

        if jurisdiction == "USPTO":
            db_patent.uspto_application_number = application_number
        elif jurisdiction == "INDIAN_IPO":
            db_patent.indian_ipo_application_number = application_number

        from datetime import datetime, timezone
        db_patent.filed_at = datetime.now(timezone.utc)

        await self.session.commit()
        refreshed = await self._get_patent_model_by_id(patent_id)
        if refreshed is None:
            return None
        return self._to_domain(refreshed)

    async def delete_patent(self, patent_id: UUID) -> bool:
        """Delete patent (cascade deletes inventors and audit logs)."""
        result = await self.session.execute(
            select(PatentModel).where(PatentModel.id == patent_id)
        )
        db_patent = result.scalar_one_or_none()
        if not db_patent:
            return False

        await self.session.delete(db_patent)
        await self.session.commit()
        return True

    async def _get_patent_model_by_id(self, patent_id: UUID) -> Optional[PatentModel]:
        result = await self.session.execute(
            select(PatentModel)
            .options(selectinload(PatentModel.inventors))
            .where(PatentModel.id == patent_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    def _to_domain(db_patent: PatentModel) -> Patent:
        """Convert SQLAlchemy model to domain model."""
        unloaded = inspect(db_patent).unloaded
        inventor_rows = [] if "inventors" in unloaded else list(db_patent.inventors or [])
        inventors = [
            Inventor(
                id=inv.id,
                name=inv.name,
                email=inv.email,
                country=inv.country,
                role=inv.role,
            )
            for inv in inventor_rows
        ]

        return Patent(
            id=db_patent.id,
            title=db_patent.title,
            abstract=db_patent.abstract,
            technical_field=db_patent.technical_field,
            status=PatentStatus(db_patent.status),
            patent_type=PatentType(db_patent.patent_type),
            embodiments=db_patent.embodiments or [],
            claims_summary=db_patent.claims_summary,
            detailed_description=db_patent.detailed_description,
            jurisdictions=[PatentJurisdiction(j) for j in (db_patent.jurisdictions or [])],
            fea_file_id=db_patent.fea_file_id,
            fea_file_name=db_patent.fea_file_name,
            inventors=inventors,
            created_at=db_patent.created_at,
            updated_at=db_patent.updated_at,
            filed_at=db_patent.filed_at,
            uspto_application_number=db_patent.uspto_application_number,
            indian_ipo_application_number=db_patent.indian_ipo_application_number,
            tenant_id=db_patent.tenant_id,
        )


class MaterialRepository:
    """Repository for Material database CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_material(self, material: Material) -> Material:
        """Create new material record."""
        db_material = MaterialModel(
            name=material.name,
            material_type=material.material_type,
            density=material.density,
            youngs_modulus=material.youngs_modulus,
            tensile_strength=material.tensile_strength,
            yield_strength=material.yield_strength,
            elongation_at_break=material.elongation_at_break,
            corrosion_resistance=material.corrosion_resistance,
            temperature_range_min=material.temperature_range_min,
            temperature_range_max=material.temperature_range_max,
            corrosion_potential=material.corrosion_potential,
            corrosion_current_density=material.corrosion_current_density,
            source=material.source,
            source_url=material.source_url,
            datasheet_url=material.datasheet_url,
        )
        self.session.add(db_material)
        await self.session.commit()
        return material

    async def get_material_by_id(self, material_id: UUID) -> Optional[Material]:
        """Retrieve material by ID."""
        result = await self.session.execute(
            select(MaterialModel).where(MaterialModel.id == material_id)
        )
        db_material = result.scalar_one_or_none()
        if not db_material:
            return None
        return self._to_domain(db_material)

    async def get_material_by_name(self, name: str) -> Optional[Material]:
        """Retrieve material by name."""
        result = await self.session.execute(
            select(MaterialModel).where(MaterialModel.name == name)
        )
        db_material = result.scalar_one_or_none()
        if not db_material:
            return None
        return self._to_domain(db_material)

    async def list_materials(
        self,
        material_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Material]:
        """List materials with optional filtering."""
        query = select(MaterialModel)
        if material_type:
            query = query.where(MaterialModel.material_type == material_type)
        query = query.limit(limit).offset(offset)

        result = await self.session.execute(query)
        materials = result.scalars().all()
        return [self._to_domain(m) for m in materials]

    async def count_materials(self) -> int:
        """Count total materials in database."""
        result = await self.session.execute(select(MaterialModel))
        return len(result.scalars().all())

    @staticmethod
    def _to_domain(db_material: MaterialModel) -> Material:
        """Convert SQLAlchemy model to domain model."""
        return Material(
            id=db_material.id,
            name=db_material.name,
            material_type=db_material.material_type,
            density=db_material.density,
            youngs_modulus=db_material.youngs_modulus,
            tensile_strength=db_material.tensile_strength,
            yield_strength=db_material.yield_strength,
            elongation_at_break=db_material.elongation_at_break,
            corrosion_resistance=db_material.corrosion_resistance,
            temperature_range_min=db_material.temperature_range_min,
            temperature_range_max=db_material.temperature_range_max,
            corrosion_potential=db_material.corrosion_potential,
            corrosion_current_density=db_material.corrosion_current_density,
            source=db_material.source,
            source_url=db_material.source_url,
            datasheet_url=db_material.datasheet_url,
            created_at=db_material.created_at,
            updated_at=db_material.updated_at,
        )


class AuditLogRepository:
    """Repository for audit trail logging."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def log_action(
        self,
        patent_id: UUID,
        action: str,
        actor: str,
        details: Optional[dict] = None,
        tenant_id: Optional[UUID] = None,
    ) -> AuditLogEntry:
        """Log an action to the audit trail."""
        db_log = AuditLogEntryModel(
            patent_id=patent_id,
            action=action,
            actor=actor,
            details=details or {},
            tenant_id=tenant_id,
        )
        self.session.add(db_log)
        await self.session.commit()

        return AuditLogEntry(
            id=db_log.id,
            patent_id=db_log.patent_id,
            action=db_log.action,
            actor=db_log.actor,
            details=db_log.details,
            timestamp=db_log.timestamp,
            tenant_id=db_log.tenant_id,
        )

    async def get_audit_log_for_patent(
        self,
        patent_id: UUID,
        limit: int = 100,
    ) -> list[AuditLogEntry]:
        """Get all audit logs for a patent."""
        result = await self.session.execute(
            select(AuditLogEntryModel)
            .where(AuditLogEntryModel.patent_id == patent_id)
            .order_by(AuditLogEntryModel.timestamp.desc())
            .limit(limit)
        )
        logs = result.scalars().all()

        return [
            AuditLogEntry(
                id=log.id,
                patent_id=log.patent_id,
                action=log.action,
                actor=log.actor,
                details=log.details,
                timestamp=log.timestamp,
                tenant_id=log.tenant_id,
            )
            for log in logs
        ]
