export type PaginatedResponse<T> = {
  items: T[];
  total: number;
  page: number;
  page_size: number;
};

export type Material = {
  id: string;
  name: string;
  alloy_group: string;
  density_kg_m3: number;
  electrochemical_potential_v: number;
  created_at: string;
  updated_at: string;
};

export type EnvironmentProfile = {
  id: string;
  profile_name: string;
  temperature_c: number;
  relative_humidity_pct: number;
  chloride_ppm: number;
  ph: number;
  dissolved_oxygen_mg_l: number;
  created_at: string;
  updated_at: string;
};

export type SimulationRecord = {
  id: string;
  material_id: string;
  environment_id: string;
  exposed_area_m2: number;
  exposure_time_hours: number;
  corrosion_rate_mm_per_year: number;
  estimated_lifespan_years: number;
  risk_classification: string;
  version: number;
  created_at: string;
  updated_at: string;
};

export type SimulationPrediction = {
  simulation_id: string;
  generated_at: string;
  corrosion_rate_mm_per_year: number;
  estimated_lifespan_years: number;
  risk_classification: string;
  recommendation_summary: string;
  environment_risk: {
    risk_score: number;
    risk_band: string;
    rationale: string;
  };
};

export type ReportRecord = {
  id: string;
  simulation_id: string;
  report_uri: string;
  status: string;
  version: number;
  created_at: string;
  updated_at: string;
};

export type BaseListQueryParams = {
  page: number;
  page_size: number;
};

export type MaterialListQueryParams = BaseListQueryParams & {
  created_from?: string;
  created_to?: string;
};

export type EnvironmentListQueryParams = BaseListQueryParams & {
  created_from?: string;
  created_to?: string;
};

export type SimulationListQueryParams = BaseListQueryParams & {
  material_id?: string;
  environment_id?: string;
  risk_level?: string;
  created_from?: string;
  created_to?: string;
};

export type ReportListQueryParams = BaseListQueryParams & {
  simulation_id?: string;
  created_from?: string;
  created_to?: string;
};

export type ApiErrorKind = "concurrency" | "http" | "network";

export type ApiError = Error & {
  status?: number;
  detail?: string;
  kind: ApiErrorKind;
};

export type GeneratedReport = {
  generated_at: string;
  simulation_id: string;
  material: Record<string, string | number>;
  environment: Record<string, string | number>;
  metrics: Record<string, string | number>;
  recommendation_summary: string;
  visual_summary: {
    intensity_map: Array<{ label: string; value: number }>;
  };
};

export type SimulationComparisonResponse = {
  left_simulation_id: string;
  right_simulation_id: string;
  corrosion_rate_delta_mm_per_year: number;
  lifespan_delta_years: number;
  risk_transition: string;
  environmental_deltas: Record<string, number>;
  material_deltas: Record<string, number>;
};

export type AuthTokenResponse = {
  access_token: string;
  refresh_token?: string;
  token_type: "bearer";
};

export type RegistrationOtpChallengeResponse = {
  message: string;
  email: string;
  expires_in_seconds: number;
  dev_otp?: string | null;
};

export type DemoRequestPayload = {
  full_name: string;
  email: string;
  company: string;
  role: string;
  use_case: string;
  preferred_auth_provider: "email" | "google" | "apple";
};

export type DemoRequestResponse = {
  request_id: string;
  message: string;
  booking_url: string;
};

export type Project = {
  id: string;
  user_id: string;
  name: string;
  created_at: string;
  updated_at: string;
};

export type ProjectSimulationSummary = {
  simulation_id: string;
  material: string;
  environment: string;
  risk_level: string;
  lifespan_years: number;
  created_at: string;
};

export type ProjectDetail = {
  id: string;
  name: string;
  created_at: string;
  simulations: PaginatedResponse<ProjectSimulationSummary>;
};

