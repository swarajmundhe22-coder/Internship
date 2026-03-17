from __future__ import annotations

from datetime import datetime, timezone

from app.core.config import get_settings
from app.models.report import ReportRecordRead


class ReportPdfService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def generate_pdf(self, report: ReportRecordRead) -> bytes:
        last_error: Exception | None = None
        for _attempt in range(1, self.settings.pdf_retry_attempts + 1):
            try:
                return self._render_pdf_document(report)
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                continue
        raise RuntimeError(f"PDF generation failed after {self.settings.pdf_retry_attempts} attempts") from last_error

    def _render_pdf_document(self, report: ReportRecordRead) -> bytes:
        generated = datetime.now(timezone.utc).isoformat()
        body = (
            "%PDF-1.4\n"
            "1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
            "2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
            "3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >> endobj\n"
            f"% The On Looker Report | report={report.id} | simulation={report.simulation_id} | status={report.status} | generated={generated}\n"
            "%%EOF\n"
        )
        return body.encode("utf-8")
