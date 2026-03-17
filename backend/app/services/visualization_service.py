from __future__ import annotations

import json
from uuid import UUID

from app.models.auth import AuthPrincipal, UserRole
from app.models.visualization import (
    VisualizationExportRead,
    VisualizationExportResponse,
    VisualizationMode,
    VisualizationPlaybackResponse,
    VisualizationRead,
)
from app.repositories.visualization_repository import VisualizationRepository
from app.services.cinematic_render_service import CinematicRenderService


class VisualizationService:
    def __init__(self, repository: VisualizationRepository, minimum_overlay_accuracy: float = 0.95) -> None:
        self.repository = repository
        self.minimum_overlay_accuracy = minimum_overlay_accuracy
        self.renderer = CinematicRenderService()

    async def auto_generate_twin(self, *, simulation_id: UUID, tenant_id: UUID | None) -> VisualizationRead | None:
        simulation = await self.repository.get_simulation(simulation_id)
        if simulation is None:
            return None

        overlay_accuracy = self._resolve_overlay_accuracy(simulation.accuracy_score)
        metadata = self._build_twin_metadata(simulation_id=simulation.id, risk=simulation.risk_classification)
        status = "generated" if overlay_accuracy >= self.minimum_overlay_accuracy else "pending_validation"

        visualization = await self.repository.create_visualization(
            simulation_id=simulation.id,
            tenant_id=tenant_id,
            mode=VisualizationMode.TWIN,
            metadata=metadata,
            status=status,
            overlay_accuracy=overlay_accuracy,
        )
        return self._to_visualization_read(visualization)

    async def generate_twin(self, *, principal: AuthPrincipal, simulation_id: UUID, tenant_id: UUID) -> VisualizationRead:
        await self._assert_tenant_access(principal=principal, simulation_id=simulation_id, tenant_id=tenant_id)

        simulation = await self.repository.get_simulation(simulation_id)
        if simulation is None:
            raise ValueError("Simulation not found")

        overlay_accuracy = self._resolve_overlay_accuracy(simulation.accuracy_score)
        if overlay_accuracy < self.minimum_overlay_accuracy:
            raise ValueError("Predictive overlay accuracy must be >= 0.95")

        metadata = self._build_twin_metadata(simulation_id=simulation.id, risk=simulation.risk_classification)
        visualization = await self.repository.create_visualization(
            simulation_id=simulation.id,
            tenant_id=tenant_id,
            mode=VisualizationMode.TWIN,
            metadata=metadata,
            status="generated",
            overlay_accuracy=overlay_accuracy,
        )
        return self._to_visualization_read(visualization)

    async def playback(self, *, principal: AuthPrincipal, simulation_id: UUID, tenant_id: UUID, mode: str) -> VisualizationPlaybackResponse:
        await self._assert_tenant_access(principal=principal, simulation_id=simulation_id, tenant_id=tenant_id)
        if mode not in VisualizationMode.ALL:
            raise ValueError("Unsupported visualization mode")

        existing = await self.repository.get_latest_visualization(
            simulation_id=simulation_id,
            tenant_id=tenant_id,
            mode=mode,
        )
        if existing is None:
            twin = await self.generate_twin(principal=principal, simulation_id=simulation_id, tenant_id=tenant_id)
            if mode == VisualizationMode.TWIN:
                visualization = twin
            else:
                visualization_entity = await self.repository.create_visualization(
                    simulation_id=simulation_id,
                    tenant_id=tenant_id,
                    mode=mode,
                    metadata=twin.metadata,
                    status="playback_ready",
                    overlay_accuracy=twin.overlay_accuracy,
                )
                visualization = self._to_visualization_read(visualization_entity)
        else:
            visualization = self._to_visualization_read(existing)

        frames = visualization.metadata.get("timeline_frames", []) if isinstance(visualization.metadata, dict) else []
        return VisualizationPlaybackResponse(
            visualization=visualization,
            tenant_id=tenant_id,
            simulation_id=simulation_id,
            mode=mode,
            timeline_frames=frames if isinstance(frames, list) else [],
            playback_hud={
                "mission_state": "sandboxed",
                "risk_hotspots": visualization.metadata.get("hotspots", []),
                "time_slider_enabled": True,
                "webxr_ready": mode in {VisualizationMode.AR, VisualizationMode.VR},
            },
        )

    async def export(
        self,
        *,
        principal: AuthPrincipal,
        simulation_id: UUID,
        tenant_id: UUID,
        mode: str,
        file_type: str,
    ) -> VisualizationExportResponse:
        playback = await self.playback(
            principal=principal,
            simulation_id=simulation_id,
            tenant_id=tenant_id,
            mode=mode,
        )
        if file_type.lower() not in {"pdf", "mp4"}:
            raise ValueError("file_type must be pdf or mp4")

        file_extension = file_type.lower()
        file_uri = self.renderer.render(
            visualization_id=playback.visualization.id,
            tenant_id=tenant_id,
            file_type=file_extension,
            metadata=playback.visualization.metadata,
        )
        export_row = await self.repository.create_export(
            visualization_id=playback.visualization.id,
            tenant_id=tenant_id,
            file_type=file_extension,
            file_uri=file_uri,
        )
        return VisualizationExportResponse(
            tenant_id=tenant_id,
            simulation_id=simulation_id,
            mode=mode,
            export=VisualizationExportRead.model_validate(export_row),
        )

    async def _assert_tenant_access(self, *, principal: AuthPrincipal, simulation_id: UUID, tenant_id: UUID) -> None:
        if principal.role != UserRole.admin:
            if not await self.repository.user_in_tenant(user_id=principal.user_id, tenant_id=tenant_id):
                raise ValueError("User is not a member of tenant")

        if not await self.repository.simulation_in_tenant(simulation_id=simulation_id, tenant_id=tenant_id):
            raise ValueError("Simulation is not bound to tenant")

    @staticmethod
    def _resolve_overlay_accuracy(accuracy_score: float | None) -> float:
        if accuracy_score is None:
            return 0.95
        return float(accuracy_score)

    @staticmethod
    def _build_twin_metadata(*, simulation_id: UUID, risk: str) -> dict[str, object]:
        frames = [
            {"minute": 0, "severity": "green", "risk_score": 0.24, "degradation_pct": 3.0},
            {"minute": 12, "severity": "yellow", "risk_score": 0.58, "degradation_pct": 22.0},
            {"minute": 24, "severity": "red", "risk_score": 0.86, "degradation_pct": 47.0},
        ]
        return {
            "simulation_id": str(simulation_id),
            "asset_type": "industrial_asset",
            "scene_profile": "glass_hud_holographic",
            "risk_classification": risk,
            "hotspots": [
                {"name": "Joint-A", "severity": "yellow", "x": -1.2, "y": 0.4, "z": 2.1},
                {"name": "Valve-C", "severity": "red", "x": 0.6, "y": 1.0, "z": -0.8},
            ],
            "timeline_frames": frames,
            "color_scale": {"green": "#22c55e", "yellow": "#facc15", "red": "#ef4444"},
            "investor_narrative": "Risk intensifies along stress joints; maintenance intervention reduces projected failure corridor.",
        }

    @staticmethod
    def _to_visualization_read(entity: object) -> VisualizationRead:
        raw_metadata = getattr(entity, "metadata_json", "{}")
        metadata: dict[str, object] = {}
        if isinstance(raw_metadata, str):
            try:
                parsed = json.loads(raw_metadata)
                if isinstance(parsed, dict):
                    metadata = parsed
            except json.JSONDecodeError:
                metadata = {}

        return VisualizationRead(
            id=getattr(entity, "id"),
            simulation_id=getattr(entity, "simulation_id"),
            tenant_id=getattr(entity, "tenant_id"),
            mode=getattr(entity, "mode"),
            status=getattr(entity, "status"),
            overlay_accuracy=float(getattr(entity, "overlay_accuracy")),
            metadata=metadata,
            created_at=getattr(entity, "created_at"),
            updated_at=getattr(entity, "updated_at"),
        )
