import { apiFetch } from "../../../utils/api";
import { executeCriticalApiRequest, toErrorSummary } from "./resilience";
import { createTraceContext, emitDomainEvent, type TraceContext } from "./telemetry";

type PaginatedResponse<T> = {
  items: T[];
  total: number;
  page: number;
  page_size: number;
};

type MaterialRecord = {
  id: string;
  name: string;
  alloy_group: string;
  density_kg_m3: number;
  electrochemical_potential_v: number;
  created_at: string;
  updated_at: string;
};

type EnvironmentRecord = {
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

type EnvironmentInput = {
  temperature_c: number;
  relative_humidity_pct: number;
  chloride_ppm: number;
  ph: number;
  dissolved_oxygen_mg_l: number;
};

type MetricConfidenceIntervalRecord = {
  lower: number;
  upper: number;
  confidence_level: number;
};

type SimulationUncertaintyBandsRecord = {
  corrosion_rate_mm_per_year?: MetricConfidenceIntervalRecord;
  design_corrosion_rate_mm_per_year?: MetricConfidenceIntervalRecord;
  estimated_lifespan_years?: MetricConfidenceIntervalRecord;
  composite_risk_score?: MetricConfidenceIntervalRecord;
};

type SimulationAlgorithmResult = {
  simulation_id: string;
  generated_at: string;
  environment_risk: {
    risk_score: number;
    risk_band: string;
    rationale: string;
  };
  corrosion_rate_mm_per_year: number;
  design_corrosion_rate_mm_per_year?: number;
  composite_risk_score?: number;
  estimated_lifespan_years: number;
  risk_classification: string;
  recommendation_summary: string;
  model_version?: string;
  asset_profile?: string;
  region_key?: string;
  region_name?: string;
  initial_thickness_mm?: number;
  minimum_safe_thickness_mm?: number;
  calibration_confidence?: number;
  uncertainty_bands?: SimulationUncertaintyBandsRecord;
};

type SimulationRecord = {
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

type CopilotResponse = {
  response: string;
  model: string;
};

export type SimulationInputPayload = {
  material?: string;
  customMaterial?: string;
  structure?: string;
  customStructure?: string;
  compliance?: string;
  criticality?: string;
  region?: string;
  temperature?: number;
  humidity?: number;
  salinity?: number;
  pH?: number;
  oxygenLevel?: number;
  uvIndex?: number;
  micActivity?: string;
  soilResistivity?: number;
  assetValue?: number;
  downtimeCost?: number;
};

export type MetricConfidenceIntervalPayload = {
  lower: number;
  upper: number;
  confidenceLevel: number;
};

export type SimulationUncertaintyPayload = {
  corrosionRate?: MetricConfidenceIntervalPayload;
  designCorrosionRate?: MetricConfidenceIntervalPayload;
  predictedLifespan?: MetricConfidenceIntervalPayload;
  riskScore?: MetricConfidenceIntervalPayload;
};

export type SimulationResultPayload = {
  riskScore: number;
  corrosionRate: number;
  designCorrosionRate?: number;
  predictedLifespan: number;
  degradationTimeline: Array<{ year: number; thickness: number }>;
  capexRequirement: number;
  projectedROI: number;
  lifecycleExtension: number;
  esgCompliance: number;
  interventions: Array<{ title: string; description: string; status: string }>;
  recommendationSummary: string;
  riskBand: string;
  backendSimulationId: string;
  modelVersion?: string;
  assetProfile?: string;
  regionKey?: string;
  regionName?: string;
  initialThicknessMm?: number;
  minimumSafeThicknessMm?: number;
  calibrationConfidence?: number;
  uncertaintyBands?: SimulationUncertaintyPayload;
};

export type TokenClaims = {
  sub: string;
  email: string;
  role: string;
  sid?: string;
  exp?: number;
};

export type CriticalRequestOptions = {
  traceId?: string;
  actorId?: string;
  projectId?: string;
};

const DEFAULT_EXPOSURE_HOURS = 24 * 365;

function buildTraceContext(options?: CriticalRequestOptions): TraceContext {
  return createTraceContext({
    traceId: options?.traceId,
    actorId: options?.actorId,
    projectId: options?.projectId,
  });
}

function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}

function parseJwtClaims(token: string): TokenClaims | null {
  const parts = token.split(".");
  if (parts.length < 2) {
    return null;
  }

  try {
    const b64 = parts[1].replace(/-/g, "+").replace(/_/g, "/");
    const padded = b64.padEnd(Math.ceil(b64.length / 4) * 4, "=");
    const decoded = atob(padded);
    const json = decodeURIComponent(
      decoded
        .split("")
        .map((char) => `%${(`00${char.charCodeAt(0).toString(16)}`).slice(-2)}`)
        .join("")
    );
    return JSON.parse(json) as TokenClaims;
  } catch {
    return null;
  }
}

export function getAccessTokenClaims(): TokenClaims | null {
  if (typeof window === "undefined") {
    return null;
  }
  const token = window.localStorage.getItem("onlooker_token");
  if (!token) {
    return null;
  }
  return parseJwtClaims(token);
}

function resolveMaterialProfile(label: string): {
  name: string;
  alloy_group: string;
  density_kg_m3: number;
  electrochemical_potential_v: number;
} {
  const name = (label || "Custom Alloy").trim();
  const normalized = name.toLowerCase();

  if (normalized.includes("carbon steel") || normalized.includes("a36") || normalized.includes("a516")) {
    return {
      name,
      alloy_group: "Ferrous",
      density_kg_m3: 7850,
      electrochemical_potential_v: -0.65
    };
  }

  if (normalized.includes("stainless") && normalized.includes("316")) {
    return {
      name,
      alloy_group: "Austenitic Stainless",
      density_kg_m3: 8000,
      electrochemical_potential_v: -0.15
    };
  }

  if (normalized.includes("stainless") && normalized.includes("304")) {
    return {
      name,
      alloy_group: "Austenitic Stainless",
      density_kg_m3: 7930,
      electrochemical_potential_v: -0.2
    };
  }

  if (normalized.includes("duplex") || normalized.includes("2205")) {
    return {
      name,
      alloy_group: "Duplex Stainless",
      density_kg_m3: 7800,
      electrochemical_potential_v: -0.1
    };
  }

  if (normalized.includes("aluminum") || normalized.includes("aluminium")) {
    return {
      name,
      alloy_group: "Aluminum Alloy",
      density_kg_m3: 2700,
      electrochemical_potential_v: -0.9
    };
  }

  if (normalized.includes("titanium")) {
    return {
      name,
      alloy_group: "Titanium",
      density_kg_m3: 4500,
      electrochemical_potential_v: 0.2
    };
  }

  if (normalized.includes("nickel") || normalized.includes("inconel")) {
    return {
      name,
      alloy_group: "Nickel Alloy",
      density_kg_m3: 8440,
      electrochemical_potential_v: 0.1
    };
  }

  return {
    name,
    alloy_group: "Custom Alloy",
    density_kg_m3: 7800,
    electrochemical_potential_v: -0.25
  };
}

async function listMaterials(traceContext: TraceContext): Promise<MaterialRecord[]> {
  const payload = await executeCriticalApiRequest(
    () => apiFetch<PaginatedResponse<MaterialRecord>>("/materials?page=1&page_size=200"),
    {
      operation: "materials.list",
      path: "/materials",
      method: "GET",
      traceContext,
      maxAttempts: 3,
    }
  );
  return payload.items;
}

async function ensureMaterial(materialName: string, traceContext: TraceContext): Promise<MaterialRecord> {
  const normalizedName = materialName.trim().toLowerCase();
  const existing = (await listMaterials(traceContext)).find((item) => item.name.trim().toLowerCase() === normalizedName);
  if (existing) {
    return existing;
  }

  const profile = resolveMaterialProfile(materialName);
  try {
    return await executeCriticalApiRequest(
      () =>
        apiFetch<MaterialRecord>("/materials", {
          method: "POST",
          body: JSON.stringify(profile)
        }),
      {
        operation: "materials.create",
        path: "/materials",
        method: "POST",
        traceContext,
        maxAttempts: 3,
      }
    );
  } catch (error) {
    const conflict = error instanceof Error && "status" in error && (error as { status?: number }).status === 409;
    if (!conflict) {
      throw error;
    }

    const retry = (await listMaterials(traceContext)).find((item) => item.name.trim().toLowerCase() === normalizedName);
    if (!retry) {
      throw error;
    }
    return retry;
  }
}

function buildEnvironmentInput(input: SimulationInputPayload): EnvironmentInput {
  return {
    temperature_c: clamp(Number(input.temperature ?? 25), -60, 150),
    relative_humidity_pct: clamp(Number(input.humidity ?? 70), 0, 100),
    chloride_ppm: Math.max(0, Number(input.salinity ?? 35) * 1000),
    ph: clamp(Number(input.pH ?? 7), 0, 14),
    dissolved_oxygen_mg_l: Math.max(0, Number(input.oxygenLevel ?? 6))
  };
}

async function createEnvironmentRecord(
  input: SimulationInputPayload,
  structureLabel: string,
  traceContext: TraceContext
): Promise<EnvironmentRecord> {
  const payload = buildEnvironmentInput(input);
  const timestamp = new Date().toISOString().replace(/[.:]/g, "-");

  return await executeCriticalApiRequest(
    () =>
      apiFetch<EnvironmentRecord>("/environment", {
        method: "POST",
        body: JSON.stringify({
          profile_name: `${structureLabel.slice(0, 48) || "Generated"}-${timestamp}`,
          ...payload
        })
      }),
    {
      operation: "environment.create",
      path: "/environment",
      method: "POST",
      traceContext,
      maxAttempts: 3,
    }
  );
}

function estimateExposedAreaM2(structureLabel: string): number {
  const normalized = structureLabel.toLowerCase();
  if (normalized.includes("pipeline")) return 180;
  if (normalized.includes("bridge")) return 260;
  if (normalized.includes("offshore") || normalized.includes("platform")) return 420;
  if (normalized.includes("tank")) return 320;
  return 140;
}

function buildTimeline(corrosionRateMmPerYear: number, baseThicknessMm: number = 12): Array<{ year: number; thickness: number }> {
  const years = [0, 5, 10, 15, 20];
  return years.map((year) => {
    const consumedMm = corrosionRateMmPerYear * year;
    const remainingMm = Math.max(baseThicknessMm - consumedMm, 0);
    const thicknessPct = clamp((remainingMm / baseThicknessMm) * 100, 0, 100);
    return {
      year,
      thickness: Number(thicknessPct.toFixed(2))
    };
  });
}

function mapConfidenceInterval(
  interval?: MetricConfidenceIntervalRecord
): MetricConfidenceIntervalPayload | undefined {
  if (!interval) {
    return undefined;
  }

  const lower = Number(interval.lower);
  const upper = Number(interval.upper);
  const confidenceLevel = Number(interval.confidence_level);

  if (!Number.isFinite(lower) || !Number.isFinite(upper) || !Number.isFinite(confidenceLevel)) {
    return undefined;
  }

  return {
    lower: Number(lower.toFixed(4)),
    upper: Number(upper.toFixed(4)),
    confidenceLevel: Number(confidenceLevel.toFixed(3)),
  };
}

function mapUncertaintyBands(
  uncertainty?: SimulationUncertaintyBandsRecord
): SimulationUncertaintyPayload | undefined {
  if (!uncertainty) {
    return undefined;
  }

  const mapped = {
    corrosionRate: mapConfidenceInterval(uncertainty.corrosion_rate_mm_per_year),
    designCorrosionRate: mapConfidenceInterval(uncertainty.design_corrosion_rate_mm_per_year),
    predictedLifespan: mapConfidenceInterval(uncertainty.estimated_lifespan_years),
    riskScore: mapConfidenceInterval(uncertainty.composite_risk_score),
  };

  if (!mapped.corrosionRate && !mapped.designCorrosionRate && !mapped.predictedLifespan && !mapped.riskScore) {
    return undefined;
  }

  return mapped;
}

function buildInterventions(riskBand: string): Array<{ title: string; description: string; status: string }> {
  const highRisk = /high|critical/i.test(riskBand);
  if (highRisk) {
    return [
      { title: "Immediate Coating Retrofit", description: "Deploy a high-build epoxy system across critical zones within the next outage window.", status: "Critical" },
      { title: "Cathodic Protection Upgrade", description: "Increase CP coverage density and verify potential windows across all measured segments.", status: "Critical" },
      { title: "Ultrasonic Inspection Sprint", description: "Run a 90-day intensive UT campaign to validate thinning rates against prediction model output.", status: "High" },
      { title: "Corrosion Inhibitor Program", description: "Introduce targeted inhibitor dosing and monitor treatment efficacy by environment cluster.", status: "Recommended" }
    ];
  }

  return [
    { title: "Condition-Based Monitoring", description: "Shift to sensor-driven interval planning with risk-threshold alerting for key hotspots.", status: "Recommended" },
    { title: "Targeted Coating Maintenance", description: "Apply preventive touch-up at vulnerable joints and atmospheric transition zones.", status: "Recommended" },
    { title: "Annual NDT Validation", description: "Verify degradation model assumptions yearly through sampling and thickness measurements.", status: "Planned" },
    { title: "Material Performance Review", description: "Assess alloy substitution options for next lifecycle phase and CAPEX planning.", status: "Planned" }
  ];
}

function deriveFinancials(input: SimulationInputPayload, riskScore: number, lifespanYears: number): {
  capexRequirement: number;
  projectedROI: number;
  lifecycleExtension: number;
  esgCompliance: number;
} {
  const assetValue = Math.max(1, Number(input.assetValue ?? 50_000_000));
  const normalizedRisk = clamp(riskScore / 100, 0, 1);

  const capexRequirement = Math.round(assetValue * (0.018 + normalizedRisk * 0.085));
  const projectedROI = Number((1.35 + (1 - normalizedRisk) * 1.65).toFixed(2));
  const lifecycleExtension = Number((Math.max(2, lifespanYears * (0.22 + (1 - normalizedRisk) * 0.33))).toFixed(1));
  const esgCompliance = Math.round(clamp(60 + (1 - normalizedRisk) * 35, 0, 100));

  return {
    capexRequirement,
    projectedROI,
    lifecycleExtension,
    esgCompliance
  };
}

export async function runSimulationWithPersistence(
  input: SimulationInputPayload,
  options?: CriticalRequestOptions
): Promise<SimulationResultPayload> {
  const traceContext = buildTraceContext(options);
  const materialLabel = input.material === "Custom" ? input.customMaterial || "Custom Alloy" : input.material || "Carbon Steel";
  const structureLabel = input.structure === "Custom" ? input.customStructure || "Custom Structure" : input.structure || "Infrastructure Asset";
  const normalizedRegion = (input.region ?? "").trim();
  const regionHint = normalizedRegion && !/^auto/i.test(normalizedRegion) ? normalizedRegion : null;

  emitDomainEvent(
    "simulation.pipeline.started",
    {
      materialLabel,
      structureLabel,
    },
    traceContext
  );

  try {
    const material = await ensureMaterial(materialLabel, traceContext);
    emitDomainEvent(
      "simulation.material.resolved",
      {
        materialId: material.id,
        alloyGroup: material.alloy_group,
      },
      traceContext
    );

    const environment = await createEnvironmentRecord(input, structureLabel, traceContext);
    emitDomainEvent(
      "simulation.environment.created",
      {
        environmentId: environment.id,
      },
      traceContext
    );

    const exposedAreaM2 = estimateExposedAreaM2(structureLabel);

    const simulated = await executeCriticalApiRequest(
      () =>
        apiFetch<SimulationAlgorithmResult>("/simulation/simulate", {
          method: "POST",
          body: JSON.stringify({
            material,
            environment: buildEnvironmentInput(input),
            exposed_area_m2: exposedAreaM2,
            exposure_time_hours: DEFAULT_EXPOSURE_HOURS,
            asset_type: structureLabel,
            compliance_standard: input.compliance ?? null,
            criticality: input.criticality ?? null,
            region: regionHint,
            uv_index: Number(input.uvIndex ?? 5),
            mic_activity: input.micActivity ?? "Low",
            soil_resistivity_ohm_cm: Number(input.soilResistivity ?? 5000),
          })
        }),
      {
        operation: "simulation.algorithm.compute",
        path: "/simulation/simulate",
        method: "POST",
        traceContext,
        maxAttempts: 3,
      }
    );

    emitDomainEvent(
      "simulation.algorithm.completed",
      {
        algorithmSimulationId: simulated.simulation_id,
        riskBand: simulated.environment_risk.risk_band,
      },
      traceContext
    );

    const persisted = await executeCriticalApiRequest(
      () =>
        apiFetch<SimulationRecord>("/simulation", {
          method: "POST",
          body: JSON.stringify({
            material_id: material.id,
            environment_id: environment.id,
            exposed_area_m2: exposedAreaM2,
            exposure_time_hours: DEFAULT_EXPOSURE_HOURS,
            corrosion_rate_mm_per_year: simulated.corrosion_rate_mm_per_year,
            estimated_lifespan_years: simulated.estimated_lifespan_years,
            risk_classification: simulated.risk_classification
          })
        }),
      {
        operation: "simulation.record.persist",
        path: "/simulation",
        method: "POST",
        traceContext,
        maxAttempts: 3,
      }
    );

    emitDomainEvent(
      "simulation.record.persisted",
      {
        simulationRecordId: persisted.id,
      },
      traceContext
    );

    const riskScore = Number((simulated.composite_risk_score ?? simulated.environment_risk.risk_score).toFixed(2));
    const predictedLifespan = Number(clamp(simulated.estimated_lifespan_years, 0.5, 200).toFixed(2));
    const corrosionRate = Number(simulated.corrosion_rate_mm_per_year.toFixed(4));
    const designCorrosionRate =
      typeof simulated.design_corrosion_rate_mm_per_year === "number"
        ? Number(simulated.design_corrosion_rate_mm_per_year.toFixed(4))
        : undefined;
    const initialThicknessMm =
      typeof simulated.initial_thickness_mm === "number"
        ? Number(simulated.initial_thickness_mm.toFixed(2))
        : 12;
    const uncertaintyBands = mapUncertaintyBands(simulated.uncertainty_bands);
    const degradationTimeline = buildTimeline(designCorrosionRate ?? corrosionRate, initialThicknessMm);
    const financials = deriveFinancials(input, riskScore, predictedLifespan);

    emitDomainEvent(
      "simulation.pipeline.completed",
      {
        backendSimulationId: persisted.id,
        riskScore,
        predictedLifespan,
      },
      traceContext
    );

    return {
      riskScore,
      corrosionRate,
      designCorrosionRate,
      predictedLifespan,
      degradationTimeline,
      capexRequirement: financials.capexRequirement,
      projectedROI: financials.projectedROI,
      lifecycleExtension: financials.lifecycleExtension,
      esgCompliance: financials.esgCompliance,
      interventions: buildInterventions(simulated.risk_classification),
      recommendationSummary: simulated.recommendation_summary,
      riskBand: simulated.risk_classification,
      backendSimulationId: persisted.id,
      modelVersion: simulated.model_version,
      assetProfile: simulated.asset_profile,
      regionKey: simulated.region_key,
      regionName: simulated.region_name,
      initialThicknessMm,
      minimumSafeThicknessMm:
        typeof simulated.minimum_safe_thickness_mm === "number"
          ? Number(simulated.minimum_safe_thickness_mm.toFixed(2))
          : undefined,
      calibrationConfidence:
        typeof simulated.calibration_confidence === "number"
          ? Number(simulated.calibration_confidence.toFixed(2))
          : undefined,
      uncertaintyBands,
    };
  } catch (error) {
    emitDomainEvent(
      "simulation.pipeline.failed",
      {
        materialLabel,
        structureLabel,
        ...toErrorSummary(error),
      },
      traceContext,
      "error"
    );
    throw error;
  }
}

export async function attachSimulationToProject(
  projectId: string,
  simulationId: string,
  options?: CriticalRequestOptions
): Promise<void> {
  const traceContext = buildTraceContext({
    ...options,
    projectId,
  });

  emitDomainEvent(
    "project.simulation.attach.started",
    {
      projectId,
      simulationId,
    },
    traceContext
  );

  try {
    await executeCriticalApiRequest(
      () =>
        apiFetch<{ status: string }>(`/projects/${projectId}/simulations`, {
          method: "POST",
          body: JSON.stringify({ simulation_id: simulationId })
        }),
      {
        operation: "project.simulation.attach",
        path: `/projects/${projectId}/simulations`,
        method: "POST",
        traceContext,
        maxAttempts: 3,
      }
    );

    emitDomainEvent(
      "project.simulation.attach.succeeded",
      {
        projectId,
        simulationId,
      },
      traceContext
    );
  } catch (error) {
    emitDomainEvent(
      "project.simulation.attach.failed",
      {
        projectId,
        simulationId,
        ...toErrorSummary(error),
      },
      traceContext,
      "error"
    );
    throw error;
  }
}

export async function askCopilot(
  prompt: string,
  tenantId?: string,
  options?: CriticalRequestOptions
): Promise<string> {
  const traceContext = buildTraceContext(options);
  const payload = {
    user_input: prompt,
    ...(tenantId ? { tenant_id: tenantId } : {})
  };

  emitDomainEvent(
    "copilot.query.started",
    {
      promptLength: prompt.length,
      tenantId: tenantId ?? null,
    },
    traceContext
  );

  try {
    const response = await executeCriticalApiRequest(
      () =>
        apiFetch<CopilotResponse>("/copilot/query", {
          method: "POST",
          body: JSON.stringify(payload)
        }),
      {
        operation: "copilot.query",
        path: "/copilot/query",
        method: "POST",
        traceContext,
        maxAttempts: 3,
      }
    );

    emitDomainEvent(
      "copilot.query.succeeded",
      {
        model: response.model,
      },
      traceContext
    );

    return response.response;
  } catch (error) {
    emitDomainEvent(
      "copilot.query.failed",
      {
        promptLength: prompt.length,
        ...toErrorSummary(error),
      },
      traceContext,
      "error"
    );
    throw error;
  }
}