export type ProjectReportSummary = {
  report_id: string;
  report_uri: string;
  simulation_id: string;
  material: string;
  environment: string;
  simulation_risk_level: string;
  risk_level: string;
  lifespan_years: number;
  created_at: string;
};

export type ComparisonSetListItem = {
  id: string;
  project_id: string;
  name: string;
  created_by: string;
  created_at: string;
  simulation_count: number;
};

export type ComparisonSetDetail = {
  id: string;
  project_id: string;
  name: string;
  created_by: string;
  created_at: string;
  simulation_ids: string[];
  comparisons: SimulationComparisonResponse[];
};

export type ProjectRole = "Owner" | "Collaborator" | "Viewer";

export type ProjectCollaborator = {
  user_id: string;
  email: string;
  role: ProjectRole;
  joined_at?: string;
};

export type AddProjectCollaboratorRequest = {
  email: string;
  role: ProjectRole;
};

export type UpdateProjectCollaboratorRequest = {
  role: ProjectRole;
};

export type AnalyticsSummary = {
  total_simulations: number;
  total_reports: number;
  high_risk_count: number;
};

export type UsageDatum = {
  name: string;
  count: number;
};

export type RiskDistributionDatum = {
  risk_level: string;
  count: number;
};

export type SimulationsOverTimeDatum = {
  bucket: string;
  count: number;
};

export type ProjectActivityEvent = {
  id: string;
  project_id: string;
  user_id: string;
  user_email?: string;
  action: string;
  timestamp: string;
  metadata: Record<string, string | number | boolean | null>;
};

export type AuditLogRecord = {
  id: string;
  event_type: string;
  user_id?: string | null;
  user_email?: string | null;
  success: boolean;
  detail?: string | null;
  created_at: string;
};

export type PredictionTimelinePoint = {
  offset_hours: number;
  corrosion_rate_mm_per_year: number;
  estimated_lifespan_years: number;
  risk_score: number;
  risk_classification: string;
};

export type ProjectPredictionRecord = {
  id: string;
  project_id: string;
  simulation_id?: string | null;
  model_name: string;
  horizon_hours: number;
  step_hours: number;
  summary: string;
  timeline: PredictionTimelinePoint[];
  created_at: string;
};

export type ProjectInsightAnomaly = {
  code: string;
  severity: string;
  message: string;
};

export type ProjectInsight = {
  project_id: string;
  generated_at: string;
  summary: string;
  recommendations: string[];
  anomalies: ProjectInsightAnomaly[];
};

export type ApiTokenRecord = {
  id: string;
  token_prefix: string;
  name: string;
  scopes: string[];
  is_active: boolean;
  expires_at?: string | null;
  created_at: string;
  revoked_at?: string | null;
};

export type ApiTokenCreateResponse = {
  id: string;
  token: string;
  token_prefix: string;
  name: string;
  scopes: string[];
  expires_at?: string | null;
  created_at: string;
};

export type WebhookRecord = {
  id: string;
  event_type: string;
  target_url: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
};

export type WebhookDeliveryLogRecord = {
  id: string;
  webhook_subscription_id: string;
  event_type: string;
  attempt_count: number;
  max_attempts: number;
  success: boolean;
  http_status?: number | null;
  error_message?: string | null;
  first_attempt_at?: string | null;
  last_attempt_at?: string | null;
  next_retry_at?: string | null;
  delivered_at?: string | null;
  created_at: string;
};

export type VisualizationMode = "twin" | "ar" | "vr";

export type TwinHotspot = {
  name: string;
  severity: string;
  x: number;
  y: number;
  z: number;
};

export type VisualizationRecord = {
  id: string;
  simulation_id: string;
  tenant_id?: string | null;
  mode: VisualizationMode;
  status: string;
  overlay_accuracy: number;
  metadata: {
    asset_type?: string;
    scene_profile?: string;
    risk_classification?: string;
    hotspots?: TwinHotspot[];
    timeline_frames?: Array<Record<string, string | number | boolean>>;
    color_scale?: Record<string, string>;
    investor_narrative?: string;
  };
  created_at: string;
  updated_at: string;
};

