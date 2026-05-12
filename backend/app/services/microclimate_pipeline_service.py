from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

from app.algorithms.microclimate_engine import interpolate_weather_snapshot
from app.models.infrastructure import (
    HourlyWeatherUpdateRecord,
    HourlyWeatherUpdateRequest,
    HourlyWeatherUpdateResponse,
)


class MicroClimatePipelineService:
    def __init__(self, *, audit_log_path: Path | None = None) -> None:
        backend_root = Path(__file__).resolve().parents[2]
        self.audit_log_path = audit_log_path or backend_root / "artifacts" / "security_reports" / "microclimate_interpolation_audit.jsonl"

    def run_hourly_update(self, payload: HourlyWeatherUpdateRequest) -> HourlyWeatherUpdateResponse:
        generated_at = datetime.now(timezone.utc)
        self.audit_log_path.parent.mkdir(parents=True, exist_ok=True)

        records: list[HourlyWeatherUpdateRecord] = []
        with self.audit_log_path.open("a", encoding="utf-8") as handle:
            for target in payload.targets:
                snapshot = interpolate_weather_snapshot(
                    location=target,
                    exposure_category=payload.exposure_category,
                    structure_height_ft=60.0,
                    reference_timestamp_utc=generated_at,
                )
                record = HourlyWeatherUpdateRecord(location=target, snapshot=snapshot)
                records.append(record)

                audit_payload = {
                    "generated_at_utc": generated_at.isoformat(),
                    "location": target.model_dump(mode="json"),
                    "snapshot": snapshot.model_dump(mode="json"),
                }
                handle.write(json.dumps(audit_payload, ensure_ascii=True) + "\n")

        return HourlyWeatherUpdateResponse(
            generated_at=generated_at,
            record_count=len(records),
            audit_log_path=str(self.audit_log_path),
            records=records,
        )
