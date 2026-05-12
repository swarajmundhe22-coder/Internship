"""Unit tests for USPTO XML generation."""

import pytest
from uuid import uuid4
from app.models.patent import Patent, PatentJurisdiction, PatentStatus, PatentType, Inventor
from app.services.patent_filing_service import USPTOXMLGenerator, IndianPatentOfficeXMLGenerator


@pytest.fixture
def sample_patent():
    """Create a sample patent for testing."""
    return Patent(
        id=uuid4(),
        title="Novel Method for Corrosion Resistance",
        abstract="A method for applying electrochemical coatings to extend material lifespan in harsh environments.",
        technical_field="Materials Science and Electrochemistry",
        patent_type=PatentType.UTILITY,
        jurisdictions=[PatentJurisdiction.USPTO],
        embodiments=[
            "Using stainless steel 316L substrate",
            "Applying electroplating at controlled voltage",
            "Post-treatment with ceramic seal",
        ],
        claims_summary="A method comprising electrochemical coating of metallic substrates.",
        status=PatentStatus.DRAFT,
        inventors=[
            Inventor(
                name="Jane Smith",
                email="jane@example.com",
                country="US",
            )
        ],
    )


class TestUSPTOXMLGenerator:
    """Tests for USPTO XML generation."""

    def test_generate_filing_xml_basic(self, sample_patent):
        """Test basic USPTO XML generation."""
        generator = USPTOXMLGenerator()
        xml = generator.generate_filing_xml(
            patent=sample_patent,
            applicant_name="Jane Smith",
            applicant_address="123 Main St",
            applicant_city="San Francisco",
            applicant_state="CA",
            applicant_zip="94105",
        )

        # Verify XML is valid and contains key elements
        assert "<?xml" in xml or "<patent-application-publication" in xml
        assert "Novel Method for Corrosion Resistance" in xml
        assert "Jane Smith" in xml
        assert "San Francisco" in xml
        assert "SN2019-01" in xml

    def test_filing_xml_contains_claims(self, sample_patent):
        """Test that filing XML contains independent and dependent claims."""
        generator = USPTOXMLGenerator()
        xml = generator.generate_filing_xml(
            patent=sample_patent,
            applicant_name="Jane Smith",
            applicant_address="123 Main St",
            applicant_city="San Francisco",
            applicant_state="CA",
            applicant_zip="94105",
        )

        # Claims should be present
        assert "claim" in xml.lower()
        assert "independent" in xml.lower() or "dependent" in xml.lower()

    def test_filing_preview_generation(self, sample_patent):
        """Test filing preview generation."""
        generator = USPTOXMLGenerator()
        preview = generator.generate_filing_xml_preview(sample_patent, "Jane Smith")

        assert preview["title"] == sample_patent.title
        assert preview["applicant"] == "Jane Smith"
        assert preview["filing_fee"] == 330.0
        assert preview["claims_count"] >= 1
        assert "estimated_processing_time_months" in preview

    def test_independent_claim_generation(self, sample_patent):
        """Test that independent claim is generated from patent title."""
        generator = USPTOXMLGenerator()
        claim = generator._generate_independent_claim(sample_patent)

        assert "method" in claim.lower()
        assert "corrosion" in claim.lower()

    def test_dependent_claim_generation(self, sample_patent):
        """Test that dependent claims are generated from embodiments."""
        generator = USPTOXMLGenerator()
        dependent = generator._generate_dependent_claim(1, "Using stainless steel 316L")

        assert "2" in dependent  # Claim number
        assert "stainless steel" in dependent


class TestIndianPatentOfficeXMLGenerator:
    """Tests for Indian Patent Office XML generation."""

    def test_generate_filing_xml(self, sample_patent):
        """Test IPO XML generation."""
        generator = IndianPatentOfficeXMLGenerator()
        xml = generator.generate_filing_xml(
            patent=sample_patent,
            applicant_name="Jane Smith",
            applicant_address="123 Main St",
            applicant_city="Bangalore",
            applicant_state="KA",
            applicant_zip="560001",
        )

        assert "patent-application" in xml
        assert "Form 2" in xml
        assert "Jane Smith" in xml
        assert "Bangalore" in xml

    def test_filing_fee_currency(self, sample_patent):
        """Test that IPO filing fee is in INR."""
        generator = IndianPatentOfficeXMLGenerator()
        xml = generator.generate_filing_xml(
            patent=sample_patent,
            applicant_name="Jane Smith",
            applicant_address="123 Main St",
            applicant_city="Bangalore",
            applicant_state="KA",
            applicant_zip="560001",
        )

        assert "INR" in xml
        assert "1600" in xml  # IPO filing fee


class TestXMLValidation:
    """Tests for XML structure and compliance."""

    def test_uspto_xml_well_formed(self, sample_patent):
        """Test that USPTO XML is well-formed."""
        import xml.etree.ElementTree as ET

        generator = USPTOXMLGenerator()
        xml = generator.generate_filing_xml(
            patent=sample_patent,
            applicant_name="Jane Smith",
            applicant_address="123 Main St",
            applicant_city="San Francisco",
            applicant_state="CA",
            applicant_zip="94105",
        )

        # Should parse without errors
        try:
            root = ET.fromstring(xml)
            assert root is not None
        except ET.ParseError as e:
            pytest.fail(f"XML parsing failed: {e}")

    def test_ipo_xml_well_formed(self, sample_patent):
        """Test that IPO XML is well-formed."""
        import xml.etree.ElementTree as ET

        generator = IndianPatentOfficeXMLGenerator()
        xml = generator.generate_filing_xml(
            patent=sample_patent,
            applicant_name="Jane Smith",
            applicant_address="123 Main St",
            applicant_city="Bangalore",
            applicant_state="KA",
            applicant_zip="560001",
        )

        try:
            root = ET.fromstring(xml)
            assert root is not None
        except ET.ParseError as e:
            pytest.fail(f"XML parsing failed: {e}")