export type VisualizationPlaybackResponse = {
  visualization: VisualizationRecord;
  tenant_id: string;
  simulation_id: string;
  mode: VisualizationMode;
  timeline_frames: Array<Record<string, string | number | boolean>>;
  playback_hud: Record<string, unknown>;
  status: string;
};

export type VisualizationExportResponse = {
  tenant_id: string;
  simulation_id: string;
  mode: VisualizationMode;
  status: string;
  export: {
    id: string;
    visualization_id: string;
    tenant_id?: string | null;
    file_type: string;
    file_uri: string;
    created_at: string;
  };
};

export type IoTIngestRequest = {
  tenant_id: string;
  sensor_id: string;
  payload: Record<string, unknown>;
};

export type IoTIngestResponse = {
  tenant_id: string;
  sensor_id: string;
  status: "ingested";
};

export type SatelliteIngestRequest = {
  tenant_id: string;
  region: string;
  imagery_source: string;
};

export type SatelliteIngestResponse = {
  tenant_id: string;
  region: string;
  status: "imagery_ingested";
};

export type AtlasRequest = {
  tenant_id: string;
  region: string;
  export_type: "map_snapshot" | "pdf" | "mp4";
};

export type AtlasGenerateResponse = {
  tenant_id: string;
  region: string;
  atlas: "risk_overlay";
  metadata: {
    nvidia_enabled?: boolean;
    overlay_profile?: string;
    overlay_points?: AtlasOverlayPoint[];
  };
  status: "generated";
};

export type AtlasExportResponse = {
  tenant_id: string;
  region: string;
  export_type: "map_snapshot" | "pdf" | "mp4";
  metadata: {
    export_intent?: string;
    status?: string;
    overlay_points?: AtlasOverlayPoint[];
  };
  status: "exported";
};

export type AtlasLatestResponse = {
  tenant_id: string;
  region: string;
  atlas: string;
  export_type: string;
  metadata: {
    overlay_points?: AtlasOverlayPoint[];
    [key: string]: unknown;
  };
  created_at: string;
};

export type MaintenanceScheduleRequest = {
  tenant_id: string;
  asset_id: string;
  risk_score: number;
};

export type MaintenanceScheduleResponse = {
  tenant_id: string;
  asset_id: string;
  recommendation: string;
};

export type AtlasOverlayPoint = {
  id: string;
  latitude: number;
  longitude: number;
  severity: "green" | "yellow" | "red";
  score: number;
  label: string;
};

export type DossierGenerateRequest = {
  tenant_id: string;
  simulation_id: string;
  format: "pdf" | "json" | "xml";
  industry_module: string;
};

export type DossierGenerateResponse = {
  dossier_id: string;
  tenant_id: string;
  simulation_id: string;
  format: string;
  industry_module: string;
  artifact_uri: string;
  status: "generated";
};

export type DeckExportRequest = {
  tenant_id: string;
  project_id: string;
  export_type: "pptx" | "pdf" | "mp4";
};

export type DeckExportResponse = {
  deck_id: string;
  tenant_id: string;
  project_id: string;
  export_type: string;
  artifact_uri: string;
  status: "exported";
};

export type ConsortiumManageRequest = {
  tenant_id: string;
  action: "join" | "upgrade" | "downgrade";
};

export type ConsortiumMembershipResponse = {
  id: string;
  tenant_id: string;
  tier: string;
  status: string;
  created_at: string;
  updated_at: string;
};

export type ConsortiumDashboardResponse = {
  tenant_id: string;
  tier: string;
  compliance_status: string;
  foresight_index: number;
  consortium_voting_enabled: boolean;
  active_dossiers_30d: number;
  active_decks_30d: number;
  generated_at: string;
};
