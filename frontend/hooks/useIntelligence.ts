import { useMemo, useState } from "react";

import {
  AtlasExportResponse,
  AtlasGenerateResponse,
  AtlasLatestResponse,
  AtlasOverlayPoint,
  AtlasRequest,
  IoTIngestRequest,
  IoTIngestResponse,
  MaintenanceScheduleRequest,
  MaintenanceScheduleResponse,
  SatelliteIngestRequest,
  SatelliteIngestResponse
} from "../types/domain";
import { useApi } from "./useApi";

type IntelligenceHistory = {
  iot?: IoTIngestResponse;
  satellite?: SatelliteIngestResponse;
  atlasGenerated?: AtlasGenerateResponse;
  atlasExported?: AtlasExportResponse;
  atlasLatest?: AtlasLatestResponse;
  maintenance?: MaintenanceScheduleResponse;
};

function asOverlayPoints(input: unknown): AtlasOverlayPoint[] {
  if (!Array.isArray(input)) {
    return [];
  }

  return input
    .filter((item): item is Record<string, unknown> => Boolean(item) && typeof item === "object")
    .map((item) => ({
      id: String(item.id ?? "overlay-unknown"),
      latitude: Number(item.latitude ?? 0),
      longitude: Number(item.longitude ?? 0),
      severity:
        item.severity === "red" || item.severity === "yellow" || item.severity === "green"
          ? item.severity
          : "green",
      score: Number(item.score ?? 0),
      label: String(item.label ?? "Overlay")
    }));
}

export function useIntelligence() {
  const {
    ingestIoT,
    ingestSatellite,
    generateAtlas,
    exportAtlas,
    getLatestAtlas,
    scheduleMaintenance,
    loading,
    error,
    apiError
  } = useApi();

  const [history, setHistory] = useState<IntelligenceHistory>({});

  const overlayPoints = useMemo(() => {
    if (history.atlasLatest?.metadata?.overlay_points) {
      return asOverlayPoints(history.atlasLatest.metadata.overlay_points);
    }
    if (history.atlasExported?.metadata?.overlay_points) {
      return asOverlayPoints(history.atlasExported.metadata.overlay_points);
    }
    if (history.atlasGenerated?.metadata?.overlay_points) {
      return asOverlayPoints(history.atlasGenerated.metadata.overlay_points);
    }
    return [];
  }, [history.atlasLatest, history.atlasExported, history.atlasGenerated]);

  async function runIoTIngest(payload: IoTIngestRequest): Promise<IoTIngestResponse> {
    const result = await ingestIoT(payload);
    setHistory((prev) => ({ ...prev, iot: result }));
    return result;
  }

  async function runSatelliteIngest(payload: SatelliteIngestRequest): Promise<SatelliteIngestResponse> {
    const result = await ingestSatellite(payload);
    setHistory((prev) => ({ ...prev, satellite: result }));
    return result;
  }

  async function runAtlasGenerate(payload: AtlasRequest): Promise<AtlasGenerateResponse> {
    const result = await generateAtlas(payload);
    setHistory((prev) => ({ ...prev, atlasGenerated: result }));
    return result;
  }

  async function runAtlasExport(payload: AtlasRequest): Promise<AtlasExportResponse> {
    const result = await exportAtlas(payload);
    setHistory((prev) => ({ ...prev, atlasExported: result }));
    return result;
  }

  async function loadLatestAtlas(tenantId: string, region: string): Promise<AtlasLatestResponse> {
    const result = await getLatestAtlas(tenantId, region);
    setHistory((prev) => ({ ...prev, atlasLatest: result }));
    return result;
  }

  async function runMaintenanceSchedule(
    payload: MaintenanceScheduleRequest
  ): Promise<MaintenanceScheduleResponse> {
    const result = await scheduleMaintenance(payload);
    setHistory((prev) => ({ ...prev, maintenance: result }));
    return result;
  }

  return {
    loading,
    error,
    apiError,
    history,
    overlayPoints,
    runIoTIngest,
    runSatelliteIngest,
    runAtlasGenerate,
    runAtlasExport,
    loadLatestAtlas,
    runMaintenanceSchedule
  };
}
