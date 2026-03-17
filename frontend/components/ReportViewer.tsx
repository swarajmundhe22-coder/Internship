import { useMemo, useState } from "react";

import { GeneratedReport, PaginatedResponse, ReportRecord } from "../types/domain";
import { useApi } from "../hooks/useApi";
import { VisualizationPanel } from "./VisualizationPanel";

type ReportViewerProps = {
  report: GeneratedReport;
};

export function ReportViewer({ report }: ReportViewerProps) {
  const { run, downloadReportPdf } = useApi();
  const intensity = report.visual_summary.intensity_map[0]?.value ?? 0;
  const [pdfLoading, setPdfLoading] = useState(false);
  const [pdfMessage, setPdfMessage] = useState<string | null>(null);
  const [pdfError, setPdfError] = useState<string | null>(null);

  const riskValue = useMemo(() => String(report.metrics.risk_classification).toLowerCase(), [report.metrics.risk_classification]);
  const riskClass = riskValue === "critical"
    ? "text-signal"
    : riskValue === "high"
      ? "text-orange-400"
      : riskValue === "moderate"
        ? "text-lagoon"
        : "text-emerald-400";

  async function resolveReportId(): Promise<string> {
    const directId = (report as GeneratedReport & { report_id?: string }).report_id;
    if (directId) {
      return directId;
    }

    // If generate payload omitted report ID, resolve latest report by simulation reference.
    const page = await run<PaginatedResponse<ReportRecord>>(
      `/reports?simulation_id=${report.simulation_id}&page=1&page_size=1`
    );
    const found = page.items[0]?.id;
    if (!found) {
      throw new Error("No report record found for this simulation.");
    }
    return found;
  }

  async function onDownloadPdf() {
    setPdfLoading(true);
    setPdfMessage(null);
    setPdfError(null);

    try {
      const reportId = await resolveReportId();
      const blob = await downloadReportPdf(reportId);
      const url = window.URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `simulation-report-${report.simulation_id}.pdf`;
      document.body.appendChild(anchor);
      anchor.click();
      document.body.removeChild(anchor);
      window.URL.revokeObjectURL(url);
      setPdfMessage("PDF download started.");
    } catch (err) {
      setPdfError(err instanceof Error ? err.message : "Failed to download PDF.");
    } finally {
      setPdfLoading(false);
    }
  }

  return (
    <section className="panel grid gap-4 p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h3 className="text-lg font-semibold text-softwhite">Generated Corrosion Report</h3>
        <button
          type="button"
          className="holo-btn rounded-md px-3 py-2 text-xs"
          onClick={() => void onDownloadPdf()}
          disabled={pdfLoading}
        >
          {pdfLoading ? "Preparing PDF..." : "Download PDF"}
        </button>
      </div>
      {pdfMessage && <p className="text-xs text-lagoon">{pdfMessage}</p>}
      {pdfError && <p className="text-xs text-red-300">{pdfError}</p>}

      <div className="grid gap-3 md:grid-cols-3">
        <article className="rounded-lg border border-lagoon/40 bg-slatewash/40 p-3">
          <p className="hud-label text-[10px]">Corrosion Rate</p>
          <p className="text-xl font-bold text-softwhite">{Number(report.metrics.corrosion_rate_mm_per_year).toFixed(4)} mm/y</p>
        </article>
        <article className="rounded-lg border border-signal/40 bg-slatewash/40 p-3">
          <p className="hud-label text-[10px]">Risk</p>
          <p className={`text-xl font-bold uppercase ${riskClass}`}>{String(report.metrics.risk_classification)}</p>
        </article>
        <article className="rounded-lg border border-neoviolet/40 bg-slatewash/40 p-3">
          <p className="hud-label text-[10px]">Lifespan</p>
          <p className="text-xl font-bold text-softwhite">{Number(report.metrics.estimated_lifespan_years).toFixed(1)} years</p>
        </article>
      </div>

      <div className="grid gap-3 lg:grid-cols-2">
        <article className="rounded-lg border border-lagoon/30 bg-slatewash/35 p-3 text-sm">
          <h4 className="mb-2 font-semibold text-softwhite">Material Profile</h4>
          {Object.entries(report.material).map(([key, value]) => (
            <p key={key} className="text-softwhite/75">{key}: {String(value)}</p>
          ))}
        </article>
        <article className="rounded-lg border border-neoviolet/30 bg-slatewash/35 p-3 text-sm">
          <h4 className="mb-2 font-semibold text-softwhite">Environment Profile</h4>
          {Object.entries(report.environment).map(([key, value]) => (
            <p key={key} className="text-softwhite/75">{key}: {String(value)}</p>
          ))}
        </article>
      </div>

      <article className="rounded-lg border border-signal/30 bg-slatewash p-3 text-sm">
        <h4 className="mb-1 font-semibold text-softwhite">Maintenance Recommendation</h4>
        <p className="text-softwhite/80">{report.recommendation_summary}</p>
      </article>

      <div className="rounded-lg border border-lagoon/30 bg-slatewash/35 p-3">
        <h4 className="mb-2 font-semibold text-softwhite">Intensity Map</h4>
        <div className="grid gap-2 text-sm">
          {report.visual_summary.intensity_map.map((entry) => (
            <div key={entry.label} className="grid grid-cols-[140px_1fr_60px] items-center gap-2">
              <span className="text-softwhite/75">{entry.label}</span>
              <div className="h-2 rounded-full bg-slatewash/70">
                <div className="h-2 rounded-full bg-signal" style={{ width: `${entry.value}%` }} />
              </div>
              <span className="text-softwhite/75">{entry.value.toFixed(1)}</span>
            </div>
          ))}
        </div>
      </div>

      <VisualizationPanel intensity={intensity} />
    </section>
  );
}
