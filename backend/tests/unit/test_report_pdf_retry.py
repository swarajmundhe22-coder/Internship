from __future__ import annotations

from uuid import uuid4

from app.models.report import ReportRecordRead
from app.services.report_pdf_service import ReportPdfService


def test_pdf_retry_succeeds_after_transient_failure(monkeypatch) -> None:
    service = ReportPdfService()
    attempts = {"count": 0}

    def flaky_renderer(_report: ReportRecordRead) -> bytes:
        attempts["count"] += 1
        if attempts["count"] == 1:
            raise RuntimeError("transient")
        return b"%PDF-1.4\nmock\n%%EOF\n"

    monkeypatch.setattr(service, "_render_pdf_document", flaky_renderer)

    report = ReportRecordRead(
        id=uuid4(),
        simulation_id=uuid4(),
        report_uri="s3://reports/retry.pdf",
        status="generated",
        version=1,
    )

    data = service.generate_pdf(report)
    assert data.startswith(b"%PDF")
    assert attempts["count"] == 2
