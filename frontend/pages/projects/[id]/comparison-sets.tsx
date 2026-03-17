import Link from "next/link";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/router";

import { ChapterHeader, HudBadge, TacticalButton, TelemetryCard } from "../../../components/CinematicHud";
import { LayoutShell } from "../../../components/LayoutShell";
import { TableShell } from "../../../components/TableShell";
import { useApi } from "../../../hooks/useApi";
import {
  ComparisonSetDetail,
  ComparisonSetListItem,
  ProjectDetail,
  ProjectSimulationSummary
} from "../../../types/domain";
import { buildQueryString } from "../../../utils/query";

function formatDateTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString();
}

export default function ProjectComparisonSetsPage() {
  const router = useRouter();
  const { id } = router.query;
  const { run, loading, error } = useApi();

  const [projectName, setProjectName] = useState("Project");
  const [projectSimulations, setProjectSimulations] = useState<ProjectSimulationSummary[]>([]);
  const [comparisonSets, setComparisonSets] = useState<ComparisonSetListItem[]>([]);
  const [selectedSimulations, setSelectedSimulations] = useState<string[]>([]);
  const [setName, setSetName] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [activeSet, setActiveSet] = useState<ComparisonSetDetail | null>(null);

  const preloadSimulationId = useMemo(() => {
    const value = router.query.add_simulation_id;
    return typeof value === "string" ? value : "";
  }, [router.query.add_simulation_id]);

  useEffect(() => {
    if (!router.isReady || typeof id !== "string") {
      return;
    }

    void loadWorkspace(id);
  }, [router.isReady, id]);

  useEffect(() => {
    if (!preloadSimulationId) {
      return;
    }
    setSelectedSimulations((prev) => {
      if (prev.includes(preloadSimulationId)) {
        return prev;
      }
      if (prev.length >= 4) {
        return prev;
      }
      return [...prev, preloadSimulationId];
    });
  }, [preloadSimulationId]);

  async function loadWorkspace(projectId: string) {
    const [projectPayload, setsPayload] = await Promise.all([
      run<ProjectDetail>(`/projects/${projectId}?page=1&page_size=200`),
      run<ComparisonSetListItem[]>(`/projects/${projectId}/comparison-sets`)
    ]);

    setProjectName(projectPayload.name);
    setProjectSimulations(projectPayload.simulations.items);
    setComparisonSets(setsPayload);
  }

  function toggleSimulationSelection(simulationId: string) {
    setSelectedSimulations((prev) => {
      if (prev.includes(simulationId)) {
        return prev.filter((item) => item !== simulationId);
      }
      if (prev.length >= 4) {
        return prev;
      }
      return [...prev, simulationId];
    });
  }

  async function createComparisonSet(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (typeof id !== "string") {
      return;
    }

    setMessage(null);

    if (selectedSimulations.length < 2 || selectedSimulations.length > 4) {
      setMessage("Select between 2 and 4 simulations.");
      return;
    }

    const payload = await run<ComparisonSetDetail>(`/projects/${id}/comparison-sets`, {
      method: "POST",
      body: JSON.stringify({
        name: setName.trim() || "Untitled Comparison Set",
        simulation_ids: selectedSimulations
      })
    });

    setMessage("Comparison set created.");
    setSetName("");
    setSelectedSimulations([]);
    setActiveSet(payload);
    await loadWorkspace(id);
  }

  async function openSet(setId: string) {
    const payload = await run<ComparisonSetDetail>(`/comparison-sets/${setId}`);
    setActiveSet(payload);
  }

  async function deleteSet(setId: string) {
    if (typeof id !== "string") {
      return;
    }

    await run(`/comparison-sets/${setId}`, { method: "DELETE" });
    if (activeSet?.id === setId) {
      setActiveSet(null);
    }
    setMessage("Comparison set deleted.");
    await loadWorkspace(id);
  }

  return (
    <LayoutShell
      title={`Comparison Sets: ${projectName}`}
      subtitle="Compose and persist reusable simulation comparison packs for engineering teams."
    >
      <section className="panel mb-6 grid gap-4 p-6">
        <div className="flex flex-wrap gap-2">
          <TacticalButton href={typeof id === "string" ? `/projects/${id}` : "/projects"} tone="support">Back To Project Workspace</TacticalButton>
          {activeSet && (
            <TacticalButton href={`/simulations/compare${buildQueryString({ set_id: activeSet.id })}`} tone="alert">Open In Compare Workspace</TacticalButton>
          )}
        </div>

        <form className="grid gap-4" onSubmit={(event) => void createComparisonSet(event)}>
          <div className="rounded-xl border border-neoviolet/35 bg-slatewash/30 p-4">
            <ChapterHeader eyebrow="Comparison Module" title="Create Comparison Set" />
            <div className="grid gap-3 md:grid-cols-[1fr_auto]">
              <input
                className="glass-input rounded-md p-2 text-sm"
                value={setName}
                onChange={(event) => setSetName(event.target.value)}
                placeholder="Set name (e.g., Coastal Corridor Variants)"
              />
              <TacticalButton type="submit" disabled={loading}>
                {loading ? "Creating..." : "Create Set"}
              </TacticalButton>
            </div>
          </div>

          <div className="rounded-xl border border-lagoon/35 bg-slatewash/25 p-4">
            <div className="mb-3 flex items-center justify-between">
              <p className="hud-label text-[11px]">Simulation Picker (2-4)</p>
              <HudBadge label={`Selected: ${selectedSimulations.length}`} tone="primary" />
            </div>
            <div className="grid gap-2 md:grid-cols-2">
              {projectSimulations.map((item) => {
                const selected = selectedSimulations.includes(item.simulation_id);
                return (
                  <button
                    key={item.simulation_id}
                    type="button"
                    onClick={() => toggleSimulationSelection(item.simulation_id)}
                    className={`rounded-lg border p-3 text-left transition ${
                      selected
                        ? "animate-hud-pulse border-lagoon/80 bg-lagoon/15"
                        : "border-softwhite/20 bg-slatewash/20 hover:border-neoviolet/60"
                    }`}
                  >
                    <TelemetryCard label={item.simulation_id} value={`${item.material} | ${item.environment}`} detail={item.risk_level.toUpperCase()} tone={selected ? "alert" : "primary"} />
                  </button>
                );
              })}
            </div>
          </div>

          {message && <p className="text-sm text-signal">{message}</p>}
          {error && <p className="text-sm text-red-300">{error}</p>}
        </form>
      </section>

      <TableShell<ComparisonSetListItem>
        title="Saved Comparison Sets"
        items={comparisonSets}
        total={comparisonSets.length}
        page={1}
        pageSize={Math.max(10, comparisonSets.length || 10)}
        loading={loading}
        error={error}
        emptyMessage="No comparison sets found for this project yet."
        onPageChange={() => undefined}
        onPageSizeChange={() => undefined}
      >
        {(items) => (
          <div className="overflow-x-auto">
            <table className="min-w-full border-collapse text-sm">
              <thead>
                <tr className="neon-divider text-left text-softwhite/75">
                  <th className="px-2 py-2">Name</th>
                  <th className="px-2 py-2">Created</th>
                  <th className="px-2 py-2">Simulations</th>
                  <th className="px-2 py-2">Actions</th>
                </tr>
              </thead>
              <tbody>
                {items.map((item) => (
                  <tr key={item.id} className="neon-divider align-top transition hover:bg-lagoon/10">
                    <td className="px-2 py-3 font-semibold text-softwhite">{item.name}</td>
                    <td className="px-2 py-3 text-softwhite/75">{formatDateTime(item.created_at)}</td>
                    <td className="px-2 py-3 text-softwhite/75"><HudBadge label={String(item.simulation_count)} tone="support" /></td>
                    <td className="px-2 py-3">
                      <div className="flex flex-wrap gap-2">
                        <TacticalButton type="button" onClick={() => void openSet(item.id)}>Open Comparison</TacticalButton>
                        <TacticalButton href={`/simulations/compare${buildQueryString({ set_id: item.id })}`} tone="support">Compare Workspace</TacticalButton>
                        <TacticalButton type="button" tone="alert" onClick={() => void deleteSet(item.id)}>Delete</TacticalButton>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </TableShell>

      {activeSet && (
        <section className="panel mt-6 grid gap-3 p-6">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <ChapterHeader eyebrow="Active Set" title={activeSet.name} />
            <HudBadge label={`${activeSet.comparisons.length} pair results`} tone="support" />
          </div>
          <div className="grid gap-2">
            {activeSet.comparisons.map((pair, index) => (
              <article key={`${pair.left_simulation_id}-${pair.right_simulation_id}`} className="rounded-lg border border-lagoon/30 bg-slatewash/20 p-3 text-sm">
                <p className="font-mono text-xs text-softwhite/80">
                  Pair {index + 1}: {pair.left_simulation_id}{" -> "}{pair.right_simulation_id}
                </p>
                <p className="text-softwhite/80">Risk: <HudBadge label={pair.risk_transition} tone="alert" /></p>
                <p className="text-softwhite/70">
                  Corrosion Delta: {pair.corrosion_rate_delta_mm_per_year.toFixed(4)} mm/y | Lifespan Delta: {pair.lifespan_delta_years.toFixed(2)} years
                </p>
              </article>
            ))}
          </div>
        </section>
      )}
    </LayoutShell>
  );
}
