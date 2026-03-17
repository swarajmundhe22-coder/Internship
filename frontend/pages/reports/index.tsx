import Link from "next/link";
import { useEffect, useState } from "react";

import { ChapterHeader, HudBadge, TacticalButton } from "../../components/CinematicHud";
import { CinematicScene } from "../../components/CinematicScene";
import { FilterBar } from "../../components/FilterBar";
import { LayoutShell } from "../../components/LayoutShell";
import { TableShell } from "../../components/TableShell";
import { useDebouncedValue } from "../../hooks/useDebouncedValue";
import { useApi } from "../../hooks/useApi";
import { useUrlQueryState } from "../../hooks/useUrlQueryState";
import { PaginatedResponse, ReportListQueryParams, ReportRecord } from "../../types/domain";
import { buildQueryString, toDateTimeEnd, toDateTimeStart } from "../../utils/query";

export default function ReportsPage() {
  const { run, loading, error } = useApi();
  const { state, setQuery, isReady } = useUrlQueryState({
    page: "1",
    page_size: "10",
    simulation_id: "",
    created_from: "",
    created_to: ""
  });

  const [simulationFilterInput, setSimulationFilterInput] = useState(state.simulation_id);
  const debouncedSimulationId = useDebouncedValue(simulationFilterInput, 300);

  const [pageData, setPageData] = useState<PaginatedResponse<ReportRecord>>({
    items: [],
    total: 0,
    page: 1,
    page_size: 10
  });

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
    if (!isReady) {
      return;
    }

    const query: ReportListQueryParams = {
      page,
      page_size: pageSize,
      simulation_id: state.simulation_id || undefined,
      created_from: toDateTimeStart(state.created_from),
      created_to: toDateTimeEnd(state.created_to)
    };

    void run<PaginatedResponse<ReportRecord>>(`/reports${buildQueryString(query)}`).then(setPageData);
  }, [isReady, state.page, state.page_size, state.simulation_id, state.created_from, state.created_to]);

  return (
    <LayoutShell title="Reports" subtitle="Track generated engineering reports and lifecycle versions.">
      <section className="story-track mb-4 grid gap-4 lg:grid-cols-[0.92fr_1.08fr]" data-story-track="true">
        <article className="story-pin-column panel p-5" data-story-pin="true">
          <ChapterHeader
            eyebrow="Briefing Timeline"
            title="Narrative-led dossier operations."
            description="Pinned mission context remains visible while report records and filters reveal in cinematic sequence."
          />
          <div className="grid gap-2">
            <p data-story-step="true"><HudBadge label="Compliance stream active" tone="support" /></p>
            <p data-story-step="true"><HudBadge label="Version control online" tone="primary" /></p>
            <p data-story-step="true"><HudBadge label="Distribution channel ready" tone="alert" /></p>
          </div>
        </article>

        <div className="story-panel-stack">
          <article className="story-panel" data-story-panel="true">
            <CinematicScene
              tone="briefing"
              sceneLabel="Scene 4 / Briefing Sequence"
              narrative="Generating compliance dossier. Investor briefing ready. Deck exports dissolve like cinematic mission folders."
            >
              <ChapterHeader
                eyebrow="Briefing Layer"
                title="Compliance dossiers and investor decks are mission-ready."
                description="Filter report timelines, inspect versions, and open record details with a consistent tactical flow."
              />
            </CinematicScene>
          </article>

          <article className="story-panel panel p-5" data-story-panel="true">
            <p className="type-kicker hud-label">Sequence Focus</p>
            <p className="mt-2 text-sm text-softwhite/78">Use temporal filters, simulation IDs, and status context to keep report retrieval deterministic during high-velocity decision cycles.</p>
          </article>
        </div>
      </section>

      <TableShell
        title="Report Records"
        items={pageData.items}
        total={pageData.total}
        page={page}
        pageSize={pageSize}
        loading={loading}
        error={error}
        emptyMessage="No reports found for this page/filter selection."
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
            onReset={() => setQuery({ simulation_id: undefined, created_from: undefined, created_to: undefined })}
          />
        }
        onPageChange={(nextPage) => setQuery({ page: String(nextPage) }, { resetPage: false })}
        onPageSizeChange={(size) =>
          setQuery({ page_size: String(size), page: "1" }, { resetPage: false })
        }
      >
        {(items) => (
          <div className="grid gap-3">
            {items.map((report) => (
              <Link
                key={report.id}
                href={`/reports/${report.id}`}
                className="rounded-lg border border-neoviolet/35 bg-slatewash/40 p-4 transition hover:border-neoviolet"
              >
                <div className="mb-2"><HudBadge label={`Status: ${report.status}`} tone="support" /></div>
                <p className="type-body text-softwhite/80">Version: {report.version}</p>
                <p className="type-caption text-softwhite/78 break-all">{report.report_uri}</p>
                <div className="mt-3"><TacticalButton tone="support">Open Dossier</TacticalButton></div>
              </Link>
            ))}
          </div>
        )}
      </TableShell>
    </LayoutShell>
  );
}
