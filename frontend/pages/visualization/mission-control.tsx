import { FormEvent, useEffect, useMemo, useState } from "react";

import { BabylonTwinStage } from "../../components/BabylonTwinStage";
import { ChapterHeader, TacticalButton, TelemetryCard } from "../../components/CinematicHud";
import { CinematicScene } from "../../components/CinematicScene";
import { LayoutShell } from "../../components/LayoutShell";
import { useApi } from "../../hooks/useApi";
import { useWebXRSession } from "../../hooks/useWebXRSession";
import { PaginatedResponse, SimulationRecord, VisualizationExportResponse, VisualizationMode, VisualizationPlaybackResponse, VisualizationRecord } from "../../types/domain";

type MissionForm = {
  simulation_id: string;
  tenant_id: string;
  mode: VisualizationMode;
  file_type: "pdf" | "mp4";
};

export default function MissionControlPage() {
  const { run, loading, error } = useApi();
  const xr = useWebXRSession();
  const [simulations, setSimulations] = useState<SimulationRecord[]>([]);
  const [twin, setTwin] = useState<VisualizationRecord | null>(null);
  const [playback, setPlayback] = useState<VisualizationPlaybackResponse | null>(null);
  const [exportResult, setExportResult] = useState<VisualizationExportResponse | null>(null);
  const [currentFrame, setCurrentFrame] = useState(0);

  const [form, setForm] = useState<MissionForm>({
    simulation_id: "",
    tenant_id: "",
    mode: "twin",
    file_type: "mp4"
  });

  useEffect(() => {
    void loadSimulations();
  }, []);

  const frames = useMemo(() => playback?.timeline_frames ?? [], [playback]);
  const frame = frames[currentFrame] ?? null;

  async function loadSimulations() {
    const response = await run<PaginatedResponse<SimulationRecord>>("/simulation?page=1&page_size=100");
    setSimulations(response.items);
    if (response.items.length > 0) {
      setForm((prev) => ({ ...prev, simulation_id: prev.simulation_id || response.items[0].id }));
    }
  }

  async function generateTwin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const response = await run<VisualizationRecord>("/visualization/twin", {
      method: "POST",
      body: JSON.stringify({ simulation_id: form.simulation_id, tenant_id: form.tenant_id, mode: form.mode })
    });
    setTwin(response);
    setPlayback(null);
    setExportResult(null);
  }

  async function generatePlayback() {
    const response = await run<VisualizationPlaybackResponse>("/visualization/playback", {
      method: "POST",
      body: JSON.stringify({ simulation_id: form.simulation_id, tenant_id: form.tenant_id, mode: form.mode })
    });
    setPlayback(response);
    setCurrentFrame(0);
  }

  async function exportShowcase() {
    const response = await run<VisualizationExportResponse>("/visualization/export", {
      method: "POST",
      body: JSON.stringify({
        simulation_id: form.simulation_id,
        tenant_id: form.tenant_id,
        mode: form.mode,
        file_type: form.file_type
      })
    });
    setExportResult(response);
  }

  return (
    <LayoutShell
      title="Mission Control"
      subtitle="Immersive digital twin operations with cinematic playback, AR/VR readiness, and investor showcase export."
    >
      <CinematicScene
        tone="battle"
        sceneLabel="Scene 3 / Playback Battle"
        narrative="Cinematic twin playback engaged. Risk zones pulse as mission timeline scrubs from baseline green into critical red."
      />

      <section className="panel mb-6 p-6">
        <form className="grid gap-4 md:grid-cols-4" onSubmit={(event) => void generateTwin(event)}>
          <label className="grid gap-1 text-sm">
            <span className="hud-label text-[10px]">Simulation</span>
            <select
              className="glass-input rounded-md p-2"
              value={form.simulation_id}
              onChange={(event) => setForm((prev) => ({ ...prev, simulation_id: event.target.value }))}
              required
            >
              <option value="">Select simulation</option>
              {simulations.map((sim) => (
                <option key={sim.id} value={sim.id}>
                  {sim.id.slice(0, 8)} | {sim.risk_classification.toUpperCase()}
                </option>
              ))}
            </select>
          </label>

          <label className="grid gap-1 text-sm">
            <span className="hud-label text-[10px]">Tenant ID</span>
            <input
              className="glass-input rounded-md p-2"
              placeholder="Tenant UUID"
              value={form.tenant_id}
              onChange={(event) => setForm((prev) => ({ ...prev, tenant_id: event.target.value }))}
              required
            />
          </label>

          <label className="grid gap-1 text-sm">
            <span className="hud-label text-[10px]">Mode</span>
            <select
              className="glass-input rounded-md p-2"
              value={form.mode}
              onChange={(event) => setForm((prev) => ({ ...prev, mode: event.target.value as VisualizationMode }))}
            >
              <option value="twin">Twin</option>
              <option value="ar">AR</option>
              <option value="vr">VR</option>
            </select>
          </label>

          <div className="grid gap-2 md:content-end">
            <TacticalButton type="submit" tone="primary" disabled={loading}>
              {loading ? "Generating..." : "Generate Twin"}
            </TacticalButton>
          </div>
        </form>
        {error && <p className="mt-3 text-sm text-red-300">{error}</p>}
      </section>

      <section className="mb-6 grid gap-6 lg:grid-cols-[1.4fr,1fr]">
        <article className="panel p-4">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="type-title text-softwhite">Digital Twin Stage</h2>
            <span className="type-caption text-softwhite/70">WebXR: {xr.label}</span>
          </div>
          <BabylonTwinStage hotspots={twin?.metadata?.hotspots ?? []} />
          <p className="mt-3 type-caption text-softwhite/70">
            Holographic stage uses glow-coded hotspots and timeline overlays for mission playback.
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            <TacticalButton
              type="button"
              onClick={() => void xr.startSession("immersive-vr")}
              disabled={xr.state === "active" || !xr.supportedModes.includes("immersive-vr")}
            >
              Enter VR Session
            </TacticalButton>
            <TacticalButton
              type="button"
              tone="support"
              onClick={() => void xr.startSession("immersive-ar")}
              disabled={xr.state === "active" || !xr.supportedModes.includes("immersive-ar")}
            >
              Enter AR Session
            </TacticalButton>
            <TacticalButton
              type="button"
              tone="alert"
              onClick={() => void xr.endSession()}
              disabled={xr.state !== "active"}
            >
              Exit XR Session
            </TacticalButton>
          </div>
          {xr.error && <p className="mt-2 text-xs text-red-300">XR error: {xr.error}</p>}
        </article>

        <article className="panel p-4">
          <ChapterHeader eyebrow="Twin Module" title="Twin Diagnostics" />
          <div className="hud-grid md:grid-cols-2">
            <TelemetryCard label="Status" value={twin?.status ?? "not generated"} tone="primary" />
            <TelemetryCard label="Overlay Accuracy" value={twin ? `${(twin.overlay_accuracy * 100).toFixed(1)}%` : "-"} tone="support" />
            <TelemetryCard label="Asset Type" value={twin?.metadata?.asset_type ?? "-"} tone="support" />
            <TelemetryCard label="Scene Profile" value={twin?.metadata?.scene_profile ?? "-"} tone="primary" />
          </div>
          <div className="mt-4 grid gap-2">
            <TacticalButton type="button" onClick={() => void generatePlayback()}>
              Prepare Playback
            </TacticalButton>
            <div className="grid grid-cols-2 gap-2">
              <select
                className="glass-input rounded-md p-2 text-sm"
                value={form.file_type}
                onChange={(event) =>
                  setForm((prev) => ({ ...prev, file_type: event.target.value as "pdf" | "mp4" }))
                }
              >
                <option value="mp4">MP4</option>
                <option value="pdf">PDF</option>
              </select>
              <TacticalButton type="button" tone="support" onClick={() => void exportShowcase()}>
                Export Showcase
              </TacticalButton>
            </div>
          </div>
        </article>
      </section>

      <section className="panel p-6">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <h2 className="type-title text-softwhite">Cinematic Playback Timeline</h2>
          <p className="type-caption text-softwhite/70">Investor narrative mode with mission control time travel slider.</p>
        </div>

        <div className="rounded-md border border-softwhite/20 bg-black/30 p-3">
          <div className="severity-track mb-2 h-1 rounded-full" />
          <input
            type="range"
            min={0}
            max={Math.max(frames.length - 1, 0)}
            value={currentFrame}
            onChange={(event) => setCurrentFrame(Number(event.target.value))}
            className="w-full accent-lagoon"
            disabled={frames.length === 0}
          />
        </div>

        <div className="mt-4 hud-grid md:grid-cols-3">
          <TelemetryCard label="Frame" value={frame ? `${currentFrame + 1} / ${frames.length}` : "-"} tone="primary" />
          <TelemetryCard label="Minute" value={frame && typeof frame.minute === "number" ? frame.minute : "-"} tone="support" />
          <TelemetryCard label="Severity" value={frame && typeof frame.severity === "string" ? frame.severity : "-"} tone="alert" />
          <TelemetryCard label="Risk Score" value={frame && typeof frame.risk_score === "number" ? frame.risk_score : "-"} tone="alert" />
          <TelemetryCard label="Degradation" value={frame && typeof frame.degradation_pct === "number" ? `${frame.degradation_pct}%` : "-"} tone="alert" />
          <TelemetryCard label="Playback Mode" value={playback?.mode ?? form.mode} tone="support" />
        </div>

        <div className="mt-4 rounded-lg border border-neoviolet/30 bg-slatewash/35 p-4 text-sm text-softwhite/85">
          Narrative: {twin?.metadata?.investor_narrative ?? "Generate twin to unlock investor showcase narrative."}
        </div>

        {exportResult && (
          <div className="mt-4 rounded-lg border border-lagoon/40 bg-lagoon/10 p-3 text-sm text-softwhite">
            Export ready: {exportResult.export.file_uri}
          </div>
        )}
      </section>
    </LayoutShell>
  );
}
