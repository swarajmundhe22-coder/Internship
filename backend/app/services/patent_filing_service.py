"""USPTO EFS-Web XML generation for mechanical patent filing.

Generates XML compatible with USPTO Form SN2019-01 (Utility Patent Application).
Reference: USPTO EFS-Web specifications
"""

import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from app.models.patent import Patent, PatentFilingTemplateUSA


class USPTOXMLGenerator:
    """Generates USPTO EFS-Web XML for mechanical patent applications."""

    def __init__(self):
        self.form_sn = "SN2019-01"
        self.filing_fee = 330.0  # USD

    def generate_filing_xml(
        self,
        patent: Patent,
        applicant_name: str,
        applicant_address: str,
        applicant_city: str,
        applicant_state: str,
        applicant_zip: str,
    ) -> str:
        """
        Generate USPTO EFS-Web XML for utility patent filing.

        Args:
            patent: Patent object with title, abstract, claims
            applicant_name: Full name of primary inventor/applicant
            applicant_address: Street address
            applicant_city: City
            applicant_state: State code (e.g., 'CA')
            applicant_zip: ZIP code

        Returns:
            XML string ready for USPTO EFS-Web submission

        """
        root = ET.Element("patent-application-publication")
        root.set("id", str(patent.id))
        root.set("date", datetime.now(timezone.utc).isoformat())

        # 1. Filing metadata
        filings = ET.SubElement(root, "filings")
        filing = ET.SubElement(filings, "filing")
        ET.SubElement(filing, "filing-type").text = "UTILITY"
        ET.SubElement(filing, "application-type").text = "nonprovisional"
        ET.SubElement(filing, "form-type").text = "SN2019-01"
        ET.SubElement(filing, "filing-fee-paid").text = str(self.filing_fee)

        # 2. Bibliographic data
        biblio = ET.SubElement(root, "bibliographic-data")
        ET.SubElement(biblio, "application-reference").text = str(patent.id)[:8]

        invention = ET.SubElement(biblio, "invention-title")
        invention.text = patent.title
        invention.set("xml:lang", "en")

        # 3. Abstract
        abstract_elem = ET.SubElement(biblio, "abstract")
        abstract_elem.text = patent.abstract
        abstract_elem.set("xml:lang", "en")

        # 4. Technical field
        technical = ET.SubElement(biblio, "technical-field")
        technical.text = patent.technical_field

        # 5. Applicant/Inventor information
        applicants = ET.SubElement(biblio, "applicants")
        applicant = ET.SubElement(applicants, "applicant")
        applicant.set("app-type", "applicant")

        addressbook = ET.SubElement(applicant, "addressbook")
        ET.SubElement(addressbook, "name").text = applicant_name
        address = ET.SubElement(addressbook, "address")
        ET.SubElement(address, "street").text = applicant_address
        ET.SubElement(address, "city").text = applicant_city
        ET.SubElement(address, "state").text = applicant_state
        ET.SubElement(address, "postcode").text = applicant_zip
        ET.SubElement(address, "country").text = "US"

        # 6. Claims section
        claims = ET.SubElement(biblio, "claims")
        claim_num = 1

        # Independent claim (required minimum)
        independent_claim = ET.SubElement(claims, "claim")
        independent_claim.set("id", f"CLM-{claim_num:04d}")
        independent_claim.set("num", str(claim_num))
        independent_claim.set("claim-type", "independent")

        claim_text = self._generate_independent_claim(patent)
        claim_para = ET.SubElement(independent_claim, "claim-text")
        claim_para.text = claim_text
        claim_num += 1

        # Generate dependent claims from embodiments
        if patent.embodiments:
            for i, embodiment in enumerate(patent.embodiments[:5], 1):  # Limit to 5 dependent claims
                dependent = ET.SubElement(claims, "claim")
                dependent.set("id", f"CLM-{claim_num:04d}")
                dependent.set("num", str(claim_num))
                dependent.set("claim-type", "dependent")
                dependent.set("depends-on", "1")

                dep_text = self._generate_dependent_claim(i, embodiment)
                dep_para = ET.SubElement(dependent, "claim-text")
                dep_para.text = dep_text
                claim_num += 1

        # 7. Description (technical specification)
        description = ET.SubElement(biblio, "description")
        ET.SubElement(description, "mode-title").text = "DETAILED DESCRIPTION"

        # Detailed description
        detailed = patent.detailed_description or self._generate_detailed_description(patent)
        desc_para = ET.SubElement(description, "description-text")
        desc_para.text = detailed[:2000]  # Limit to 2000 chars for MVP

        # Pretty print and return
        self._indent_xml(root)
        return ET.tostring(root, encoding="unicode")

    def _generate_independent_claim(self, patent: Patent) -> str:
        """Generate the independent claim (claim 1) for the patent."""
        title_text = (patent.title or "").strip()
        lower_title = title_text.lower()
        prefixes = (
            "novel method for",
            "method for",
            "system for",
            "apparatus for",
        )
        claim_focus = title_text
        for prefix in prefixes:
            if lower_title.startswith(prefix):
                claim_focus = title_text[len(prefix):].strip() or patent.technical_field
                break
        if not claim_focus:
            claim_focus = patent.technical_field

        return (
            f"1. A method for {claim_focus.lower()}, comprising: "
            f"providing a {patent.embodiments[0] if patent.embodiments else 'technical component'}; "
            "and processing said component according to the detailed description below."
        )

    def _generate_dependent_claim(self, claim_num: int, embodiment: str) -> str:
        """Generate dependent claims based on embodiments."""
        return (
            f"{claim_num + 1}. The method of claim 1, wherein said component comprises: "
            f"{embodiment}."
        )

    def _generate_detailed_description(self, patent: Patent) -> str:
        """Generate boilerplate detailed description if not provided."""
        lines = [
            "DETAILED DESCRIPTION OF THE INVENTION",
            f"The present invention relates to {patent.technical_field}.",
            f"The invention provides the following technical advantages:",
        ]
        for embodiment in patent.embodiments[:3]:
            lines.append(f"- {embodiment}")
        lines.append(
            "The implementation details are shown in the figures and specification below."
        )
        return "\n\n".join(lines)

    def generate_filing_xml_preview(
        self,
        patent: Patent,
        applicant_name: str,
    ) -> dict:
        """
        Generate a preview of the filing for USPTO submission.

        Returns a dict with key filing information.
        """
        return {
            "application_id": str(patent.id)[:8],
            "title": patent.title,
            "abstract": patent.abstract,
            "field": patent.technical_field,
            "applicant": applicant_name,
            "claims_count": 1 + min(len(patent.embodiments), 5),
            "filing_fee": self.filing_fee,
            "estimated_processing_time_months": 18,
        }

    @staticmethod
    def _indent_xml(elem, level=0):
        """Add pretty-print indentation to XML."""
        indent = "\n" + level * "  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = indent + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = indent
            for child in elem:
                USPTOXMLGenerator._indent_xml(child, level + 1)
            if not child.tail or not child.tail.strip():
                child.tail = indent
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = indent


