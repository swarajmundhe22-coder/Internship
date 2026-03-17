import { useCallback, useState } from "react";

import {
  AddProjectCollaboratorRequest,
  AnalyticsSummary,
  AtlasExportResponse,
  AtlasGenerateResponse,
  AtlasLatestResponse,
  AtlasRequest,
  ApiError,
  IoTIngestRequest,
  IoTIngestResponse,
  MaintenanceScheduleRequest,
  MaintenanceScheduleResponse,
  ConsortiumDashboardResponse,
  ConsortiumManageRequest,
  ConsortiumMembershipResponse,
  DeckExportRequest,
  DeckExportResponse,
  DossierGenerateRequest,
  DossierGenerateResponse,
  ProjectActivityEvent,
  ProjectCollaborator,
  RiskDistributionDatum,
  SatelliteIngestRequest,
  SatelliteIngestResponse,
  SimulationsOverTimeDatum,
  UpdateProjectCollaboratorRequest,
  UsageDatum
} from "../types/domain";
import {
  apiFetch,
  apiFetchBlob,
  getProjectActivity
} from "../utils/api";

export function useApi() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [apiError, setApiError] = useState<ApiError | null>(null);

  const run = useCallback(async <T,>(path: string, init?: RequestInit): Promise<T> => {
    setLoading(true);
    setError(null);
    setApiError(null);
    try {
      return await apiFetch<T>(path, init);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown request failure";
      setError(message);
      if (err instanceof Error && "kind" in err) {
        setApiError(err as ApiError);
      }
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const runBlob = useCallback(async (path: string, init?: RequestInit): Promise<Blob> => {
    setLoading(true);
    setError(null);
    setApiError(null);
    try {
      return await apiFetchBlob(path, init);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown request failure";
      setError(message);
      if (err instanceof Error && "kind" in err) {
        setApiError(err as ApiError);
      }
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const collaboratorApi = {
    getProjectCollaborators: useCallback(
      async (projectId: string): Promise<ProjectCollaborator[]> => run(`/projects/${projectId}/collaborators`),
      [run]
    ),
    addProjectCollaborator: useCallback(
      async (projectId: string, payload: AddProjectCollaboratorRequest): Promise<ProjectCollaborator> =>
        run(`/projects/${projectId}/collaborators`, {
          method: "POST",
          body: JSON.stringify(payload)
        }),
      [run]
    ),
    updateProjectCollaborator: useCallback(
      async (
        projectId: string,
        userId: string,
        payload: UpdateProjectCollaboratorRequest
      ): Promise<ProjectCollaborator> =>
        run(`/projects/${projectId}/collaborators/${userId}`, {
          method: "PATCH",
          body: JSON.stringify(payload)
        }),
      [run]
    ),
    deleteProjectCollaborator: useCallback(
      async (projectId: string, userId: string): Promise<void> =>
        run(`/projects/${projectId}/collaborators/${userId}`, {
          method: "DELETE"
        }),
      [run]
    )
  };

  const analyticsApi = {
    getAnalyticsSummary: useCallback(async (): Promise<AnalyticsSummary> => run("/analytics/summary"), [run]),
    getMaterialUsage: useCallback(async (): Promise<UsageDatum[]> => run("/analytics/material-usage"), [run]),
    getEnvironmentUsage: useCallback(async (): Promise<UsageDatum[]> => run("/analytics/environment-usage"), [run]),
    getRiskDistribution: useCallback(async (): Promise<RiskDistributionDatum[]> => run("/analytics/risk-distribution"), [run]),
    getSimulationsOverTime: useCallback(async (): Promise<SimulationsOverTimeDatum[]> => run("/analytics/simulations-over-time"), [run])
  };

  const reportApi = {
    downloadReportPdf: useCallback(async (reportId: string): Promise<Blob> => runBlob(`/reports/${reportId}/pdf`), [runBlob])
  };

  const activityApi = {
    getProjectActivity: useCallback(
      async (
        projectId: string,
        filters?: { user_id?: string; action?: string; created_from?: string; created_to?: string }
      ): Promise<ProjectActivityEvent[]> => {
        const payload = await getProjectActivity(projectId, filters);
        return Array.isArray(payload) ? payload : payload.items;
      },
      []
    )
  };

  const intelligenceApi = {
    ingestIoT: useCallback(
      async (payload: IoTIngestRequest): Promise<IoTIngestResponse> =>
        run<IoTIngestResponse>("/intelligence/iot/ingest", {
          method: "POST",
          body: JSON.stringify(payload)
        }),
      [run]
    ),
    ingestSatellite: useCallback(
      async (payload: SatelliteIngestRequest): Promise<SatelliteIngestResponse> =>
        run<SatelliteIngestResponse>("/intelligence/satellite/ingest", {
          method: "POST",
          body: JSON.stringify(payload)
        }),
      [run]
    ),
    generateAtlas: useCallback(
      async (payload: AtlasRequest): Promise<AtlasGenerateResponse> =>
        run<AtlasGenerateResponse>("/intelligence/atlas/generate", {
          method: "POST",
          body: JSON.stringify(payload)
        }),
      [run]
    ),
    exportAtlas: useCallback(
      async (payload: AtlasRequest): Promise<AtlasExportResponse> =>
        run<AtlasExportResponse>("/intelligence/atlas/export", {
          method: "POST",
          body: JSON.stringify(payload)
        }),
      [run]
    ),
    getLatestAtlas: useCallback(
      async (tenantId: string, region: string): Promise<AtlasLatestResponse> =>
        run<AtlasLatestResponse>(
          `/intelligence/atlas/latest?tenant_id=${encodeURIComponent(tenantId)}&region=${encodeURIComponent(region)}`
        ),
      [run]
    ),
    scheduleMaintenance: useCallback(
      async (payload: MaintenanceScheduleRequest): Promise<MaintenanceScheduleResponse> =>
        run<MaintenanceScheduleResponse>("/intelligence/maintenance/schedule", {
          method: "POST",
          body: JSON.stringify(payload)
        }),
      [run]
    )
  };

  const governanceApi = {
    generateDossier: useCallback(
      async (payload: DossierGenerateRequest): Promise<DossierGenerateResponse> =>
        run<DossierGenerateResponse>("/dossier/generate", {
          method: "POST",
          body: JSON.stringify(payload)
        }),
      [run]
    ),
    exportDeck: useCallback(
      async (payload: DeckExportRequest): Promise<DeckExportResponse> =>
        run<DeckExportResponse>("/deck/export", {
          method: "POST",
          body: JSON.stringify(payload)
        }),
      [run]
    ),
    manageConsortium: useCallback(
      async (payload: ConsortiumManageRequest): Promise<ConsortiumMembershipResponse> =>
        run<ConsortiumMembershipResponse>("/consortium/manage", {
          method: "POST",
          body: JSON.stringify(payload)
        }),
      [run]
    ),
    getConsortiumDashboard: useCallback(
      async (tenantId: string): Promise<ConsortiumDashboardResponse> =>
        run<ConsortiumDashboardResponse>(`/consortium/dashboard?tenant_id=${encodeURIComponent(tenantId)}`),
      [run]
    )
  };

  return {
    run,
    runBlob,
    loading,
    error,
    apiError,
    ...collaboratorApi,
    ...reportApi,
    ...analyticsApi,
    ...activityApi,
    ...intelligenceApi,
    ...governanceApi
  };
}
