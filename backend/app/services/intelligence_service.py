from __future__ import annotations

import asyncio
import hashlib
import json
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from app.core.config import get_settings
from app.models.auth import AuthPrincipal, UserRole
from app.models.intelligence import (
    AtlasExportJobRequest,
    AtlasExportJobResponse,
    AtlasExportResponse,
    AtlasGenerateResponse,
    AtlasLatestQuery,
    AtlasLatestResponse,
    AtlasRequest,
    IoTConnectorEvent,
    IoTIngestRequest,
    IoTIngestResponse,
    IoTStreamIngestRequest,
    IoTStreamIngestResponse,
    MaintenanceScheduleRequest,
    MaintenanceScheduleResponse,
    OpsSloResponse,
    SatelliteProviderSyncRequest,
    SatelliteProviderSyncResponse,
    SatelliteIngestRequest,
    SatelliteIngestResponse,
)
from app.repositories.intelligence_repository import IntelligenceRepository
from app.services.connector_adapter_service import ConnectorAdapterService, ConnectorPullRequest
from app.services.satellite_provider_client_service import SatelliteProviderClientService


class IntelligenceService:
    _rate_windows: dict[str, list[datetime]] = {}
    _rate_lock = asyncio.Lock()

    def __init__(
        self,
        repository: IntelligenceRepository,
        connector_adapter: ConnectorAdapterService | None = None,
        satellite_provider_client: SatelliteProviderClientService | None = None,
    ) -> None:
        self.repository = repository
        self.settings = get_settings()
        self.connector_adapter = connector_adapter or ConnectorAdapterService()
        self.satellite_provider_client = satellite_provider_client or SatelliteProviderClientService()

    async def ingest_iot(self, *, principal: AuthPrincipal, payload: IoTIngestRequest) -> IoTIngestResponse:
        await self._assert_tenant_access(principal=principal, tenant_id=payload.tenant_id)
        await self._enforce_rate_limit(tenant_id=payload.tenant_id, operation="iot.ingest")
        await self.repository.create_iot_data(
            tenant_id=payload.tenant_id,
            sensor_id=payload.sensor_id,
            payload=payload.payload,
        )
        return IoTIngestResponse(tenant_id=payload.tenant_id, sensor_id=payload.sensor_id)

    async def ingest_iot_stream(
        self,
        *,
        principal: AuthPrincipal,
        payload: IoTStreamIngestRequest,
    ) -> IoTStreamIngestResponse:
        await self._assert_tenant_access(principal=principal, tenant_id=payload.tenant_id)
        await self._enforce_rate_limit(tenant_id=payload.tenant_id, operation="iot.stream")

        events = list(payload.events)
        if not events:
            pulled = await self.connector_adapter.pull_events(
                ConnectorPullRequest(
                    connector_type=payload.connector_type,
                    tenant_id=str(payload.tenant_id),
                    max_events=payload.max_events,
                    topic=payload.topic,
                )
            )
            events.extend(pulled)

        accepted = 0
        dead_lettered = 0
        for item in events:
            try:
                await self._ingest_connector_event(tenant_id=payload.tenant_id, connector_type=payload.connector_type, item=item)
                accepted += 1
            except Exception as exc:
                dead_lettered += 1
                await self.repository.create_dead_letter(
                    tenant_id=payload.tenant_id,
                    event_source=f"iot.connector.{payload.connector_type}",
                    payload={"sensor_id": item.sensor_id, "payload": item.payload},
                    error_message=str(exc),
                    retry_count=0,
                )

        return IoTStreamIngestResponse(
            tenant_id=payload.tenant_id,
            connector_type=payload.connector_type,
            accepted_events=accepted,
            dead_lettered_events=dead_lettered,
        )

    async def ingest_satellite(
        self,
        *,
        principal: AuthPrincipal,
        payload: SatelliteIngestRequest,
    ) -> SatelliteIngestResponse:
        await self._assert_tenant_access(principal=principal, tenant_id=payload.tenant_id)
        await self._enforce_rate_limit(tenant_id=payload.tenant_id, operation="satellite.ingest")
        await self.repository.create_satellite_data(
            tenant_id=payload.tenant_id,
            region=payload.region,
            imagery_source=payload.imagery_source,
            metadata={"ingestion_mode": "satellite", "source": payload.imagery_source},
        )
        return SatelliteIngestResponse(tenant_id=payload.tenant_id, region=payload.region)

    async def sync_satellite_provider(
        self,
        *,
        principal: AuthPrincipal,
        payload: SatelliteProviderSyncRequest,
    ) -> SatelliteProviderSyncResponse:
        await self._assert_tenant_access(principal=principal, tenant_id=payload.tenant_id)
        await self._enforce_rate_limit(tenant_id=payload.tenant_id, operation="satellite.sync")

        provider_payload = await self._execute_with_retry(
            operation=f"satellite.provider.{payload.provider}",
            payload={"tenant_id": str(payload.tenant_id), "region": payload.region, "provider": payload.provider},
            tenant_id=payload.tenant_id,
            action=lambda: self.satellite_provider_client.fetch_imagery(
                provider=payload.provider,
                region=payload.region,
            ),
        )
        await self.repository.create_satellite_data(
            tenant_id=payload.tenant_id,
            region=payload.region,
            imagery_source=payload.provider,
            metadata=provider_payload,
        )
        frames = provider_payload.get("frames", []) if isinstance(provider_payload, dict) else []
        return SatelliteProviderSyncResponse(
            tenant_id=payload.tenant_id,
            region=payload.region,
            provider=payload.provider,
            frames_ingested=len(frames) if isinstance(frames, list) else 0,
        )

    async def generate_atlas(
        self,
        *,
        principal: AuthPrincipal,
        payload: AtlasRequest,
    ) -> AtlasGenerateResponse:
        await self._assert_tenant_access(principal=principal, tenant_id=payload.tenant_id)
        iot_rows = await self.repository.list_recent_iot(tenant_id=payload.tenant_id, limit=100)
        satellite_rows = await self.repository.list_recent_satellite(
            tenant_id=payload.tenant_id,
            region=payload.region,
            limit=30,
        )
        overlay_points, signal_stats = self._build_overlay_points(
            tenant_id=payload.tenant_id,
            region=payload.region,
            iot_rows=iot_rows,
            satellite_rows=satellite_rows,
        )
        atlas_row = await self.repository.create_atlas(
            tenant_id=payload.tenant_id,
            region=payload.region,
            atlas_key="risk_overlay",
            export_type=payload.export_type,
            metadata={
                "nvidia_enabled": bool(self.settings.nvidia_api_key),
                "overlay_profile": "global-risk-atlas",
                "overlay_points": overlay_points,
                "signal_stats": signal_stats,
            },
        )
        return AtlasGenerateResponse(
            tenant_id=payload.tenant_id,
            region=payload.region,
            metadata=self._parse_metadata(atlas_row.metadata_json),
        )

    async def export_atlas(
        self,
        *,
        principal: AuthPrincipal,
        payload: AtlasRequest,
    ) -> AtlasExportResponse:
        await self._assert_tenant_access(principal=principal, tenant_id=payload.tenant_id)
        latest = await self.repository.get_latest_atlas(tenant_id=payload.tenant_id, region=payload.region)
        prior_metadata = self._parse_metadata(getattr(latest, "metadata_json", "{}"))
        overlay_points = prior_metadata.get("overlay_points")
        if not isinstance(overlay_points, list):
            overlay_points = self._build_overlay_points(tenant_id=payload.tenant_id, region=payload.region)

        atlas_row = await self.repository.create_atlas(
            tenant_id=payload.tenant_id,
            region=payload.region,
            atlas_key="risk_overlay",
            export_type=payload.export_type,
            metadata={
                "export_intent": "compliance_deck",
                "status": "exported",
                "overlay_points": overlay_points,
            },
        )
        return AtlasExportResponse(
            tenant_id=payload.tenant_id,
            region=payload.region,
            export_type=payload.export_type,
            metadata=self._parse_metadata(atlas_row.metadata_json),
        )

    async def enqueue_export_job(
        self,
        *,
        principal: AuthPrincipal,
        payload: AtlasExportJobRequest,
    ) -> AtlasExportJobResponse:
        await self._assert_tenant_access(principal=principal, tenant_id=payload.tenant_id)
        await self._enforce_rate_limit(tenant_id=payload.tenant_id, operation="atlas.export.job")
        job = await self.repository.create_export_job(
            tenant_id=payload.tenant_id,
            region=payload.region,
            export_type=payload.export_type,
            max_attempts=self.settings.intelligence_retry_attempts,
            metadata={"queued_by": str(principal.user_id), "pipeline": "atlas-export-orchestrator"},
        )
        return self._to_export_job_response(job)

    async def process_export_job(self, *, job_id: UUID) -> AtlasExportJobResponse | None:
        job = await self.repository.get_export_job(job_id=job_id)
        if job is None:
            return None

        max_attempts = int(job.max_attempts)
        for attempt in range(1, max_attempts + 1):
            attempted_at = datetime.now(UTC)
            try:
                if job.export_type not in {"map_snapshot", "pdf", "mp4"}:
                    raise ValueError("Unsupported atlas export type")

                extension = "png" if job.export_type == "map_snapshot" else job.export_type
                output_uri = (
                    f"{self.settings.export_artifacts_dir}/atlas_{job.id}_{attempted_at.strftime('%Y%m%d%H%M%S')}.{extension}"
                )
                saved = await self.repository.update_export_job(
                    job_id=job.id,
                    status="completed",
                    attempt_count=attempt,
                    output_uri=output_uri,
                    last_error=None,
                    last_attempt_at=attempted_at,
                    completed_at=attempted_at,
                )
                if saved is None:
                    return None
                return self._to_export_job_response(saved)
            except Exception as exc:
                is_final = attempt >= max_attempts
                status = "failed" if is_final else "retrying"
                saved = await self.repository.update_export_job(
                    job_id=job.id,
                    status=status,
                    attempt_count=attempt,
                    output_uri=None,
                    last_error=str(exc),
                    last_attempt_at=attempted_at,
                    completed_at=attempted_at if is_final else None,
                )
                if is_final:
                    await self.repository.create_dead_letter(
                        tenant_id=job.tenant_id,
                        event_source="atlas.export.job",
                        payload={"job_id": str(job.id), "region": job.region, "export_type": job.export_type},
                        error_message=str(exc),
                        retry_count=attempt,
                    )
                    return self._to_export_job_response(saved) if saved else None

                delay_seconds = (self.settings.intelligence_retry_base_delay_ms * (2 ** (attempt - 1))) / 1000.0
                await asyncio.sleep(delay_seconds)

        refreshed = await self.repository.get_export_job(job_id=job_id)
        return self._to_export_job_response(refreshed) if refreshed else None

    async def get_export_job(self, *, principal: AuthPrincipal, job_id: UUID) -> AtlasExportJobResponse:
        job = await self.repository.get_export_job(job_id=job_id)
        if job is None:
            raise ValueError("Export job not found")
        await self._assert_tenant_access(principal=principal, tenant_id=job.tenant_id)
        return self._to_export_job_response(job)

    async def get_latest_atlas(
        self,
        *,
        principal: AuthPrincipal,
        query: AtlasLatestQuery,
    ) -> AtlasLatestResponse:
        await self._assert_tenant_access(principal=principal, tenant_id=query.tenant_id)
        atlas_row = await self.repository.get_latest_atlas(tenant_id=query.tenant_id, region=query.region)
        if atlas_row is None:
            raise ValueError("Atlas not found")
        return AtlasLatestResponse(
            tenant_id=atlas_row.tenant_id,
            region=atlas_row.region,
            atlas=atlas_row.atlas_key,
            export_type=atlas_row.export_type,
            metadata=self._parse_metadata(atlas_row.metadata_json),
            created_at=atlas_row.created_at,
        )

    async def get_ops_slo(
        self,
        *,
        principal: AuthPrincipal,
        tenant_id: UUID,
        window_hours: int = 24,
    ) -> OpsSloResponse:
        await self._assert_tenant_access(principal=principal, tenant_id=tenant_id)
        bounded_hours = max(1, min(window_hours, 168))
        since = datetime.now(UTC) - timedelta(hours=bounded_hours)

        iot_count = await self.repository.count_iot_since(tenant_id=tenant_id, since=since)
        satellite_count = await self.repository.count_satellite_since(tenant_id=tenant_id, since=since)
        exports_completed = await self.repository.count_export_jobs_since(
            tenant_id=tenant_id,
            since=since,
            status="completed",
        )
        exports_failed = await self.repository.count_export_jobs_since(
            tenant_id=tenant_id,
            since=since,
            status="failed",
        )
        dead_letters = await self.repository.count_dead_letters_since(tenant_id=tenant_id, since=since)

        total_ops = iot_count + satellite_count + exports_completed + exports_failed
        success_ratio = (iot_count + satellite_count + exports_completed) / total_ops if total_ops > 0 else 1.0

        return OpsSloResponse(
            tenant_id=tenant_id,
            window_hours=bounded_hours,
            iot_ingestion_events=iot_count,
            satellite_ingestion_events=satellite_count,
            atlas_exports_completed=exports_completed,
            atlas_exports_failed=exports_failed,
            dead_letter_events=dead_letters,
            success_ratio=round(success_ratio, 4),
        )

    async def schedule_maintenance(
        self,
        *,
        principal: AuthPrincipal,
        payload: MaintenanceScheduleRequest,
    ) -> MaintenanceScheduleResponse:
        await self._assert_tenant_access(principal=principal, tenant_id=payload.tenant_id)
        recommendation = "Immediate inspection" if payload.risk_score > 0.8 else "Routine check"
        await self.repository.create_maintenance_schedule(
            tenant_id=payload.tenant_id,
            asset_id=payload.asset_id,
            risk_score=payload.risk_score,
            recommendation=recommendation,
            metadata={"model": "phase9_rule_based", "risk_score": payload.risk_score},
        )
        return MaintenanceScheduleResponse(
            tenant_id=payload.tenant_id,
            asset_id=payload.asset_id,
            recommendation=recommendation,
        )

    async def _ingest_connector_event(self, *, tenant_id: UUID, connector_type: str, item: IoTConnectorEvent) -> None:
        payload = dict(item.payload)
        payload["connector_type"] = connector_type
        await self.repository.create_iot_data(
            tenant_id=tenant_id,
            sensor_id=item.sensor_id,
            payload=payload,
        )

    async def _enforce_rate_limit(self, *, tenant_id: UUID, operation: str) -> None:
        now = datetime.now(UTC)
        key = f"{tenant_id}:{operation}"
        async with self._rate_lock:
            bucket = self._rate_windows.get(key, [])
            cutoff = now - timedelta(minutes=1)
            bucket = [stamp for stamp in bucket if stamp >= cutoff]
            if len(bucket) >= self.settings.intelligence_rate_limit_per_minute:
                raise ValueError("Rate limit exceeded for operation")
            bucket.append(now)
            self._rate_windows[key] = bucket

    async def _execute_with_retry(
        self,
        *,
        operation: str,
        payload: dict[str, Any],
        tenant_id: UUID,
        action,
    ) -> dict[str, Any]:
        last_error = "Unknown provider error"
        for attempt in range(1, self.settings.intelligence_retry_attempts + 1):
            try:
                result = await action()
                if not isinstance(result, dict):
                    raise ValueError("Provider payload is invalid")
                return result
            except Exception as exc:
                last_error = str(exc)
                if attempt >= self.settings.intelligence_retry_attempts:
                    await self.repository.create_dead_letter(
                        tenant_id=tenant_id,
                        event_source=operation,
                        payload=payload,
                        error_message=last_error,
                        retry_count=attempt,
                    )
                    raise ValueError(last_error) from exc
                delay_seconds = (self.settings.intelligence_retry_base_delay_ms * (2 ** (attempt - 1))) / 1000.0
                await asyncio.sleep(delay_seconds)
        raise ValueError(last_error)

    async def _assert_tenant_access(self, *, principal: AuthPrincipal, tenant_id) -> None:
        if not await self.repository.tenant_exists(tenant_id):
            raise ValueError("Tenant not found")

        if principal.role == UserRole.admin:
            return

        if not await self.repository.user_in_tenant(user_id=principal.user_id, tenant_id=tenant_id):
            raise ValueError("User is not a member of tenant")

    @staticmethod
    def _parse_metadata(raw: str) -> dict[str, Any]:
        try:
            data = json.loads(raw)
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass
        return {}

    @staticmethod
    def _build_overlay_points(
        *,
        tenant_id: UUID,
        region: str,
        iot_rows: list[Any],
        satellite_rows: list[Any],
    ) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        digest = hashlib.sha256(f"{tenant_id}:{region}".encode("utf-8")).hexdigest()
        seed = int(digest[:8], 16)

        base_lat = (seed % 10000) / 100 - 50
        base_lon = ((seed // 100) % 30000) / 100 - 150

        avg_temp = 25.0
        avg_humidity = 60.0
        avg_chloride = 1500.0
        if iot_rows:
            temperatures: list[float] = []
            humidities: list[float] = []
            chlorides: list[float] = []
            for row in iot_rows:
                payload = IntelligenceService._parse_metadata(getattr(row, "payload_json", "{}"))
                temp = payload.get("temperature_c")
                humidity = payload.get("humidity_pct")
                chloride = payload.get("chloride_ppm")
                if isinstance(temp, (float, int)):
                    temperatures.append(float(temp))
                if isinstance(humidity, (float, int)):
                    humidities.append(float(humidity))
                if isinstance(chloride, (float, int)):
                    chlorides.append(float(chloride))
            if temperatures:
                avg_temp = sum(temperatures) / len(temperatures)
            if humidities:
                avg_humidity = sum(humidities) / len(humidities)
            if chlorides:
                avg_chloride = sum(chlorides) / len(chlorides)

        satellite_severity = 0.45
        if satellite_rows:
            values: list[float] = []
            for row in satellite_rows:
                metadata = IntelligenceService._parse_metadata(getattr(row, "metadata_json", "{}"))
                raw = metadata.get("severity_index")
                if isinstance(raw, (float, int)):
                    values.append(float(raw))
            if values:
                satellite_severity = sum(values) / len(values)

        model_score = min(
            1.0,
            max(
                0.0,
                (avg_temp / 65.0) * 0.25
                + (avg_humidity / 100.0) * 0.25
                + (min(avg_chloride, 15000.0) / 15000.0) * 0.3
                + satellite_severity * 0.2,
            ),
        )

        green_score = max(0.1, round(model_score * 0.45, 3))
        yellow_score = max(0.2, round(min(1.0, model_score * 0.85), 3))
        red_score = max(0.3, round(min(1.0, model_score * 1.08), 3))

        generated_at = datetime.now(UTC).isoformat()
        return [
            {
                "id": f"overlay-{digest[:8]}-0",
                "latitude": max(-70.0, min(70.0, base_lat)),
                "longitude": max(-175.0, min(175.0, base_lon)),
                "severity": "green",
                "score": green_score,
                "label": "Baseline corridor",
                "generated_at": generated_at,
            },
            {
                "id": f"overlay-{digest[:8]}-1",
                "latitude": max(-70.0, min(70.0, base_lat + 3.4)),
                "longitude": max(-175.0, min(175.0, base_lon + 4.9)),
                "severity": "yellow",
                "score": yellow_score,
                "label": "Escalation lane",
                "generated_at": generated_at,
            },
            {
                "id": f"overlay-{digest[:8]}-2",
                "latitude": max(-70.0, min(70.0, base_lat - 2.7)),
                "longitude": max(-175.0, min(175.0, base_lon - 5.3)),
                "severity": "red",
                "score": red_score,
                "label": "Critical hotspot",
                "generated_at": generated_at,
            },
        ], {
            "model": "phase9_geospatial_blend_v1",
            "avg_temperature_c": round(avg_temp, 3),
            "avg_humidity_pct": round(avg_humidity, 3),
            "avg_chloride_ppm": round(avg_chloride, 3),
            "satellite_severity": round(satellite_severity, 3),
            "model_score": round(model_score, 3),
            "input_iot_events": len(iot_rows),
            "input_satellite_frames": len(satellite_rows),
        }

    @staticmethod
    def _to_export_job_response(job: Any) -> AtlasExportJobResponse:
        return AtlasExportJobResponse(
            job_id=job.id,
            tenant_id=job.tenant_id,
            region=job.region,
            export_type=job.export_type,
            status=job.status,
            attempt_count=int(job.attempt_count),
            max_attempts=int(job.max_attempts),
            output_uri=job.output_uri,
            last_error=job.last_error,
        )
