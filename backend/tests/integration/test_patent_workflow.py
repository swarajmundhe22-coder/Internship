"""Integration tests for patent filing workflow."""

import pytest
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import StaticPool

from app.database.patent_models import Base
from app.models.patent import PatentJurisdiction, PatentStatus, PatentType, Inventor
from app.services.patent_orchestration_service import PatentFilingOrchestrator


@pytest.fixture
async def async_session():
    """Create an in-memory async SQLite session for testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    from sqlalchemy.ext.asyncio import AsyncSession as AS

    async_session = AS(engine, expire_on_commit=False)
    yield async_session
    await async_session.close()
    await engine.dispose()


class TestPatentFilingWorkflow:
    """Integration tests for complete patent filing workflow."""

    @pytest.mark.asyncio
    async def test_create_draft_patent(self, async_session: AsyncSession):
        """Test creating a draft patent."""
        orchestrator = PatentFilingOrchestrator(async_session)

        patent = await orchestrator.create_draft_patent(
            title="Test Patent",
            abstract="A test patent abstract",
            technical_field="Materials Science",
            actor_email="test@example.com",
        )

        assert patent.title == "Test Patent"
        assert patent.status == PatentStatus.DRAFT
        assert patent.id is not None

    @pytest.mark.asyncio
    async def test_add_embodiments(self, async_session: AsyncSession):
        """Test adding embodiments to patent."""
        orchestrator = PatentFilingOrchestrator(async_session)

        # Create patent
        patent = await orchestrator.create_draft_patent(
            title="Test Patent",
            abstract="A test patent abstract",
            technical_field="Materials Science",
            actor_email="test@example.com",
        )

        # Add embodiments
        updated = await orchestrator.add_embodiments(
            patent_id=patent.id,
            embodiments=["Uses stainless steel", "High temperature resistant"],
            actor_email="test@example.com",
        )

        assert len(updated.embodiments) == 2
        assert "stainless steel" in updated.embodiments[0]

    @pytest.mark.asyncio
    async def test_set_claims_summary(self, async_session: AsyncSession):
        """Test setting claims summary."""
        orchestrator = PatentFilingOrchestrator(async_session)

        patent = await orchestrator.create_draft_patent(
            title="Test Patent",
            abstract="A test patent abstract",
            technical_field="Materials Science",
            actor_email="test@example.com",
        )

        updated = await orchestrator.set_claims_summary(
            patent_id=patent.id,
            claims_summary="A method comprising the steps described below",
            actor_email="test@example.com",
        )

        assert updated.claims_summary is not None
        assert "method" in updated.claims_summary.lower()

    @pytest.mark.asyncio
    async def test_filing_preview_generation(self, async_session: AsyncSession):
        """Test generating filing preview."""
        orchestrator = PatentFilingOrchestrator(async_session)

        # Create and populate patent
        patent = await orchestrator.create_draft_patent(
            title="Test Patent",
            abstract="A test patent abstract",
            technical_field="Materials Science",
            actor_email="test@example.com",
        )

        preview = await orchestrator.generate_filing_preview(
            patent_id=patent.id,
            jurisdiction=PatentJurisdiction.USPTO,
            applicant_name="Test User",
        )

        assert preview["title"] == "Test Patent"
        assert preview["filing_fee"] == 330.0
        assert "application_id" in preview

    @pytest.mark.asyncio
    async def test_submit_for_filing(self, async_session: AsyncSession):
        """Test submitting patent for filing."""
        orchestrator = PatentFilingOrchestrator(async_session)

        # Create and populate patent
        patent = await orchestrator.create_draft_patent(
            title="Test Patent",
            abstract="A test abstract",
            technical_field="Materials Science",
            actor_email="test@example.com",
        )

        await orchestrator.add_embodiments(
            patent_id=patent.id,
            embodiments=["Embodiment 1"],
            actor_email="test@example.com",
        )

        await orchestrator.set_claims_summary(
            patent_id=patent.id,
            claims_summary="Test claims summary",
            actor_email="test@example.com",
        )

        # Submit for filing
        result = await orchestrator.submit_for_filing(
            request=type("PatentFilingRequest", (), {
                "patent_id": patent.id,
                "jurisdiction": PatentJurisdiction.USPTO,
            })(),
            applicant_name="Test User",
            applicant_address="123 Main St",
            applicant_city="Test City",
            applicant_state="CA",
            applicant_zip="94105",
            actor_email="test@example.com",
        )

        assert result["status"] == "success"
        assert "filing_xml" in result

    @pytest.mark.asyncio
    async def test_mark_as_filed(self, async_session: AsyncSession):
        """Test marking patent as filed."""
        orchestrator = PatentFilingOrchestrator(async_session)

        patent = await orchestrator.create_draft_patent(
            title="Test Patent",
            abstract="A test patent",
            technical_field="Materials Science",
            actor_email="test@example.com",
        )

        marked = await orchestrator.mark_as_filed(
            patent_id=patent.id,
            jurisdiction=PatentJurisdiction.USPTO,
            application_number="US2026123456",
            actor_email="test@example.com",
        )

        assert marked.status == PatentStatus.FILED
        assert marked.uspto_application_number == "US2026123456"
        assert marked.filed_at is not None

    @pytest.mark.asyncio
    async def test_audit_trail_logging(self, async_session: AsyncSession):
        """Test that audit trail is recorded for actions."""
        orchestrator = PatentFilingOrchestrator(async_session)

        patent = await orchestrator.create_draft_patent(
            title="Test Patent",
            abstract="Test abstract",
            technical_field="Materials Science",
            actor_email="test@example.com",
        )

        trail = await orchestrator.get_audit_trail(patent.id)

        # Should have at least creation entry
        assert len(trail) >= 1
        assert any(entry["action"] == "CREATED" for entry in trail)

    @pytest.mark.asyncio
    async def test_get_patent_status(self, async_session: AsyncSession):
        """Test getting detailed patent status."""
        orchestrator = PatentFilingOrchestrator(async_session)

        patent = await orchestrator.create_draft_patent(
            title="Test Patent",
            abstract="Test abstract",
            technical_field="Materials Science",
            actor_email="test@example.com",
        )

        status = await orchestrator.get_patent_status(patent.id)

        assert status["id"] == str(patent.id)
        assert status["title"] == "Test Patent"
        assert "progress" in status
        assert "status" in status

    @pytest.mark.asyncio
    async def test_progress_calculation(self, async_session: AsyncSession):
        """Test patent progress calculation."""
        orchestrator = PatentFilingOrchestrator(async_session)

        patent = await orchestrator.create_draft_patent(
            title="Test Patent",
            abstract="Test abstract",
            technical_field="Materials Science",
            actor_email="test@example.com",
        )

        # Initial progress should be > 0 (has title and abstract)
        status1 = await orchestrator.get_patent_status(patent.id)
        progress1 = status1["progress"]
        assert progress1 > 0

        # Add embodiments
        await orchestrator.add_embodiments(
            patent_id=patent.id,
            embodiments=["Embodiment 1", "Embodiment 2"],
            actor_email="test@example.com",
        )

        # Progress should increase
        status2 = await orchestrator.get_patent_status(patent.id)
        progress2 = status2["progress"]
        assert progress2 > progress1


class TestMaterialDatabase:
    """Integration tests for material database."""

    @pytest.mark.asyncio
    async def test_material_lookup(self, async_session: AsyncSession):
        """Test looking up material by name."""
        orchestrator = PatentFilingOrchestrator(async_session)

        from app.models.patent import Material

        # Create a material
        material = Material(
            name="Test Steel 304",
            material_type="metal",
            density=8.0,
            youngs_modulus=193.0,
            tensile_strength=515.0,
            corrosion_resistance="excellent",
            source="Test Source",
        )

        await orchestrator.material_repo.create_material(material)

        # Look it up
        found = await orchestrator.lookup_material("Test Steel 304")

        assert found is not None
        assert found["name"] == "Test Steel 304"
        assert found["density"] == 8.0

    @pytest.mark.asyncio
    async def test_list_materials_by_type(self, async_session: AsyncSession):
        """Test listing materials by type."""
        orchestrator = PatentFilingOrchestrator(async_session)

        from app.models.patent import Material

        # Create materials
        for i in range(3):
            material = Material(
                name=f"Steel {i}",
                material_type="metal",
                density=7.8,
                youngs_modulus=200.0,
                tensile_strength=400.0,
                corrosion_resistance="good",
                source="Test",
            )
            await orchestrator.material_repo.create_material(material)

        # List them
        materials = await orchestrator.list_materials_by_type("metal", limit=10)

        assert len(materials) >= 3
