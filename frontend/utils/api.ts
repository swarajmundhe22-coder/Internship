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

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

function toApiError(status: number, detail: string): ApiError {
  const isConcurrency = status === 409 && /(conflict|version|stale)/i.test(detail);
  const error = new Error(detail) as ApiError;
  error.status = status;
  error.detail = detail;
  error.kind = isConcurrency ? "concurrency" : "http";
  return error;
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const authToken = typeof window !== "undefined" ? window.localStorage.getItem("onlooker_token") : null;

  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      headers: {
        "Content-Type": "application/json",
        ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
        ...(init?.headers ?? {})
      },
      ...init
    });
  } catch (err) {
    const error = new Error(err instanceof Error ? err.message : "Network request failed") as ApiError;
    error.kind = "network";
    throw error;
  }

  if (!response.ok) {
    const text = await response.text();
    throw toApiError(response.status, text || `Request failed: ${response.status}`);
  }

  return (await response.json()) as T;
}

export async function apiFetchBlob(path: string, init?: RequestInit): Promise<Blob> {
  const authToken = typeof window !== "undefined" ? window.localStorage.getItem("onlooker_token") : null;

  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      headers: {
        ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
        ...(init?.headers ?? {})
      },
      ...init
    });
  } catch (err) {
    const error = new Error(err instanceof Error ? err.message : "Network request failed") as ApiError;
    error.kind = "network";
    throw error;
  }

  if (!response.ok) {
    const text = await response.text();
    throw toApiError(response.status, text || `Request failed: ${response.status}`);
  }

  return await response.blob();
}

function buildQuery(params: Record<string, string | undefined>): string {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (!value) {
      return;
    }
    query.set(key, value);
  });
  const serialized = query.toString();
  return serialized ? `?${serialized}` : "";
}

export function getProjectCollaborators(projectId: string): Promise<ProjectCollaborator[]> {
  return apiFetch<ProjectCollaborator[]>(`/projects/${projectId}/collaborators`);
}

export function addProjectCollaborator(
  projectId: string,
  payload: AddProjectCollaboratorRequest
): Promise<ProjectCollaborator> {
  return apiFetch<ProjectCollaborator>(`/projects/${projectId}/collaborators`, {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function updateProjectCollaborator(
  projectId: string,
  userId: string,
  payload: UpdateProjectCollaboratorRequest
): Promise<ProjectCollaborator> {
  return apiFetch<ProjectCollaborator>(`/projects/${projectId}/collaborators/${userId}`, {
    method: "PATCH",
    body: JSON.stringify(payload)
  });
}

export function deleteProjectCollaborator(projectId: string, userId: string): Promise<void> {
  return apiFetch<void>(`/projects/${projectId}/collaborators/${userId}`, {
    method: "DELETE"
  });
}

export function downloadReportPdf(reportId: string): Promise<Blob> {
  return apiFetchBlob(`/reports/${reportId}/pdf`);
}

export function getAnalyticsSummary(): Promise<AnalyticsSummary> {
  return apiFetch<AnalyticsSummary>("/analytics/summary");
}

export function getMaterialUsage(): Promise<UsageDatum[]> {
  return apiFetch<UsageDatum[]>("/analytics/material-usage");
}

export function getEnvironmentUsage(): Promise<UsageDatum[]> {
  return apiFetch<UsageDatum[]>("/analytics/environment-usage");
}

export function getRiskDistribution(): Promise<RiskDistributionDatum[]> {
  return apiFetch<RiskDistributionDatum[]>("/analytics/risk-distribution");
}

export function getSimulationsOverTime(): Promise<SimulationsOverTimeDatum[]> {
  return apiFetch<SimulationsOverTimeDatum[]>("/analytics/simulations-over-time");
}

export function getProjectActivity(
  projectId: string,
  filters?: {
    user_id?: string;
    action?: string;
    created_from?: string;
    created_to?: string;
  }
): Promise<ProjectActivityEvent[] | { items: ProjectActivityEvent[] }> {
  const query = buildQuery({
    user_id: filters?.user_id,
    action: filters?.action,
    created_from: filters?.created_from,
    created_to: filters?.created_to
  });
  return apiFetch<ProjectActivityEvent[] | { items: ProjectActivityEvent[] }>(`/projects/${projectId}/activity${query}`);
}

export function ingestIoT(payload: IoTIngestRequest): Promise<IoTIngestResponse> {
  return apiFetch<IoTIngestResponse>("/intelligence/iot/ingest", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function ingestSatellite(payload: SatelliteIngestRequest): Promise<SatelliteIngestResponse> {
  return apiFetch<SatelliteIngestResponse>("/intelligence/satellite/ingest", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function generateAtlas(payload: AtlasRequest): Promise<AtlasGenerateResponse> {
  return apiFetch<AtlasGenerateResponse>("/intelligence/atlas/generate", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function exportAtlas(payload: AtlasRequest): Promise<AtlasExportResponse> {
  return apiFetch<AtlasExportResponse>("/intelligence/atlas/export", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function getLatestAtlas(tenantId: string, region: string): Promise<AtlasLatestResponse> {
  const query = buildQuery({ tenant_id: tenantId, region });
  return apiFetch<AtlasLatestResponse>(`/intelligence/atlas/latest${query}`);
}

export function scheduleMaintenance(payload: MaintenanceScheduleRequest): Promise<MaintenanceScheduleResponse> {
  return apiFetch<MaintenanceScheduleResponse>("/intelligence/maintenance/schedule", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function generateDossier(payload: DossierGenerateRequest): Promise<DossierGenerateResponse> {
  return apiFetch<DossierGenerateResponse>("/dossier/generate", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function exportDeck(payload: DeckExportRequest): Promise<DeckExportResponse> {
  return apiFetch<DeckExportResponse>("/deck/export", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function manageConsortium(payload: ConsortiumManageRequest): Promise<ConsortiumMembershipResponse> {
  return apiFetch<ConsortiumMembershipResponse>("/consortium/manage", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export function getConsortiumDashboard(tenantId: string): Promise<ConsortiumDashboardResponse> {
  const query = buildQuery({ tenant_id: tenantId });
  return apiFetch<ConsortiumDashboardResponse>(`/consortium/dashboard${query}`);
}
