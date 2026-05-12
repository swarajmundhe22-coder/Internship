"""FastAPI routes for Patent Platform Phase 0 MVP."""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_session
from app.models.patent import (
    Patent,
    PatentFilingRequest,
    PatentJurisdiction,
    PatentStatus,
    Inventor,
)
from app.services.patent_orchestration_service import PatentFilingOrchestrator

router = APIRouter(prefix="/patents", tags=["patents"])


async def get_orchestrator(session: AsyncSession = Depends(get_session)) -> PatentFilingOrchestrator:
    """Dependency to provide PatentFilingOrchestrator."""
    return PatentFilingOrchestrator(session)


def get_actor_email() -> str:
    """Get current user email from JWT token (placeholder for auth)."""
    # TODO: Integrate with JWT auth from existing backend
    return "user@example.com"


# ============================================================================
# Patent Creation & Management
# ============================================================================

@router.post("/create", response_model=Patent)
async def create_patent(
    title: str,
    abstract: str,
    technical_field: str,
    orchestrator: PatentFilingOrchestrator = Depends(get_orchestrator),
    actor_email: str = Depends(get_actor_email),
):
    """
    Create a new patent application in DRAFT status.

    Args:
        title: Patent title
        abstract: Brief abstract of the invention
        technical_field: Technical field of the invention

    Returns:
        Created patent object
    """
    try:
        patent = await orchestrator.create_draft_patent(
            title=title,
            abstract=abstract,
            technical_field=technical_field,
            actor_email=actor_email,
        )
        return patent
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{patent_id}", response_model=Patent)
async def get_patent(
    patent_id: UUID,
    orchestrator: PatentFilingOrchestrator = Depends(get_orchestrator),
):
    """Retrieve patent by ID."""
    patent = await orchestrator.patent_repo.get_patent_by_id(patent_id)
    if not patent:
        raise HTTPException(status_code=404, detail="Patent not found")
    return patent


@router.post("/{patent_id}/embodiments")
async def add_embodiments(
    patent_id: UUID,
    embodiments: list[str],
    orchestrator: PatentFilingOrchestrator = Depends(get_orchestrator),
    actor_email: str = Depends(get_actor_email),
):
    """Add technical embodiments to patent."""
    if not embodiments or len(embodiments) == 0:
        raise HTTPException(status_code=400, detail="At least one embodiment required")

    patent = await orchestrator.add_embodiments(
        patent_id=patent_id,
        embodiments=embodiments,
        actor_email=actor_email,
    )

    if not patent:
        raise HTTPException(status_code=404, detail="Patent not found")

    return {
        "status": "success",
        "patent_id": str(patent_id),
        "embodiments_count": len(patent.embodiments),
    }


@router.post("/{patent_id}/claims")
async def set_claims(
    patent_id: UUID,
    claims_summary: str,
    orchestrator: PatentFilingOrchestrator = Depends(get_orchestrator),
    actor_email: str = Depends(get_actor_email),
):
    """Set claims summary for patent."""
    if not claims_summary or len(claims_summary) < 10:
        raise HTTPException(status_code=400, detail="Claims summary must be at least 10 characters")

    patent = await orchestrator.set_claims_summary(
        patent_id=patent_id,
        claims_summary=claims_summary,
        actor_email=actor_email,
    )

    if not patent:
        raise HTTPException(status_code=404, detail="Patent not found")

    return {
        "status": "success",
        "patent_id": str(patent_id),
        "claims_summary_length": len(patent.claims_summary or ""),
    }


# ============================================================================
# Patent Filing Workflow
# ============================================================================

