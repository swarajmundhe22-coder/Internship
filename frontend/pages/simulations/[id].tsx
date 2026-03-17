import { FormEvent } from "react";
import { useRouter } from "next/router";
import { useEffect, useState } from "react";

import { ChapterHeader, HudBadge, TacticalButton, TelemetryCard } from "../../components/CinematicHud";
import { LayoutShell } from "../../components/LayoutShell";
import { ReportViewer } from "../../components/ReportViewer";
import { SimulationPlaybackPanel } from "../../components/SimulationPlaybackPanel";
import { VisualizationPanel } from "../../components/VisualizationPanel";
import { useApi } from "../../hooks/useApi";
import { ApiError, GeneratedReport, PaginatedResponse, Project, ProjectPredictionRecord, SimulationRecord } from "../../types/domain";
import { buildQueryString } from "../../utils/query";

type SimulationFormState = {
  exposed_area_m2: number;
  exposure_time_hours: number;
  corrosion_rate_mm_per_year: number;
  estimated_lifespan_years: number;
  risk_classification: string;
};

export default function SimulationDetailPage() {
  const router = useRouter();
  const { id } = router.query;
  const { run } = useApi();

  const [simulation, setSimulation] = useState<SimulationRecord | null>(null);
  const [form, setForm] = useState<SimulationFormState | null>(null);
  const [latest, setLatest] = useState<SimulationRecord | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");
  const [generatedReport, setGeneratedReport] = useState<GeneratedReport | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [conflict, setConflict] = useState<string | null>(null);
  const [showDiff, setShowDiff] = useState(false);
  const [predictions, setPredictions] = useState<ProjectPredictionRecord[]>([]);
  const [activePredictionId, setActivePredictionId] = useState<string>("");
  const [predictionLoading, setPredictionLoading] = useState(false);

  async function fetchSimulation() {
    if (!id || typeof id !== "string") {
      return;
    }

    const data = await run<SimulationRecord>(`/simulation/${id}`);
    setSimulation(data);
    setForm({
      exposed_area_m2: data.exposed_area_m2,
      exposure_time_hours: data.exposure_time_hours,
      corrosion_rate_mm_per_year: data.corrosion_rate_mm_per_year,
      estimated_lifespan_years: data.estimated_lifespan_years,
      risk_classification: data.risk_classification
    });

    const token = typeof window !== "undefined" ? window.localStorage.getItem("onlooker_token") : null;
    if (token) {
      try {
        const projectList = await run<Project[]>("/projects");
        setProjects(projectList);
        if (projectList.length > 0 && !selectedProjectId) {
          setSelectedProjectId(projectList[0].id);
        }
      } catch {
        setProjects([]);
      }
    }
  }

  async function fetchPredictions(projectId: string, simulationId?: string) {
    if (!projectId) {
      setPredictions([]);
      setActivePredictionId("");
      return;
    }

    const query = buildQueryString({
      page: 1,
      page_size: 10,
      simulation_id: simulationId
    });

    const payload = await run<PaginatedResponse<ProjectPredictionRecord>>(
      `/projects/${projectId}/predictions${query}`
    );

    setPredictions(payload.items);
    setActivePredictionId((current) => {
      if (current && payload.items.some((item) => item.id === current)) {
        return current;
      }
      return payload.items[0]?.id ?? "";
    });
  }

  useEffect(() => {
    void fetchSimulation();
  }, [id]);

  useEffect(() => {
    if (!selectedProjectId || !id || typeof id !== "string") {
      setPredictions([]);
      setActivePredictionId("");
      return;
    }

    void fetchPredictions(selectedProjectId, id);
  }, [selectedProjectId, id]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!id || typeof id !== "string" || !simulation || !form) {
      return;
    }

    setMessage(null);
    setConflict(null);
    setShowDiff(false);

    try {
      const updated = await run<SimulationRecord>(`/simulation/${id}`, {
        method: "PUT",
        body: JSON.stringify({
          expected_version: simulation.version,
          exposed_area_m2: form.exposed_area_m2,
          exposure_time_hours: form.exposure_time_hours,
          corrosion_rate_mm_per_year: form.corrosion_rate_mm_per_year,
          estimated_lifespan_years: form.estimated_lifespan_years,
          risk_classification: form.risk_classification
        })
      });

      setSimulation(updated);
      setForm({
        exposed_area_m2: updated.exposed_area_m2,
        exposure_time_hours: updated.exposure_time_hours,
        corrosion_rate_mm_per_year: updated.corrosion_rate_mm_per_year,
        estimated_lifespan_years: updated.estimated_lifespan_years,
        risk_classification: updated.risk_classification
      });
      setLatest(null);
      setMessage("Simulation updated successfully.");
    } catch (err) {
      const apiError = err as ApiError;
      if (apiError.kind === "concurrency") {
        const fresh = await run<SimulationRecord>(`/simulation/${id}`);
        setLatest(fresh);
        setConflict(
          "This simulation was modified by another process. Reload latest data or compare your edits."
        );
      }
    }
  }

  async function generateReport() {
    if (!id || typeof id !== "string") {
      return;
    }
    const report = await run<GeneratedReport>("/reports/generate", {
      method: "POST",
      body: JSON.stringify({ simulation_id: id })
    });
    setGeneratedReport(report);
    setMessage("Report generated successfully.");
  }

  function downloadReportHtml() {
    if (!generatedReport) {
      return;
    }
    const html = `
      <html>
      <head><title>The On Looker Report</title></head>
      <body>
        <h1>Simulation Report</h1>
        <p>Simulation ID: ${generatedReport.simulation_id}</p>
        <p>Corrosion Rate: ${generatedReport.metrics.corrosion_rate_mm_per_year}</p>
        <p>Risk: ${generatedReport.metrics.risk_classification}</p>
        <p>Lifespan: ${generatedReport.metrics.estimated_lifespan_years}</p>
        <h2>Recommendation</h2>
        <p>${generatedReport.recommendation_summary}</p>
      </body>
      </html>
    `;

    const blob = new Blob([html], { type: "text/html" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = `simulation-report-${generatedReport.simulation_id}.html`;
    anchor.click();
    URL.revokeObjectURL(url);
  }

  async function saveToProject() {
    if (!selectedProjectId || !id || typeof id !== "string") {
      return;
    }
    await run(`/projects/${selectedProjectId}/simulations`, {
      method: "POST",
      body: JSON.stringify({ simulation_id: id })
    });
    setMessage("Simulation saved to project.");
  }

  async function generatePrediction() {
    if (!selectedProjectId || !id || typeof id !== "string") {
      return;
    }

    setPredictionLoading(true);
    try {
      const created = await run<ProjectPredictionRecord>(`/projects/${selectedProjectId}/predict`, {
        method: "POST",
        body: JSON.stringify({
          simulation_id: id,
          horizon_hours: 24 * 30,
          step_hours: 24
        })
      });

      setPredictions((current) => [created, ...current]);
      setActivePredictionId(created.id);
      setMessage("Predictive playback generated.");
    } finally {
      setPredictionLoading(false);
    }
  }

  const activePrediction = predictions.find((item) => item.id === activePredictionId) ?? predictions[0] ?? null;

  return (
    <LayoutShell title="Simulation Detail" subtitle="Inspect one simulation snapshot and visual corrosion intensity.">
      {!simulation || !form ? (
        <section className="panel p-6 type-body text-softwhite/70">Loading simulation...</section>
      ) : (
        <div className="grid gap-4 lg:grid-cols-2">
          <form className="panel grid gap-3 p-6" onSubmit={submit}>
            <ChapterHeader eyebrow="Simulation Editor" title="Edit Simulation" />
            <div><HudBadge label={`Version: ${simulation.version}`} tone="primary" /></div>

            <label className="grid gap-1 text-sm text-softwhite/85">
              Risk Classification
              <input
                className="glass-input rounded-md p-2"
                value={form.risk_classification}
                onChange={(event) =>
                  setForm((prev) =>
                    prev ? { ...prev, risk_classification: event.target.value } : prev
                  )
                }
              />
            </label>

            <label className="grid gap-1 text-sm text-softwhite/85">
              Corrosion Rate (mm/year)
              <input
                className="glass-input rounded-md p-2"
                type="number"
                step="0.0001"
                value={form.corrosion_rate_mm_per_year}
                onChange={(event) =>
                  setForm((prev) =>
                    prev
                      ? { ...prev, corrosion_rate_mm_per_year: Number(event.target.value) }
                      : prev
                  )
                }
              />
            </label>

            <label className="grid gap-1 text-sm text-softwhite/85">
              Estimated Lifespan (years)
              <input
                className="glass-input rounded-md p-2"
                type="number"
                step="0.01"
                value={form.estimated_lifespan_years}
                onChange={(event) =>
                  setForm((prev) =>
                    prev
                      ? { ...prev, estimated_lifespan_years: Number(event.target.value) }
                      : prev
                  )
                }
              />
            </label>

            <label className="grid gap-1 text-sm text-softwhite/85">
              Exposed Area (m2)
              <input
                className="glass-input rounded-md p-2"
                type="number"
                step="0.1"
                value={form.exposed_area_m2}
                onChange={(event) =>
                  setForm((prev) =>
                    prev ? { ...prev, exposed_area_m2: Number(event.target.value) } : prev
                  )
                }
              />
            </label>

            <label className="grid gap-1 text-sm text-softwhite/85">
              Exposure Time (hours)
              <input
                className="glass-input rounded-md p-2"
                type="number"
                step="1"
                value={form.exposure_time_hours}
                onChange={(event) =>
                  setForm((prev) =>
                    prev ? { ...prev, exposure_time_hours: Number(event.target.value) } : prev
                  )
                }
              />
            </label>

            <TacticalButton type="submit">Save Changes</TacticalButton>
            {message && <p className="text-sm text-lagoon">{message}</p>}
          </form>

          <div className="grid gap-4">
            <VisualizationPanel intensity={Math.min(simulation.corrosion_rate_mm_per_year * 220, 100)} />

            <section className="panel grid gap-3 p-6">
              <ChapterHeader eyebrow="Operations" title="Reports And Projects" />
              <div className="flex flex-wrap gap-2">
                <TacticalButton type="button" onClick={() => void generateReport()}>
                  Generate Report
                </TacticalButton>
                <TacticalButton type="button" tone="support" onClick={downloadReportHtml} disabled={!generatedReport}>
                  Download HTML
                </TacticalButton>
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <select
                  className="glass-input rounded-md p-2 text-sm"
                  value={selectedProjectId}
                  onChange={(event) => setSelectedProjectId(event.target.value)}
                >
                  <option value="">Select project</option>
                  {projects.map((project) => (
                    <option key={project.id} value={project.id}>
                      {project.name}
                    </option>
                  ))}
                </select>
                <TacticalButton type="button" tone="support" onClick={() => void saveToProject()} disabled={!selectedProjectId}>
                  Save Simulation To Project
                </TacticalButton>
                <TacticalButton type="button" tone="alert" onClick={() => void generatePrediction()} disabled={!selectedProjectId || predictionLoading}>
                  {predictionLoading ? "Generating Playback..." : "Generate Predictive Playback"}
                </TacticalButton>
              </div>

              {predictions.length > 0 && (
                <label className="grid gap-1 text-sm">
                  Playback Sequence
                  <select
                    className="glass-input rounded-md p-2 text-sm"
                    value={activePrediction?.id ?? ""}
                    onChange={(event) => setActivePredictionId(event.target.value)}
                  >
                    {predictions.map((prediction) => (
                      <option key={prediction.id} value={prediction.id}>
                        {new Date(prediction.created_at).toLocaleString()} | {prediction.model_name}
                      </option>
                    ))}
                  </select>
                </label>
              )}

              <TacticalButton type="button" tone="support" onClick={() => void router.push("/simulations/compare")}>
                Open Scenario Comparison
              </TacticalButton>
            </section>

            <section className="panel p-6">
              <ChapterHeader eyebrow="Consistency" title="Concurrency Status" />
              {!conflict && <p className="mt-2 type-body text-softwhite/70">No conflict detected for this record.</p>}
              {conflict && (
                <div className="mt-2 grid gap-3">
                  <p className="text-sm text-red-600">{conflict}</p>
                  <div className="flex gap-2">
                    <TacticalButton type="button" tone="support" onClick={() => void fetchSimulation()}>
                      Reload Latest Data
                    </TacticalButton>
                    <TacticalButton type="button" tone="alert" onClick={() => setShowDiff((prev) => !prev)}>
                      View Diff
                    </TacticalButton>
                  </div>

                  {showDiff && latest && (
                    <div className="hud-grid md:grid-cols-3">
                      <TelemetryCard label="Risk" value={`you: ${form.risk_classification} | latest: ${latest.risk_classification}`} tone="alert" />
                      <TelemetryCard label="Corrosion" value={`you: ${form.corrosion_rate_mm_per_year} | latest: ${latest.corrosion_rate_mm_per_year}`} tone="support" />
                      <TelemetryCard label="Lifespan" value={`you: ${form.estimated_lifespan_years} | latest: ${latest.estimated_lifespan_years}`} tone="primary" />
                    </div>
                  )}
                </div>
              )}
            </section>

            <SimulationPlaybackPanel timeline={activePrediction?.timeline ?? []} loading={predictionLoading} />
          </div>
        </div>
      )}

      {generatedReport && <ReportViewer report={generatedReport} />}
    </LayoutShell>
  );
}
