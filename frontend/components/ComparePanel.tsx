import { useMemo, useState } from "react";

import { SimulationComparisonResponse, SimulationRecord } from "../types/domain";

type ComparePanelProps = {
  comparison: SimulationComparisonResponse | null;
  leftSimulation: SimulationRecord | null;
  rightSimulation: SimulationRecord | null;
};

function deltaClass(value: number): string {
  if (value > 0) {
    return "text-signal";
  }
  if (value < 0) {
    return "text-lagoon";
  }
  return "text-softwhite/80";
}

function formatMetric(value: number): string {
  const abs = Math.abs(value);
  if (abs >= 1000) {
    return value.toFixed(0);
  }
  if (abs >= 10) {
    return value.toFixed(2);
  }
  return value.toFixed(4);
}

function deltaWidth(value: number, max: number): number {
  if (max <= 0) {
    return 0;
  }
  return Math.min(100, Math.max(5, (Math.abs(value) / max) * 100));
}

export function ComparePanel({ comparison, leftSimulation, rightSimulation }: ComparePanelProps) {
  const [exporting, setExporting] = useState<"pdf" | "video" | null>(null);

  const maxDelta = useMemo(() => {
    if (!comparison) {
      return 1;
    }
    const values = [
      Math.abs(comparison.corrosion_rate_delta_mm_per_year),
      Math.abs(comparison.lifespan_delta_years),
      ...Object.values(comparison.environmental_deltas).map((value) => Math.abs(value)),
      ...Object.values(comparison.material_deltas).map((value) => Math.abs(value))
    ];
    return Math.max(1, ...values);
  }, [comparison]);

  async function exportPdfSnapshot() {
    if (!comparison) {
      return;
    }
    setExporting("pdf");
    try {
      const { jsPDF } = await import("jspdf");
      const doc = new jsPDF();
      doc.setFontSize(16);
      doc.text("The On Looker - Comparison Snapshot", 12, 16);
      doc.setFontSize(10);
      doc.text(`Left Simulation: ${comparison.left_simulation_id}`, 12, 26);
      doc.text(`Right Simulation: ${comparison.right_simulation_id}`, 12, 32);
      doc.text(`Corrosion Delta: ${comparison.corrosion_rate_delta_mm_per_year.toFixed(4)} mm/y`, 12, 42);
      doc.text(`Lifespan Delta: ${comparison.lifespan_delta_years.toFixed(2)} years`, 12, 48);
      doc.text(`Risk Transition: ${comparison.risk_transition}`, 12, 54);

      let y = 64;
      doc.text("Environmental Deltas", 12, y);
      y += 6;
      Object.entries(comparison.environmental_deltas).slice(0, 8).forEach(([key, value]) => {
        doc.text(`${key}: ${value.toFixed(3)}`, 16, y);
        y += 6;
      });

      y += 4;
      doc.text("Material Deltas", 12, y);
      y += 6;
      Object.entries(comparison.material_deltas).slice(0, 8).forEach(([key, value]) => {
        doc.text(`${key}: ${value.toFixed(3)}`, 16, y);
        y += 6;
      });

      doc.save(`comparison-${comparison.left_simulation_id.slice(0, 8)}-${comparison.right_simulation_id.slice(0, 8)}.pdf`);
    } finally {
      setExporting(null);
    }
  }

  async function exportVideoPlayback() {
    if (!comparison || typeof window === "undefined" || typeof MediaRecorder === "undefined") {
      return;
    }

    setExporting("video");
    try {
      const canvas = document.createElement("canvas");
      canvas.width = 1280;
      canvas.height = 720;
      const context = canvas.getContext("2d");
      if (!context) {
        return;
      }

      const stream = canvas.captureStream(24);
      const chunks: BlobPart[] = [];
      const recorder = new MediaRecorder(stream, { mimeType: "video/webm" });
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunks.push(event.data);
        }
      };

      const frames = 72;
      recorder.start();
      for (let frame = 0; frame < frames; frame += 1) {
        const progress = frame / (frames - 1);
        context.fillStyle = "#060c1a";
        context.fillRect(0, 0, canvas.width, canvas.height);

        context.fillStyle = "#00e5ff";
        context.font = "bold 36px Arial";
        context.fillText("The On Looker Comparison Playback", 48, 64);

        context.fillStyle = "#9a4dff";
        context.font = "24px Arial";
        context.fillText(`Risk Transition: ${comparison.risk_transition}`, 48, 116);

        context.fillStyle = "#d7ecff";
        context.font = "18px Arial";
        context.fillText(`Frame ${frame + 1}/${frames}`, 1040, 64);

        const corrosionWidth = Math.max(10, Math.abs(comparison.corrosion_rate_delta_mm_per_year) * 1800 * progress);
        const lifespanWidth = Math.max(10, Math.abs(comparison.lifespan_delta_years) * 30 * progress);
        const envAggregate = Object.values(comparison.environmental_deltas).reduce((sum, value) => sum + Math.abs(value), 0);
        const materialAggregate = Object.values(comparison.material_deltas).reduce((sum, value) => sum + Math.abs(value), 0);
        const envWidth = Math.max(10, envAggregate * 0.12 * progress);
        const materialWidth = Math.max(10, materialAggregate * 0.14 * progress);

        context.fillStyle = comparison.corrosion_rate_delta_mm_per_year >= 0 ? "#ffb84d" : "#00e5ff";
        context.fillRect(48, 200, Math.min(canvas.width - 96, corrosionWidth), 48);
        context.fillStyle = "#d7ecff";
        context.fillText("Corrosion Delta", 48, 190);

        context.fillStyle = comparison.lifespan_delta_years >= 0 ? "#ffb84d" : "#00e5ff";
        context.fillRect(48, 320, Math.min(canvas.width - 96, lifespanWidth), 48);
        context.fillStyle = "#d7ecff";
        context.fillText("Lifespan Delta", 48, 310);

        context.fillStyle = "#00e5ff";
        context.fillRect(48, 430, Math.min(canvas.width - 96, envWidth), 24);
        context.fillStyle = "#d7ecff";
        context.fillText("Environment Aggregate Delta", 48, 424);

        context.fillStyle = "#9a4dff";
        context.fillRect(48, 500, Math.min(canvas.width - 96, materialWidth), 24);
        context.fillStyle = "#d7ecff";
        context.fillText("Material Aggregate Delta", 48, 494);

        context.fillStyle = "rgba(154,77,255,0.35)";
        context.fillRect(48, 612, canvas.width - 96, 6);
        context.fillStyle = "#ffb84d";
        context.fillRect(48, 612, (canvas.width - 96) * progress, 6);

        context.fillStyle = "rgba(3,14,33,0.65)";
        context.fillRect(900, 140, 330, 180);
        context.strokeStyle = "rgba(0,229,255,0.5)";
        context.strokeRect(900, 140, 330, 180);
        context.fillStyle = "#d7ecff";
        context.font = "bold 16px Arial";
        context.fillText("Legend", 920, 168);
        context.font = "13px Arial";
        context.fillStyle = "#ffb84d";
        context.fillRect(920, 184, 22, 10);
        context.fillStyle = "#d7ecff";
        context.fillText("Positive Delta", 950, 193);
        context.fillStyle = "#00e5ff";
        context.fillRect(920, 206, 22, 10);
        context.fillStyle = "#d7ecff";
        context.fillText("Negative Delta", 950, 215);
        context.fillStyle = "#9a4dff";
        context.fillRect(920, 228, 22, 10);
        context.fillStyle = "#d7ecff";
        context.fillText("Material Track", 950, 237);
        context.fillStyle = "#00e5ff";
        context.fillRect(920, 250, 22, 10);
        context.fillStyle = "#d7ecff";
        context.fillText("Environment Track", 950, 259);

        context.font = "12px Arial";
        context.fillStyle = "rgba(215,236,255,0.65)";
        context.fillText("The On Looker | Confidential Demo Watermark", 925, 700);

        await new Promise((resolve) => window.setTimeout(resolve, 42));
      }

      recorder.stop();
      await new Promise<void>((resolve) => {
        recorder.onstop = () => resolve();
      });

      const blob = new Blob(chunks, { type: "video/webm" });
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `comparison-${comparison.left_simulation_id.slice(0, 8)}-${comparison.right_simulation_id.slice(0, 8)}.webm`;
      anchor.click();
      URL.revokeObjectURL(url);
    } finally {
      setExporting(null);
    }
  }

  if (!comparison) {
    return <section className="panel p-6 text-sm text-softwhite/70">Run comparison to view scenario deltas.</section>;
  }

  return (
    <section className="panel grid gap-4 p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h3 className="font-hud text-lg text-softwhite">Scenario Delta Analysis</h3>
        <div className="flex gap-2">
          <button
            type="button"
            className="holo-btn rounded-md px-3 py-2 text-xs"
            onClick={() => void exportPdfSnapshot()}
            disabled={exporting !== null}
          >
            {exporting === "pdf" ? "Exporting PDF..." : "Export PDF Snapshot"}
          </button>
          <button
            type="button"
            className="holo-btn rounded-md px-3 py-2 text-xs"
            onClick={() => void exportVideoPlayback()}
            disabled={exporting !== null}
          >
            {exporting === "video" ? "Rendering Video..." : "Export Playback Video"}
          </button>
        </div>
      </div>

      <div className="grid gap-3 lg:grid-cols-2">
        <article className="rounded-lg border border-lagoon/40 bg-slatewash/45 p-3 shadow-neon">
          <p className="hud-label text-[10px] text-softwhite/75">Left Hologram</p>
          <p className="font-mono text-xs text-softwhite/75">{comparison.left_simulation_id}</p>
          <p className="mt-2 text-sm text-softwhite/90">Risk: {leftSimulation?.risk_classification ?? "-"}</p>
          <p className="text-sm text-softwhite/90">Corrosion: {leftSimulation ? leftSimulation.corrosion_rate_mm_per_year.toFixed(4) : "-"} mm/y</p>
          <p className="text-sm text-softwhite/90">Lifespan: {leftSimulation ? leftSimulation.estimated_lifespan_years.toFixed(2) : "-"} y</p>
        </article>
        <article className="rounded-lg border border-neoviolet/45 bg-slatewash/45 p-3 shadow-violet">
          <p className="hud-label text-[10px] text-softwhite/75">Right Hologram</p>
          <p className="font-mono text-xs text-softwhite/75">{comparison.right_simulation_id}</p>
          <p className="mt-2 text-sm text-softwhite/90">Risk: {rightSimulation?.risk_classification ?? "-"}</p>
          <p className="text-sm text-softwhite/90">Corrosion: {rightSimulation ? rightSimulation.corrosion_rate_mm_per_year.toFixed(4) : "-"} mm/y</p>
          <p className="text-sm text-softwhite/90">Lifespan: {rightSimulation ? rightSimulation.estimated_lifespan_years.toFixed(2) : "-"} y</p>
        </article>
      </div>

      <div className="grid gap-3 md:grid-cols-3">
        <article className="rounded-lg border border-lagoon/40 bg-slatewash/45 p-3 shadow-neon">
          <p className="hud-label text-[10px] text-softwhite/75">Corrosion Delta</p>
          <p className={`text-xl font-bold ${deltaClass(comparison.corrosion_rate_delta_mm_per_year)}`}>
            {comparison.corrosion_rate_delta_mm_per_year.toFixed(4)} mm/y
          </p>
          <div className="mt-2 h-2 w-full rounded bg-softwhite/10">
            <div
              className="h-2 animate-hud-pulse rounded bg-lagoon"
              style={{ width: `${deltaWidth(comparison.corrosion_rate_delta_mm_per_year, maxDelta)}%` }}
            />
          </div>
        </article>
        <article className="rounded-lg border border-lagoon/40 bg-slatewash/45 p-3 shadow-neon">
          <p className="hud-label text-[10px] text-softwhite/75">Lifespan Delta</p>
          <p className={`text-xl font-bold ${deltaClass(comparison.lifespan_delta_years)}`}>
            {comparison.lifespan_delta_years.toFixed(2)} years
          </p>
          <div className="mt-2 h-2 w-full rounded bg-softwhite/10">
            <div
              className="h-2 animate-hud-pulse rounded bg-neoviolet"
              style={{ width: `${deltaWidth(comparison.lifespan_delta_years, maxDelta)}%` }}
            />
          </div>
        </article>
        <article className="rounded-lg border border-neoviolet/45 bg-slatewash/45 p-3 shadow-violet">
          <p className="hud-label text-[10px] text-softwhite/75">Risk Transition</p>
          <p className="text-xl font-bold text-softwhite">{comparison.risk_transition}</p>
        </article>
      </div>

      <div className="grid gap-3 lg:grid-cols-2">
        <article className="rounded-lg border border-lagoon/35 bg-slatewash/40 p-3 text-sm">
          <h4 className="mb-2 font-hud text-sm text-softwhite">Environmental Deltas</h4>
          {Object.entries(comparison.environmental_deltas).map(([key, value]) => (
            <div key={key} className="mb-2">
              <p className={deltaClass(value)}>{key}: {formatMetric(value)}</p>
              <div className="h-1.5 w-full rounded bg-softwhite/10">
                <div className="h-1.5 rounded bg-lagoon/80 transition-all duration-700" style={{ width: `${deltaWidth(value, maxDelta)}%` }} />
              </div>
            </div>
          ))}
        </article>
        <article className="rounded-lg border border-neoviolet/35 bg-slatewash/40 p-3 text-sm">
          <h4 className="mb-2 font-hud text-sm text-softwhite">Material Deltas</h4>
          {Object.entries(comparison.material_deltas).map(([key, value]) => (
            <div key={key} className="mb-2">
              <p className={deltaClass(value)}>{key}: {formatMetric(value)}</p>
              <div className="h-1.5 w-full rounded bg-softwhite/10">
                <div className="h-1.5 rounded bg-neoviolet/80 transition-all duration-700" style={{ width: `${deltaWidth(value, maxDelta)}%` }} />
              </div>
            </div>
          ))}
        </article>
      </div>
    </section>
  );
}
