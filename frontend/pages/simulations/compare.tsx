import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/router";

import { ComparePanel } from "../../components/ComparePanel";
import { LayoutShell } from "../../components/LayoutShell";
import { useApi } from "../../hooks/useApi";
import { ComparisonSetDetail, PaginatedResponse, SimulationComparisonResponse, SimulationRecord } from "../../types/domain";

type CompareForm = {
  left_simulation_id: string;
  right_simulation_id: string;
};

export default function SimulationComparePage() {
  const router = useRouter();
  const { run, loading, error } = useApi();
  const [simulations, setSimulations] = useState<SimulationRecord[]>([]);
  const [comparisonSet, setComparisonSet] = useState<ComparisonSetDetail | null>(null);
  const [activeSetComparisonIndex, setActiveSetComparisonIndex] = useState(0);
  const [comparison, setComparison] = useState<SimulationComparisonResponse | null>(null);
  const [form, setForm] = useState<CompareForm>({ left_simulation_id: "", right_simulation_id: "" });

  useEffect(() => {
    if (!router.isReady) {
      return;
    }
    void loadSimulations();
    void loadComparisonSet();
  }, [router.isReady]);

  async function loadComparisonSet() {
    const setId = typeof router.query.set_id === "string" ? router.query.set_id : "";
    if (!setId) {
      setComparisonSet(null);
      return;
    }

    const payload = await run<ComparisonSetDetail>(`/comparison-sets/${setId}`);
    setComparisonSet(payload);
    setActiveSetComparisonIndex(0);
    setComparison(payload.comparisons[0] ?? null);
  }

  async function loadSimulations() {
    const response = await run<PaginatedResponse<SimulationRecord>>("/simulations?page=1&page_size=100");
    setSimulations(response.items);
    const prefilledLeft = typeof router.query.left_simulation_id === "string" ? router.query.left_simulation_id : "";
    const prefilledRight = typeof router.query.right_simulation_id === "string" ? router.query.right_simulation_id : "";

    if (response.items.length >= 2) {
      const fallbackLeft = response.items[0].id;
      const fallbackRight = response.items[1].id;
      setForm({
        left_simulation_id: prefilledLeft || fallbackLeft,
        right_simulation_id: prefilledRight || (prefilledLeft ? fallbackLeft : fallbackRight)
      });
    } else if (response.items.length === 1) {
      setForm({
        left_simulation_id: prefilledLeft || response.items[0].id,
        right_simulation_id: prefilledRight || response.items[0].id
      });
    }
  }

  async function compare(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const result = await run<SimulationComparisonResponse>("/compare/simulations", {
      method: "POST",
      body: JSON.stringify(form)
    });
    setComparison(result);
  }

  const leftSimulation = simulations.find((item) => item.id === form.left_simulation_id) ?? null;
  const rightSimulation = simulations.find((item) => item.id === form.right_simulation_id) ?? null;

  const setMode = Boolean(comparisonSet);

  return (
    <LayoutShell
      title="Scenario Comparison"
      subtitle="Run side-by-side delta analysis across two simulation records."
    >
      {setMode && comparisonSet && (
        <section className="panel mb-6 grid gap-3 p-6">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h2 className="font-hud text-base text-softwhite">Comparison Set Mode: {comparisonSet.name}</h2>
            <p className="text-xs text-softwhite/70">{comparisonSet.simulation_ids.length} simulations</p>
          </div>
          <div className="flex flex-wrap gap-2">
            {comparisonSet.comparisons.map((item, index) => (
              <button
                key={`${item.left_simulation_id}-${item.right_simulation_id}`}
                type="button"
                className={`rounded-md px-3 py-2 text-xs transition ${
                  index === activeSetComparisonIndex
                    ? "animate-hud-pulse border border-lagoon/70 bg-lagoon/20 text-softwhite"
                    : "holo-btn"
                }`}
                onClick={() => {
                  setActiveSetComparisonIndex(index);
                  setComparison(item);
                }}
              >
                Pair {index + 1}
              </button>
            ))}
          </div>
        </section>
      )}

      <section className="panel mb-6 p-6">
        <form className="grid gap-4 md:grid-cols-3" onSubmit={(event) => void compare(event)}>
          <label className="grid gap-1 text-sm">
            <span className="hud-label text-[10px]">Left simulation</span>
            <select
              className="glass-input rounded-md p-2"
              value={form.left_simulation_id}
              onChange={(event) => setForm((prev) => ({ ...prev, left_simulation_id: event.target.value }))}
              required
            >
              <option value="">Select simulation</option>
              {simulations.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.id.slice(0, 8)} | {item.risk_classification.toUpperCase()} | {item.corrosion_rate_mm_per_year.toFixed(4)}
                </option>
              ))}
            </select>
          </label>

          <label className="grid gap-1 text-sm">
            <span className="hud-label text-[10px]">Right simulation</span>
            <select
              className="glass-input rounded-md p-2"
              value={form.right_simulation_id}
              onChange={(event) => setForm((prev) => ({ ...prev, right_simulation_id: event.target.value }))}
              required
            >
              <option value="">Select simulation</option>
              {simulations.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.id.slice(0, 8)} | {item.risk_classification.toUpperCase()} | {item.corrosion_rate_mm_per_year.toFixed(4)}
                </option>
              ))}
            </select>
          </label>

          <div className="flex items-end">
            <button className="holo-btn w-full rounded-md px-3 py-2 text-sm" type="submit" disabled={loading}>
              {loading ? "Comparing..." : "Compare"}
            </button>
          </div>
        </form>

        {error && <p className="mt-3 text-sm text-red-300">{error}</p>}
      </section>

      <ComparePanel
        comparison={comparison}
        leftSimulation={leftSimulation}
        rightSimulation={rightSimulation}
      />
    </LayoutShell>
  );
}
