from __future__ import annotations

from datetime import datetime, timezone

from app.models.infrastructure import InfrastructureValidationResponse


class InfrastructureCompliancePdfService:
    def generate_pdf(self, validation: InfrastructureValidationResponse) -> bytes:
        generated = datetime.now(timezone.utc).isoformat()
        line_items = []
        for code_result in validation.code_results:
            governing = next(
                (item for item in code_result.limit_states if item.limit_state_id == code_result.governing_limit_state_id),
                code_result.limit_states[0],
            )
            line_items.append(
                " | ".join(
                    [
                        f"code={code_result.code_family.value}",
                        f"pass={code_result.passes}",
                        f"governing={governing.limit_state_id}",
                        f"util={governing.utilization_ratio:.4f}",
                        f"mos={governing.margin_of_safety:.4f}",
                    ]
                )
            )

        body = (
            "%PDF-1.4\n"
            "1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n"
            "2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n"
            "3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >> endobj\n"
            f"% Infrastructure Compliance Report | validation_id={validation.validation_id} | overall={validation.overall_passes} | stamped={generated}\n"
            f"% engine_version={validation.engine_version} | generated_at={validation.generated_at.isoformat()}\n"
            + "".join(f"% {line}\n" for line in line_items)
            + "%%EOF\n"
        )
        return body.encode("utf-8")
