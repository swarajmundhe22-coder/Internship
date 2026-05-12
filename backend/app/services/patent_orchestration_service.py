"""Patent filing orchestration service."""

from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.patent import (
    Patent,
    PatentFilingRequest,
    PatentStatus,
    PatentJurisdiction,
)
from app.repositories.patent_repository import (
    AuditLogRepository,
    MaterialRepository,
    PatentRepository,
)
from app.services.patent_filing_service import (
    IndianPatentOfficeXMLGenerator,
    USPTOXMLGenerator,
)


class PatentFilingOrchestrator:
    """Orchestrates patent creation, validation, and filing workflow."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.patent_repo = PatentRepository(session)
        self.material_repo = MaterialRepository(session)
        self.audit_repo = AuditLogRepository(session)
        self.uspto_generator = USPTOXMLGenerator()
        self.ipo_generator = IndianPatentOfficeXMLGenerator()

    async def create_draft_patent(
        self,
        title: str,
        abstract: str,
        technical_field: str,
        actor_email: str,
        tenant_id: Optional[UUID] = None,
    ) -> Patent:
        """Create a new patent in DRAFT status."""
        patent = Patent(
            title=title,
            abstract=abstract,
            technical_field=technical_field,
            status=PatentStatus.DRAFT,
            tenant_id=tenant_id,
        )

        created_patent = await self.patent_repo.create_patent(patent)

        # Log creation
        await self.audit_repo.log_action(
            patent_id=created_patent.id,
            action="CREATED",
            actor=actor_email,
            details={"title": title},
            tenant_id=tenant_id,
        )

        return created_patent

    async def add_embodiments(
        self,
        patent_id: UUID,
        embodiments: list[str],
        actor_email: str,
    ) -> Patent:
        """Add technical embodiments to patent."""
        patent = await self.patent_repo.update_patent(
            patent_id,
            {"embodiments": embodiments},
        )

        if patent:
            await self.audit_repo.log_action(
                patent_id=patent_id,
                action="EMBODIMENTS_ADDED",
                actor=actor_email,
                details={"count": len(embodiments)},
            )

        return patent

    async def set_claims_summary(
        self,
        patent_id: UUID,
        claims_summary: str,
        actor_email: str,
    ) -> Patent:
        """Add claims summary to patent."""
        patent = await self.patent_repo.update_patent(
            patent_id,
            {"claims_summary": claims_summary},
        )

        if patent:
            await self.audit_repo.log_action(
                patent_id=patent_id,
                action="CLAIMS_SUMMARY_SET",
                actor=actor_email,
            )

        return patent

    async def generate_filing_preview(
        self,
        patent_id: UUID,
        jurisdiction: PatentJurisdiction,
        applicant_name: str,
    ) -> dict:
        """Generate XML preview for USPTO or Indian IPO filing."""
        patent = await self.patent_repo.get_patent_by_id(patent_id)
        if not patent:
            raise ValueError(f"Patent {patent_id} not found")

        if jurisdiction == PatentJurisdiction.USPTO:
            preview = self.uspto_generator.generate_filing_xml_preview(
                patent,
                applicant_name,
            )
        elif jurisdiction == PatentJurisdiction.INDIAN_IPO:
            preview = {
                "application_id": str(patent_id)[:8],
                "title": patent.title,
                "abstract": patent.abstract,
                "applicant": applicant_name,
                "claims_count": 1 + len(patent.embodiments),
                "filing_fee": self.ipo_generator.filing_fee,
                "jurisdiction": "Indian Patent Office",
            }
        else:
            raise ValueError(f"Unsupported jurisdiction: {jurisdiction}")

        return preview

    async def submit_for_filing(
        self,
        request: PatentFilingRequest,
        applicant_name: str,
        applicant_address: str,
        applicant_city: str,
        applicant_state: str,
        applicant_zip: str,
        actor_email: str,
    ) -> dict:
        """Generate filing XML and mark patent as READY_FOR_FILING."""
        patent = await self.patent_repo.get_patent_by_id(request.patent_id)
        if not patent:
            raise ValueError(f"Patent {request.patent_id} not found")

        # Validate patent has required fields
        if not patent.abstract or not patent.title or not patent.embodiments:
            raise ValueError(
                "Patent must have title, abstract, and at least one embodiment"
            )

        # Generate XML
        if request.jurisdiction == PatentJurisdiction.USPTO:
            filing_xml = self.uspto_generator.generate_filing_xml(
                patent,
                applicant_name,
                applicant_address,
                applicant_city,
                applicant_state,
                applicant_zip,
            )
        elif request.jurisdiction == PatentJurisdiction.INDIAN_IPO:
            filing_xml = self.ipo_generator.generate_filing_xml(
                patent,
                applicant_name,
                applicant_address,
                applicant_city,
                applicant_state,
                applicant_zip,
            )
        else:
            raise ValueError(f"Unsupported jurisdiction: {request.jurisdiction}")

        # Update patent status
        updated = await self.patent_repo.update_patent(
            request.patent_id,
            {"status": PatentStatus.READY_FOR_FILING.value},
        )

        # Log filing submission
        await self.audit_repo.log_action(
            patent_id=request.patent_id,
            action="SUBMITTED_FOR_FILING",
            actor=actor_email,
            details={
                "jurisdiction": request.jurisdiction.value,
                "applicant": applicant_name,
            },
        )

        return {
            "patent_id": str(request.patent_id),
            "status": "success",
            "patent_status": updated.status.value,
            "jurisdiction": request.jurisdiction.value,
            "filing_xml": filing_xml[:500],  # Return snippet for preview
            "estimated_filing_time": "2-3 weeks",
            "next_step": "Review XML, obtain patent attorney review, then file with USPTO/IPO",
        }

    async def mark_as_filed(
        self,
        patent_id: UUID,
        jurisdiction: PatentJurisdiction,
        application_number: str,
        actor_email: str,
    ) -> Patent:
        """Mark patent as FILED with USPTO/IPO application number."""
        patent = await self.patent_repo.mark_as_filed(
            patent_id,
            jurisdiction.value,
            application_number,
        )

        if patent:
            await self.audit_repo.log_action(
                patent_id=patent_id,
                action="FILED",
                actor=actor_email,
                details={
                    "jurisdiction": jurisdiction.value,
                    "application_number": application_number,
                },
            )

        return patent

    async def lookup_material(
        self,
        material_name: str,
    ) -> Optional[dict]:
        """Look up material properties by name."""
        material = await self.material_repo.get_material_by_name(material_name)
        if not material:
            return None

        return {
            "id": str(material.id),
            "name": material.name,
            "type": material.material_type,
            "density": material.density,
            "youngs_modulus": material.youngs_modulus,
            "tensile_strength": material.tensile_strength,
            "corrosion_resistance": material.corrosion_resistance,
            "temperature_range": {
                "min": material.temperature_range_min,
                "max": material.temperature_range_max,
            },
            "source": material.source,
            "datasheet_url": material.datasheet_url,
        }

    async def list_materials_by_type(
        self,
        material_type: str,
        limit: int = 50,
    ) -> list[dict]:
        """List materials by type."""
        materials = await self.material_repo.list_materials(
            material_type=material_type,
            limit=limit,
        )
        return [
            {
                "id": str(m.id),
                "name": m.name,
                "type": m.material_type,
                "density": m.density,
                "youngs_modulus": m.youngs_modulus,
                "tensile_strength": m.tensile_strength,
                "corrosion_resistance": m.corrosion_resistance,
                "source": m.source,
            }
            for m in materials
        ]

    async def get_audit_trail(
        self,
        patent_id: UUID,
    ) -> list[dict]:
        """Get full audit trail for patent."""
        logs = await self.audit_repo.get_audit_log_for_patent(patent_id)
        return [
            {
                "timestamp": log.timestamp.isoformat(),
                "action": log.action,
                "actor": log.actor,
                "details": log.details,
            }
            for log in logs
        ]

    async def get_patent_status(
        self,
        patent_id: UUID,
    ) -> Optional[dict]:
        """Get detailed patent status and filing info."""
        patent = await self.patent_repo.get_patent_by_id(patent_id)
        if not patent:
            return None

        return {
            "id": str(patent.id),
            "title": patent.title,
            "status": patent.status.value,
            "jurisdictions": [j.value for j in patent.jurisdictions],
            "filed_at": patent.filed_at.isoformat() if patent.filed_at else None,
            "uspto_application_number": patent.uspto_application_number,
            "indian_ipo_application_number": patent.indian_ipo_application_number,
            "claims_count": 1 + len(patent.embodiments),
            "progress": self._calculate_progress(patent),
        }

    @staticmethod
    def _calculate_progress(patent: Patent) -> int:
        """Calculate patent completion progress (0-100%)."""
        points = 0
        # Title and abstract: 20 points
        if patent.title:
            points += 10
        if patent.abstract:
            points += 10
        # Embodiments: 20 points
        if patent.embodiments:
            points += min(20, len(patent.embodiments) * 5)
        # Claims: 20 points
        if patent.claims_summary:
            points += 20
        # Ready for filing: 20 points
        if patent.status == PatentStatus.READY_FOR_FILING:
            points += 20
        elif patent.status == PatentStatus.FILED:
            points += 30

        return min(100, points)