@router.post("/{patent_id}/filing-preview")
async def preview_filing(
    patent_id: UUID,
    jurisdiction: PatentJurisdiction,
    applicant_name: str,
    orchestrator: PatentFilingOrchestrator = Depends(get_orchestrator),
):
    """Generate preview of USPTO/IPO filing XML."""
    try:
        preview = await orchestrator.generate_filing_preview(
            patent_id=patent_id,
            jurisdiction=jurisdiction,
            applicant_name=applicant_name,
        )
        return preview
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{patent_id}/submit-for-filing")
async def submit_for_filing(
    patent_id: UUID,
    jurisdiction: PatentJurisdiction,
    applicant_name: str,
    applicant_address: str,
    applicant_city: str,
    applicant_state: str,
    applicant_zip: str,
    orchestrator: PatentFilingOrchestrator = Depends(get_orchestrator),
    actor_email: str = Depends(get_actor_email),
):
    """
    Submit patent for filing with USPTO or Indian Patent Office.

    Generates XML filing document and marks patent as READY_FOR_FILING.
    Next step: Patent attorney review and actual submission.
    """
    try:
        request = PatentFilingRequest(
            patent_id=patent_id,
            jurisdiction=jurisdiction,
        )

        result = await orchestrator.submit_for_filing(
            request=request,
            applicant_name=applicant_name,
            applicant_address=applicant_address,
            applicant_city=applicant_city,
            applicant_state=applicant_state,
            applicant_zip=applicant_zip,
            actor_email=actor_email,
        )

        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{patent_id}/mark-as-filed")
async def mark_as_filed(
    patent_id: UUID,
    jurisdiction: PatentJurisdiction,
    application_number: str,
    orchestrator: PatentFilingOrchestrator = Depends(get_orchestrator),
    actor_email: str = Depends(get_actor_email),
):
    """
    Mark patent as FILED with USPTO/IPO application number.

    Called after successful filing with government office.
    """
    patent = await orchestrator.mark_as_filed(
        patent_id=patent_id,
        jurisdiction=jurisdiction,
        application_number=application_number,
        actor_email=actor_email,
    )

    if not patent:
        raise HTTPException(status_code=404, detail="Patent not found")

    return {
        "status": "success",
        "patent_id": str(patent_id),
        "status_updated": patent.status.value,
        "application_number": application_number,
        "filed_at": patent.filed_at.isoformat() if patent.filed_at else None,
    }


@router.get("/{patent_id}/status")
async def get_status(
    patent_id: UUID,
    orchestrator: PatentFilingOrchestrator = Depends(get_orchestrator),
):
    """Get detailed patent status and filing information."""
    status_info = await orchestrator.get_patent_status(patent_id)
    if not status_info:
        raise HTTPException(status_code=404, detail="Patent not found")
    return status_info


# ============================================================================
# Material Database
# ============================================================================

@router.get("/materials/lookup")
async def lookup_material(
    name: str,
    orchestrator: PatentFilingOrchestrator = Depends(get_orchestrator),
):
    """Look up material properties by name."""
    material = await orchestrator.lookup_material(name)
    if not material:
        raise HTTPException(status_code=404, detail=f"Material '{name}' not found in database")
    return material


@router.get("/materials/by-type/{material_type}")
async def list_materials_by_type(
    material_type: str,
    limit: int = 50,
    orchestrator: PatentFilingOrchestrator = Depends(get_orchestrator),
):
    """List all materials of a given type (metal, composite, polymer)."""
    materials = await orchestrator.list_materials_by_type(
        material_type=material_type,
        limit=limit,
    )
    return {
        "type": material_type,
        "count": len(materials),
        "materials": materials,
    }


# ============================================================================
# Audit Trail
# ============================================================================

@router.get("/{patent_id}/audit-trail")
async def get_audit_trail(
    patent_id: UUID,
    orchestrator: PatentFilingOrchestrator = Depends(get_orchestrator),
):
    """Get complete audit trail for patent."""
    trail = await orchestrator.get_audit_trail(patent_id)
    if not trail:
        raise HTTPException(status_code=404, detail="Patent not found or no audit logs")
    return {
        "patent_id": str(patent_id),
        "audit_entries": trail,
        "total": len(trail),
    }


# ============================================================================
# Listing & Filtering
# ============================================================================

@router.get("/")
async def list_patents(
    status: Optional[PatentStatus] = None,
    limit: int = 50,
    offset: int = 0,
    orchestrator: PatentFilingOrchestrator = Depends(get_orchestrator),
):
    """List patents with optional status filtering."""
    patents = await orchestrator.patent_repo.list_patents(
        status=status,
        limit=limit,
        offset=offset,
    )
    return {
        "count": len(patents),
        "limit": limit,
        "offset": offset,
        "patents": patents,
    }


# ============================================================================
# Health Check
# ============================================================================

@router.get("/health")
async def health_check():
    """Health check for patent service."""
    return {
        "status": "healthy",
        "service": "patent-platform",
        "version": "0.1.0",
    }