class IndianPatentOfficeXMLGenerator:
    """Generates XML for Indian Patent Office (IPO) Form 2 filing."""

    def __init__(self):
        self.form_number = "Form 2"
        self.filing_fee = 1600.0  # INR for small entity

    def generate_filing_xml(
        self,
        patent: Patent,
        applicant_name: str,
        applicant_address: str,
        applicant_city: str,
        applicant_state: str,
        applicant_zip: str,
    ) -> str:
        """Generate Indian Patent Office Form 2 XML."""
        root = ET.Element("patent-application")
        root.set("form", self.form_number)
        root.set("date", datetime.now(timezone.utc).isoformat())

        # IPO-specific: Patent specification
        specification = ET.SubElement(root, "specification")
        title = ET.SubElement(specification, "title")
        title.text = patent.title
        title.set("lang", "en")

        abstract = ET.SubElement(specification, "abstract")
        abstract.text = patent.abstract
        abstract.set("lang", "en")

        # Field of invention
        field = ET.SubElement(specification, "field-of-invention")
        field.text = patent.technical_field

        # Applicant details (same as summary)
        applicants = ET.SubElement(root, "applicants")
        applicant = ET.SubElement(applicants, "applicant")
        ET.SubElement(applicant, "name").text = applicant_name
        addr = ET.SubElement(applicant, "address")
        ET.SubElement(addr, "street").text = applicant_address
        ET.SubElement(addr, "city").text = applicant_city
        ET.SubElement(addr, "state").text = applicant_state
        ET.SubElement(addr, "postal").text = applicant_zip

        # Claims
        claims = ET.SubElement(root, "claims")
        claim = ET.SubElement(claims, "claim")
        claim.set("number", "1")
        claim_text = ET.SubElement(claim, "claim-text")
        claim_text.text = (
            f"A method for {patent.technical_field.lower()} comprising the features "
            "outlined in the detailed specification."
        )

        # Filing fee
        ET.SubElement(root, "filing-fee").text = f"INR {self.filing_fee}"

        self._indent_xml(root)
        return ET.tostring(root, encoding="unicode")

    @staticmethod
    def _indent_xml(elem, level=0):
        """Add pretty-print indentation to XML."""
        indent = "\n" + level * "  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = indent + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = indent
            for child in elem:
                IndianPatentOfficeXMLGenerator._indent_xml(child, level + 1)
            if not child.tail or not child.tail.strip():
                child.tail = indent
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = indent
