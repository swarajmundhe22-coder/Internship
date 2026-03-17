import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { ChapterHeader, HudBadge, TacticalButton } from "../../components/CinematicHud";
import { CinematicScene } from "../../components/CinematicScene";
import { FilterBar } from "../../components/FilterBar";
import { LayoutShell } from "../../components/LayoutShell";
import { ResultsPanel } from "../../components/ResultsPanel";
import { SimulationControlPanel } from "../../components/SimulationControlPanel";
import { TableShell } from "../../components/TableShell";
import { VisualizationPanel } from "../../components/VisualizationPanel";
import { useApi } from "../../hooks/useApi";
import { useUrlQueryState } from "../../hooks/useUrlQueryState";
import {
  EnvironmentProfile,
  Material,
  PaginatedResponse,
  SimulationListQueryParams,
  SimulationPrediction,
  SimulationRecord
} from "../../types/domain";
import { buildQueryString, toDateTimeEnd, toDateTimeStart } from "../../utils/query";

export default function SimulationsPage() {
  const { run, error, loading } = useApi();
  const { state, setQuery, isReady } = useUrlQueryState({
    page: "1",
    page_size: "10",
    material_id: "",
    environment_id: "",
    risk_level: "",
    created_from: "",
    created_to: ""
  });

  const [materials, setMaterials] = useState<Material[]>([]);
  const [environments, setEnvironments] = useState<EnvironmentProfile[]>([]);
  const [simulationPage, setSimulationPage] = useState<PaginatedResponse<SimulationRecord>>({
    items: [],
    total: 0,
    page: 1,
    page_size: 10
  });
  const [selectedMaterialId, setSelectedMaterialId] = useState<string>("");
  const [selectedEnvironmentId, setSelectedEnvironmentId] = useState<string>("");
  const [result, setResult] = useState<SimulationPrediction | null>(null);

  const page = Number(state.page) || 1;
  const pageSize = Number(state.page_size) || 10;

  const selectedMaterial = useMemo(
    () => materials.find((item) => item.id === selectedMaterialId) ?? null,
    [materials, selectedMaterialId]
  );
  const selectedEnvironment = useMemo(
    () => environments.find((item) => item.id === selectedEnvironmentId) ?? null,
    [environments, selectedEnvironmentId]
  );

  const filterFields = useMemo(
    () => [
      {
        key: "material_id",
        label: "Material Filter",
        type: "select" as const,
        options: materials.map((item) => ({ label: item.name, value: item.id }))
      },
      {
        key: "environment_id",
        label: "Environment Filter",
        type: "select" as const,
        options: environments.map((item) => ({ label: item.profile_name, value: item.id }))
      },
      {
        key: "risk_level",
        label: "Risk Level",
        type: "select" as const,
        options: [
          { label: "Low", value: "low" },
          { label: "Moderate", value: "moderate" },
          { label: "High", value: "high" },
          { label: "Critical", value: "critical" }
        ]
      },
      {
        key: "created_from",
        label: "Created From",
        type: "date" as const
      },
      {
        key: "created_to",
        label: "Created To",
        type: "date" as const
      }
    ],
    [materials, environments]
  );

  async function loadReferenceData() {
    const [materialPage, environmentPage] = await Promise.all([
      run<PaginatedResponse<Material>>("/materials?page=1&page_size=100"),
      run<PaginatedResponse<EnvironmentProfile>>("/environment?page=1&page_size=100")
    ]);

    setMaterials(materialPage.items);
    setEnvironments(environmentPage.items);

    if (materialPage.items.length > 0 && !selectedMaterialId) {
      setSelectedMaterialId(materialPage.items[0].id);
    }
    if (environmentPage.items.length > 0 && !selectedEnvironmentId) {
      setSelectedEnvironmentId(environmentPage.items[0].id);
    }
  }

  async function loadSimulations() {
    const query: SimulationListQueryParams = {
      page,
      page_size: pageSize,
      material_id: state.material_id || undefined,
      environment_id: state.environment_id || undefined,
      risk_level: state.risk_level || undefined,
      created_from: toDateTimeStart(state.created_from),
      created_to: toDateTimeEnd(state.created_to)
    };

    const list = await run<PaginatedResponse<SimulationRecord>>(
      `/simulation${buildQueryString(query)}`
    );
    setSimulationPage(list);
  }

  useEffect(() => {
    void loadReferenceData();
  }, []);

  useEffect(() => {
    if (!isReady) {
      return;
    }

    void loadSimulations();
  }, [
    isReady,
    state.page,
    state.page_size,
    state.material_id,
    state.environment_id,
    state.risk_level,
    state.created_from,
    state.created_to
  ]);

  async function runSimulation(payload: { exposed_area_m2: number; exposure_time_hours: number }) {
    if (!selectedMaterial || !selectedEnvironment) {
      return;
    }

    const prediction = await run<SimulationPrediction>("/simulation/simulate", {
      method: "POST",
      body: JSON.stringify({
        material: selectedMaterial,
        environment: {
          temperature_c: selectedEnvironment.temperature_c,
          relative_humidity_pct: selectedEnvironment.relative_humidity_pct,
          chloride_ppm: selectedEnvironment.chloride_ppm,
          ph: selectedEnvironment.ph,
          dissolved_oxygen_mg_l: selectedEnvironment.dissolved_oxygen_mg_l
        },
        exposed_area_m2: payload.exposed_area_m2,
        exposure_time_hours: payload.exposure_time_hours
      })
    });
    setResult(prediction);
  }

  return (
    <LayoutShell
      title="Simulation Operations"
      subtitle="Run predictive corrosion models and inspect simulation history."
    >
      <div className="page-polish-simulations">
      <section className="story-track mb-4 grid gap-4 lg:grid-cols-[0.92fr_1.08fr]" data-story-track="true" data-story-curve="snappy" data-story-start="top 92%" data-story-end="top 44%" data-story-scrub="0.43" data-story-progress-start="top 90%" data-story-progress-end="bottom 18%" data-story-compact-start="top 88%" data-story-compact-beat-start="top 78%">
        <article className="story-pin-column panel p-5" data-story-pin="true">
          <ChapterHeader
            eyebrow="Battle Timeline"
            title="Escalation narrative in pinned command view."
            description="As users scroll, tactical context stays locked while simulation controls and outcomes progress in sequenced chapters."
          />
          <div className="grid gap-2">
            <p data-story-step="true"><HudBadge label="Material context locked" tone="primary" /></p>
            <p data-story-step="true"><HudBadge label="Environment vectors armed" tone="support" /></p>
            <p data-story-step="true"><HudBadge label="Risk thresholds monitored" tone="alert" /></p>
          </div>
        </article>

        <div className="story-panel-stack">
          <article className="story-panel" data-story-panel="true" data-story-ease="expo.out" data-story-offset="36" data-story-scrub="0.5">
            <CinematicScene
              tone="battle"
              sceneLabel="Scene 3 / Battle Sequence"
              narrative="Corrosion risk escalating. Predictive foresight engaged with severity progression from green to red."
            >
              <div className="grid gap-3 md:grid-cols-[1fr,auto] md:items-center">
                <div>
                  <p className="type-caption text-softwhite/75">Timeline Severity Gradient</p>
                  <div className="severity-track mt-1 h-2 rounded-full border border-softwhite/20" />
                </div>
                <HudBadge label="Tactical focus: affected zones pulse with escalation glow" tone="alert" />
              </div>
            </CinematicScene>
          </article>

          <section className="story-panel grid gap-4 panel p-4 md:grid-cols-2" data-story-panel="true" data-story-ease="power3.out" data-story-offset="22" data-story-scrub="0.42">
            <label className="grid gap-1 text-sm text-softwhite/85" data-story-step="true">
              Material
              <select
                className="glass-input rounded-md p-2"
                value={selectedMaterialId}
                onChange={(e) => setSelectedMaterialId(e.target.value)}
              >
                {materials.map((material) => (
                  <option key={material.id} value={material.id}>
                    {material.name}
                  </option>
                ))}
              </select>
            </label>
            <label className="grid gap-1 text-sm text-softwhite/85" data-story-step="true">
              Environment
              <select
                className="glass-input rounded-md p-2"
                value={selectedEnvironmentId}
                onChange={(e) => setSelectedEnvironmentId(e.target.value)}
              >
                {environments.map((environment) => (
                  <option key={environment.id} value={environment.id}>
                    {environment.profile_name}
                  </option>
                ))}
              </select>
            </label>
          </section>
        </div>
      </section>

      <div className="grid gap-4 lg:grid-cols-3">
        <SimulationControlPanel onRun={runSimulation} />
        <VisualizationPanel intensity={result?.environment_risk.risk_score ?? 10} />
        <ResultsPanel result={result} />
      </div>

      <TableShell
        title="Simulation Records"
        items={simulationPage.items}
        total={simulationPage.total}
        page={page}
        pageSize={pageSize}
        loading={loading}
        error={error}
        emptyMessage="No simulation records match your current filters."
        filters={
          <FilterBar
            fields={filterFields}
            values={state}
            onChange={(key, value) => setQuery({ [key]: value })}
            onReset={() =>
              setQuery(
                {
                  material_id: undefined,
                  environment_id: undefined,
                  risk_level: undefined,
                  created_from: undefined,
                  created_to: undefined
                },
                { resetPage: true }
              )
            }
          />
        }
        onPageChange={(nextPage) => setQuery({ page: String(nextPage) }, { resetPage: false })}
        onPageSizeChange={(size) =>
          setQuery({ page_size: String(size), page: "1" }, { resetPage: false })
        }
      >
        {(items) => (
          <div className="grid gap-3">
            {items.map((simulation) => (
              <Link
                href={`/simulations/${simulation.id}`}
                key={simulation.id}
                className="rounded-lg border border-signal/30 bg-slatewash/45 p-4 transition hover:border-signal"
              >
                <div className="mb-2">
                  <HudBadge label={simulation.risk_classification.toUpperCase()} tone="alert" />
                </div>
                <p className="type-body text-softwhite/80">
                  Lifespan: {simulation.estimated_lifespan_years.toFixed(1)} years
                </p>
                <p className="type-body text-softwhite/80">
                  Corrosion: {simulation.corrosion_rate_mm_per_year.toFixed(3)} mm/year
                </p>
                <div className="mt-3">
                  <TacticalButton tone="alert">Open Simulation Brief</TacticalButton>
                </div>
              </Link>
            ))}
          </div>
        )}
      </TableShell>
      </div>
    </LayoutShell>
  );
}
