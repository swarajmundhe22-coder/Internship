import Link from "next/link";
import { useRouter } from "next/router";
import { useEffect, useMemo, useState } from "react";

import { ChapterHeader, HudBadge, TacticalButton, TelemetryCard } from "../../../components/CinematicHud";
import { FilterBar } from "../../../components/FilterBar";
import { LayoutShell } from "../../../components/LayoutShell";
import { useApi } from "../../../hooks/useApi";
import { useUrlQueryState } from "../../../hooks/useUrlQueryState";
import { ProjectActivityEvent } from "../../../types/domain";
import { toDateTimeEnd, toDateTimeStart } from "../../../utils/query";

function formatDateTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString();
}

function renderMetadata(metadata: Record<string, string | number | boolean | null>): string {
  const entries = Object.entries(metadata);
  if (entries.length === 0) {
    return "-";
  }

  return entries
    .slice(0, 4)
    .map(([key, value]) => `${key}: ${String(value)}`)
    .join(" | ");
}

function eventGlow(action: string): string {
  const key = action.toLowerCase();
  if (key.includes("collaborator")) {
    return "bg-neoviolet shadow-[0_0_16px_rgba(154,77,255,0.75)]";
  }
  if (key.includes("report")) {
    return "bg-signal shadow-[0_0_16px_rgba(255,184,77,0.8)]";
  }
  if (key.includes("simulation")) {
    return "bg-lagoon shadow-[0_0_16px_rgba(0,229,255,0.75)]";
  }
  return "bg-emerald-400 shadow-[0_0_16px_rgba(52,211,153,0.75)]";
}

export default function ProjectActivityPage() {
  const router = useRouter();
  const { id } = router.query;
  const { getProjectActivity, loading, error } = useApi();

  const { state, setQuery, isReady } = useUrlQueryState({
    user_id: "",
    action: "",
    created_from: "",
    created_to: ""
  });

  const [events, setEvents] = useState<ProjectActivityEvent[]>([]);

  const actionOptions = useMemo(
    () => [
      { label: "All", value: "" },
      { label: "Project Created", value: "project_created" },
      { label: "Simulation Saved", value: "simulation_saved" },
      { label: "Report Generated", value: "report_generated" },
      { label: "Collaborator Added", value: "collaborator_added" },
      { label: "Collaborator Updated", value: "collaborator_updated" },
      { label: "Collaborator Removed", value: "collaborator_removed" }
    ],
    []
  );

  useEffect(() => {
    if (!router.isReady || !isReady || typeof id !== "string") {
      return;
    }

    void getProjectActivity(id, {
      user_id: state.user_id || undefined,
      action: state.action || undefined,
      created_from: toDateTimeStart(state.created_from),
      created_to: toDateTimeEnd(state.created_to)
    }).then(setEvents);
  }, [
    router.isReady,
    isReady,
    id,
    state.user_id,
    state.action,
    state.created_from,
    state.created_to
  ]);

  return (
    <LayoutShell title="Project Activity Timeline" subtitle="Chronological event stream for project collaboration and simulation workflows.">
      <section className="panel mb-4 p-4">
        <ChapterHeader eyebrow="Timeline Module" title="Project Activity Timeline" />
        <div className="flex flex-wrap gap-2 text-sm">
          <TacticalButton href={typeof id === "string" ? `/projects/${id}` : "/projects"} tone="support">Back To Project Workspace</TacticalButton>
        </div>
      </section>

      <section className="panel p-6">
        <FilterBar
          fields={[
            {
              key: "user_id",
              label: "User ID",
              type: "text",
              placeholder: "Filter by user UUID"
            },
            {
              key: "action",
              label: "Action",
              type: "select",
              options: actionOptions
            },
            { key: "created_from", label: "From", type: "date" },
            { key: "created_to", label: "To", type: "date" }
          ]}
          values={state}
          onChange={(key, value) => setQuery({ [key]: value })}
          onReset={() =>
            setQuery({
              user_id: undefined,
              action: undefined,
              created_from: undefined,
              created_to: undefined
            })
          }
        />

        {loading && <p className="text-sm text-softwhite/70">Loading activity timeline...</p>}
        {error && <p className="text-sm text-red-300">{error}</p>}

        {!loading && !error && events.length === 0 && (
          <p className="text-sm text-softwhite/70">No activity events match the active filters.</p>
        )}

        {!loading && !error && events.length > 0 && (
          <ol className="relative grid gap-4 pl-6 before:absolute before:bottom-0 before:left-[0.62rem] before:top-1 before:w-px before:bg-gradient-to-b before:from-lagoon/80 before:via-neoviolet/60 before:to-transparent">
            {events.map((event) => (
              <li key={event.id} className="relative rounded-xl border border-lagoon/30 bg-slatewash/35 p-4 transition hover:border-lagoon/60 hover:shadow-neon">
                <span className={`absolute -left-6 top-6 h-3 w-3 rounded-full ${eventGlow(event.action)} animate-hud-pulse`} />

                <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
                  <HudBadge label={event.action.replace(/_/g, " ")} tone="support" />
                  <span className="text-xs text-softwhite/70">{formatDateTime(event.timestamp)}</span>
                </div>

                <div className="hud-grid md:grid-cols-2">
                  <TelemetryCard label="User" value={event.user_email ?? event.user_id} tone="primary" />
                  <TelemetryCard label="Metadata" value={renderMetadata(event.metadata)} tone="support" />
                </div>
              </li>
            ))}
          </ol>
        )}
      </section>
    </LayoutShell>
  );
}
