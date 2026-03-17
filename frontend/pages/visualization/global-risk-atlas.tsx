import dynamic from "next/dynamic";
import { FormEvent, useState } from "react";

import { ChapterHeader, HudBadge, TacticalButton, TelemetryCard } from "../../components/CinematicHud";
import { CinematicScene } from "../../components/CinematicScene";
import { LayoutShell } from "../../components/LayoutShell";
import { useIntelligence } from "../../hooks/useIntelligence";
import { AtlasRequest } from "../../types/domain";

const GlobalRiskAtlasMap = dynamic(
  () => import("../../components/GlobalRiskAtlasMap").then((mod) => mod.GlobalRiskAtlasMap),
  { ssr: false }
);

type AtlasFormState = {
  tenant_id: string;
  sensor_id: string;
  region: string;
  imagery_source: string;
  export_type: AtlasRequest["export_type"];
  asset_id: string;
  risk_score: number;
};

export default function GlobalRiskAtlasPage() {
  const {
    loading,
    error,
    history,
    overlayPoints,
    runIoTIngest,
    runSatelliteIngest,
    runAtlasGenerate,
    runAtlasExport,
    loadLatestAtlas,
    runMaintenanceSchedule
  } = useIntelligence();

  const [form, setForm] = useState<AtlasFormState>({
    tenant_id: "",
    sensor_id: "sensor-atlas-01",
    region: "north-sea",
    imagery_source: "sentinel-2",
    export_type: "map_snapshot",
    asset_id: "asset-001",
    risk_score: 0.72
  });

  async function onIoTIngest(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await runIoTIngest({
      tenant_id: form.tenant_id,
      sensor_id: form.sensor_id,
      payload: {
        humidity_pct: 79.4,
        temperature_c: 30.1,
        chloride_ppm: 9700,
        region: form.region
      }
    });
  }

  async function onSatelliteIngest(): Promise<void> {
    await runSatelliteIngest({
      tenant_id: form.tenant_id,
      region: form.region,
      imagery_source: form.imagery_source
    });
  }

  async function onAtlasGenerate(): Promise<void> {
    await runAtlasGenerate({
      tenant_id: form.tenant_id,
      region: form.region,
      export_type: form.export_type
    });
  }

  async function onAtlasExport(): Promise<void> {
    await runAtlasExport({
      tenant_id: form.tenant_id,
      region: form.region,
      export_type: form.export_type
    });
  }

  async function onScheduleMaintenance(): Promise<void> {
    await runMaintenanceSchedule({
      tenant_id: form.tenant_id,
      asset_id: form.asset_id,
      risk_score: form.risk_score
    });
  }

  async function onLoadLatestAtlas(): Promise<void> {
    if (!form.tenant_id || !form.region) {
      return;
    }
    await loadLatestAtlas(form.tenant_id, form.region);
  }

  return (
    <LayoutShell
      title="Global Risk Atlas"
      subtitle="Phase 9 command shell for IoT ingestion, satellite fusion, atlas generation, and predictive maintenance scheduling."
    >
      <CinematicScene
        tone="world"
        sceneLabel="Scene 5 / World Scene"
        narrative="Global foresight atlas activated. Planetary risk intelligence online with aurora overlays and regional zoom focus."
      >
        <div className="grid gap-2 text-xs text-softwhite/75 md:grid-cols-3">
          <HudBadge label="Planet rotates with dynamic severity layers." tone="primary" />
          <HudBadge label="Cinematic zoom into active regions and hotspots." tone="support" />
          <HudBadge label="Holographic pop-ups expose risk telemetry in-flight." tone="alert" />
        </div>
      </CinematicScene>

      <section className="panel mb-6 p-6">
        <form className="grid gap-4 lg:grid-cols-6" onSubmit={(event) => void onIoTIngest(event)}>
          <label className="grid gap-1 text-sm lg:col-span-2">
            <span className="hud-label text-[10px]">Tenant ID</span>
            <input
              className="glass-input rounded-md p-2"
              value={form.tenant_id}
              onChange={(event) => setForm((prev) => ({ ...prev, tenant_id: event.target.value }))}
              placeholder="Tenant UUID"
              required
            />
          </label>

          <label className="grid gap-1 text-sm">
            <span className="hud-label text-[10px]">Sensor ID</span>
            <input
              className="glass-input rounded-md p-2"
              value={form.sensor_id}
              onChange={(event) => setForm((prev) => ({ ...prev, sensor_id: event.target.value }))}
              required
            />
          </label>

          <label className="grid gap-1 text-sm lg:col-span-2">
            <span className="hud-label text-[10px]">Region</span>
            <input
              className="glass-input rounded-md p-2"
              value={form.region}
              onChange={(event) => setForm((prev) => ({ ...prev, region: event.target.value }))}
              required
            />
          </label>

          <div className="grid gap-2 lg:content-end">
            <TacticalButton type="submit" disabled={loading}>
              IoT Ingest
            </TacticalButton>
          </div>

          <label className="grid gap-1 text-sm lg:col-span-2">
            <span className="hud-label text-[10px]">Imagery Source</span>
            <input
              className="glass-input rounded-md p-2"
              value={form.imagery_source}
              onChange={(event) => setForm((prev) => ({ ...prev, imagery_source: event.target.value }))}
              required
            />
          </label>

          <label className="grid gap-1 text-sm lg:col-span-2">
            <span className="hud-label text-[10px]">Export Type</span>
            <select
              className="glass-input rounded-md p-2"
              value={form.export_type}
              onChange={(event) =>
                setForm((prev) => ({ ...prev, export_type: event.target.value as AtlasRequest["export_type"] }))
              }
            >
              <option value="map_snapshot">map_snapshot</option>
              <option value="pdf">pdf</option>
              <option value="mp4">mp4</option>
            </select>
          </label>

          <label className="grid gap-1 text-sm lg:col-span-1">
            <span className="hud-label text-[10px]">Asset ID</span>
            <input
              className="glass-input rounded-md p-2"
              value={form.asset_id}
              onChange={(event) => setForm((prev) => ({ ...prev, asset_id: event.target.value }))}
              required
            />
          </label>

          <label className="grid gap-1 text-sm lg:col-span-1">
            <span className="hud-label text-[10px]">Risk Score</span>
            <input
              className="glass-input rounded-md p-2"
              type="number"
              min={0}
              max={1}
              step={0.01}
              value={form.risk_score}
              onChange={(event) => setForm((prev) => ({ ...prev, risk_score: Number(event.target.value) }))}
            />
          </label>

          <div className="grid gap-2 lg:col-span-6 lg:grid-cols-5">
            <TacticalButton type="button" onClick={() => void onSatelliteIngest()} disabled={loading}>
              Satellite Ingest
            </TacticalButton>
            <TacticalButton type="button" tone="support" onClick={() => void onAtlasGenerate()} disabled={loading}>
              Generate Atlas
            </TacticalButton>
            <TacticalButton type="button" tone="support" onClick={() => void onAtlasExport()} disabled={loading}>
              Export Atlas
            </TacticalButton>
            <TacticalButton type="button" tone="alert" onClick={() => void onScheduleMaintenance()} disabled={loading}>
              Schedule Maintenance
            </TacticalButton>
            <TacticalButton type="button" tone="primary" onClick={() => void onLoadLatestAtlas()} disabled={loading || !form.tenant_id || !form.region}>
              Load Latest Atlas
            </TacticalButton>
          </div>
        </form>

        {error && <p className="mt-3 text-sm text-red-300">{error}</p>}
      </section>

      <section className="mb-6 grid gap-6 xl:grid-cols-[1.35fr,1fr]">
        <article className="panel p-4">
          <div className="mb-3 flex items-center justify-between">
            <h2 className="type-title text-softwhite">Atlas Overlay Stage</h2>
            <p className="type-caption text-softwhite/70">Mapbox + Deck.gl scaffold</p>
          </div>
          <GlobalRiskAtlasMap points={overlayPoints} />
        </article>

        <article className="panel p-4">
          <ChapterHeader eyebrow="Phase 9" title="Event Status" />
          <div className="hud-grid text-sm md:grid-cols-2">
            <TelemetryCard label="IoT Ingest" value={history.iot ? `${history.iot.sensor_id} | ${history.iot.status}` : "pending"} tone="primary" />
            <TelemetryCard label="Satellite Ingest" value={history.satellite ? `${history.satellite.region} | ${history.satellite.status}` : "pending"} tone="support" />
            <TelemetryCard label="Atlas Generation" value={history.atlasGenerated ? history.atlasGenerated.status : "pending"} tone="support" />
            <TelemetryCard label="Atlas Export" value={history.atlasExported ? `${history.atlasExported.export_type} | ${history.atlasExported.status}` : "pending"} tone="support" />
            <TelemetryCard label="Latest Atlas Cache" value={history.atlasLatest ? `${history.atlasLatest.region} | loaded` : "pending"} tone="primary" />
            <TelemetryCard label="Overlay Points Loaded" value={overlayPoints.length} tone="primary" />
            <TelemetryCard label="Maintenance" value={history.maintenance ? history.maintenance.recommendation : "pending"} tone="alert" />
          </div>

          <div className="mt-3 grid gap-1 text-xs text-softwhite/75">
            <p>IoT ingest: {history.iot ? `${history.iot.sensor_id} | ${history.iot.status}` : "pending"}</p>
            <p>Satellite ingest: {history.satellite ? `${history.satellite.region} | ${history.satellite.status}` : "pending"}</p>
            <p>Atlas generation: {history.atlasGenerated ? history.atlasGenerated.status : "pending"}</p>
            <p>Atlas export: {history.atlasExported ? `${history.atlasExported.export_type} | ${history.atlasExported.status}` : "pending"}</p>
            <p>Latest atlas cache: {history.atlasLatest ? `${history.atlasLatest.region} | loaded` : "pending"}</p>
            <p>Overlay points loaded: {overlayPoints.length}</p>
            <p>Maintenance: {history.maintenance ? history.maintenance.recommendation : "pending"}</p>
          </div>

          <div className="mt-4 rounded-lg border border-neoviolet/35 bg-slatewash/35 p-4 text-xs text-softwhite/80">
            Severity overlay colors map to risk states: green baseline, yellow escalation, red critical.
          </div>
        </article>
      </section>
    </LayoutShell>
  );
}
