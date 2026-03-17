import Link from "next/link";
import { useRouter } from "next/router";
import { useEffect, useState } from "react";

import { ChapterHeader, HudBadge, TacticalButton } from "../../../components/CinematicHud";
import { FilterBar } from "../../../components/FilterBar";
import { LayoutShell } from "../../../components/LayoutShell";
import { TableShell } from "../../../components/TableShell";
import { useDebouncedValue } from "../../../hooks/useDebouncedValue";
import { useApi } from "../../../hooks/useApi";
import { useUrlQueryState } from "../../../hooks/useUrlQueryState";
import { PaginatedResponse, ProjectDetail, ProjectReportSummary } from "../../../types/domain";
import { buildQueryString, toDateTimeEnd, toDateTimeStart } from "../../../utils/query";

function formatDateTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString();
}

export default function ProjectReportsPage() {
  const router = useRouter();
  const { id } = router.query;
  const { run, loading, error, downloadReportPdf } = useApi();

  const { state, setQuery, isReady } = useUrlQueryState({
    page: "1",
    page_size: "10",
    simulation_id: "",
    risk_level: "",
    created_from: "",
    created_to: ""
  });

  const [projectName, setProjectName] = useState<string>("Project");
  const [simulationFilterInput, setSimulationFilterInput] = useState(state.simulation_id);
  const debouncedSimulationId = useDebouncedValue(simulationFilterInput, 300);
  const [pageData, setPageData] = useState<PaginatedResponse<ProjectReportSummary>>({
    items: [],
    total: 0,
    page: 1,
    page_size: 10
  });
  const [pdfDownloadingId, setPdfDownloadingId] = useState<string | null>(null);
  const [pdfMessage, setPdfMessage] = useState<string | null>(null);
  const [pdfError, setPdfError] = useState<string | null>(null);

  const page = Number(state.page) || 1;
  const pageSize = Number(state.page_size) || 10;

  useEffect(() => {
    setSimulationFilterInput(state.simulation_id);
  }, [state.simulation_id]);

  useEffect(() => {
    if (!isReady) {
      return;
    }
    setQuery({ simulation_id: debouncedSimulationId || undefined });
  }, [debouncedSimulationId]);

  useEffect(() => {
    if (!router.isReady || !isReady || typeof id !== "string") {
      return;
    }

    const query = buildQueryString({
      page,
      page_size: pageSize,
      simulation_id: state.simulation_id || undefined,
      risk_level: state.risk_level || undefined,
      created_from: toDateTimeStart(state.created_from),
      created_to: toDateTimeEnd(state.created_to)
    });

    void run<PaginatedResponse<ProjectReportSummary>>(`/projects/${id}/reports${query}`).then(setPageData);
  }, [
    router.isReady,
    isReady,
    id,
    state.page,
    state.page_size,
    state.simulation_id,
    state.risk_level,
    state.created_from,
    state.created_to
  ]);

  useEffect(() => {
    if (!router.isReady || typeof id !== "string") {
      return;
    }

    void run<ProjectDetail>(`/projects/${id}?page=1&page_size=1`).then((project) => setProjectName(project.name));
  }, [router.isReady, id]);

  async function onDownloadPdf(reportId: string) {
    setPdfMessage(null);
    setPdfError(null);
    setPdfDownloadingId(reportId);

    try {
      const blob = await downloadReportPdf(reportId);
      const url = window.URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `project-report-${reportId}.pdf`;
      document.body.appendChild(anchor);
      anchor.click();
      document.body.removeChild(anchor);
      window.URL.revokeObjectURL(url);
      setPdfMessage("PDF download started.");
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to download PDF";
      setPdfError(message);
    } finally {
      setPdfDownloadingId(null);
    }
  }

  return (
    <LayoutShell
      title={`Project Reports: ${projectName}`}
      subtitle="Filter and manage report records generated from project simulations."
    >
      <section className="panel mb-4 p-4">
        <ChapterHeader eyebrow="Project Reports" title="Project Report Collection" />
        <div className="flex flex-wrap gap-2 text-sm">
          <TacticalButton href={typeof id === "string" ? `/projects/${id}` : "/projects"} tone="support">Back To Project Workspace</TacticalButton>
        </div>
        {pdfMessage && <p className="mt-2 text-sm text-lagoon">{pdfMessage}</p>}
        {pdfError && <p className="mt-2 text-sm text-red-300">{pdfError}</p>}
      </section>

      <TableShell<ProjectReportSummary>
        title="Project Report Collection"
        items={pageData.items}
        total={pageData.total}
        page={page}
        pageSize={pageSize}
        loading={loading}
        error={error}
        emptyMessage="No reports found for this project and filter selection."
        filters={
          <FilterBar
            fields={[
              {
                key: "simulation_id_input",
                label: "Simulation ID",
                type: "text",
                placeholder: "UUID",
                debounceMs: 300
              },
              {
                key: "risk_level",
                label: "Risk Level",
                type: "select",
                options: [
                  { label: "Low", value: "low" },
                  { label: "Moderate", value: "moderate" },
                  { label: "High", value: "high" },
                  { label: "Critical", value: "critical" }
                ]
              },
              { key: "created_from", label: "Created From", type: "date" },
              { key: "created_to", label: "Created To", type: "date" }
            ]}
            values={{ ...state, simulation_id_input: simulationFilterInput }}
            onChange={(key, value) => {
              if (key === "simulation_id_input") {
                setSimulationFilterInput(value ?? "");
                return;
              }
              setQuery({ [key]: value });
            }}
            onReset={() =>
              setQuery({
                simulation_id: undefined,
                risk_level: undefined,
                created_from: undefined,
                created_to: undefined
              })
            }
          />
        }
        onPageChange={(nextPage) => setQuery({ page: String(nextPage) }, { resetPage: false })}
        onPageSizeChange={(size) => setQuery({ page_size: String(size), page: "1" }, { resetPage: false })}
      >
        {(items) => (
          <div className="overflow-x-auto">
            <table className="min-w-full border-collapse text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-left text-slate-600">
                  <th className="px-2 py-2">Simulation Reference</th>
                  <th className="px-2 py-2">Risk Level</th>
                  <th className="px-2 py-2">Lifespan</th>
                  <th className="px-2 py-2">Created At</th>
                  <th className="px-2 py-2">Actions</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr key={item.report_id} className="border-b border-slate-100 align-top">
                    <td className="px-2 py-3">
                      <p className="font-mono text-xs">{item.simulation_id}</p>
                      <p>{item.material} | {item.environment}</p>
                    </td>
                    <td className="px-2 py-3 uppercase"><HudBadge label={item.risk_level} tone="alert" /></td>
                    <td className="px-2 py-3">{item.lifespan_years.toFixed(1)} years</td>
                    <td className="px-2 py-3">{formatDateTime(item.created_at)}</td>
                    <td className="px-2 py-3">
                      <div className="flex flex-wrap gap-2">
                        <TacticalButton href={`/reports/${item.report_id}`}>Open Report</TacticalButton>
                        <a href={item.report_uri} target="_blank" rel="noreferrer" className="tactical-btn hud-tone-support">Download HTML</a>
                        <TacticalButton type="button" tone="support" onClick={() => void onDownloadPdf(item.report_id)} disabled={pdfDownloadingId === item.report_id}>
                          {pdfDownloadingId === item.report_id ? "Preparing PDF..." : "Download PDF"}
                        </TacticalButton>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </TableShell>
    </LayoutShell>
  );
}
