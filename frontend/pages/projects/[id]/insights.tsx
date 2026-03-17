import Link from "next/link";
import { useRouter } from "next/router";
import { useEffect, useState } from "react";

import { ChapterHeader, HudBadge, TacticalButton, TelemetryCard } from "../../../components/CinematicHud";
import { LayoutShell } from "../../../components/LayoutShell";
import { useApi } from "../../../hooks/useApi";
import { ProjectInsight } from "../../../types/domain";

function formatDateTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString();
}

export default function ProjectInsightsPage() {
  const router = useRouter();
  const { id } = router.query;
  const { run, loading, error } = useApi();
  const [insight, setInsight] = useState<ProjectInsight | null>(null);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    if (!router.isReady || typeof id !== "string") {
      return;
    }

    void run<ProjectInsight>(`/projects/${id}/insights`).then(setInsight);
  }, [router.isReady, id]);

  async function exportInsightReport() {
    if (typeof id !== "string" || typeof window === "undefined") {
      return;
    }

    setExporting(true);
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1"}/projects/${id}/insights/report`, {
        headers: {
          Authorization: `Bearer ${window.localStorage.getItem("onlooker_token") ?? ""}`
        }
      });
      if (!response.ok) {
        throw new Error(`Export failed: ${response.status}`);
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = `project-${id}-insights.txt`;
      anchor.click();
      URL.revokeObjectURL(url);
    } finally {
      setExporting(false);
    }
  }

  return (
    <LayoutShell
      title="AI Insights"
      subtitle="Cinematic risk intelligence with recommendations and anomaly detection for project leadership reviews."
    >
      <section className="panel mb-4 p-4">
        <div className="flex flex-wrap gap-2 text-sm">
          <TacticalButton href={typeof id === "string" ? `/projects/${id}` : "/projects"} tone="support">Back To Project Workspace</TacticalButton>
          <TacticalButton
            type="button"
            onClick={() => void exportInsightReport()}
            disabled={exporting}
          >
            {exporting ? "Exporting..." : "Export Insights Report"}
          </TacticalButton>
        </div>
      </section>

      <section className="panel p-6">
        {loading && <p className="text-sm text-softwhite/75">Loading AI insights...</p>}
        {error && <p className="text-sm text-red-300">{error}</p>}

        {!loading && !error && insight && (
          <div className="grid gap-4">
            <article className="rounded-xl border border-lagoon/35 bg-gradient-to-r from-lagoon/10 via-neoviolet/10 to-signal/10 p-4 shadow-neon">
              <ChapterHeader eyebrow="Generated" title="AI Risk Summary" description={insight.summary} />
              <div className="mt-2"><HudBadge label={formatDateTime(insight.generated_at)} tone="support" /></div>
            </article>

            <div className="grid gap-3 md:grid-cols-2">
              <article className="rounded-lg border border-neoviolet/40 bg-slatewash/35 p-4">
                <ChapterHeader eyebrow="AI Output" title="Recommendations" />
                <ul className="mt-2 grid gap-2 text-sm text-softwhite/85">
                  {insight.recommendations.map((item, index) => (
                    <li key={`${index}-${item}`} className="rounded-md border border-softwhite/10 bg-black/20 p-2">
                      {item}
                    </li>
                  ))}
                </ul>
              </article>

              <article className="rounded-lg border border-signal/40 bg-slatewash/35 p-4">
                <ChapterHeader eyebrow="AI Output" title="Anomaly Detection" />
                {insight.anomalies.length === 0 ? (
                  <p className="mt-2 text-sm text-softwhite/75">No active anomalies detected in the latest model run.</p>
                ) : (
                  <ul className="mt-2 grid gap-2 text-sm text-softwhite/85">
                    {insight.anomalies.map((item) => (
                      <li key={item.code} className="rounded-md border border-signal/30 bg-signal/10 p-2">
                        <HudBadge label={item.severity} tone="alert" />
                        <p className="text-xs text-softwhite/70">{item.code}</p>
                        <p className="mt-1">{item.message}</p>
                      </li>
                    ))}
                  </ul>
                )}
              </article>
            </div>
          </div>
        )}
      </section>
    </LayoutShell>
  );
}
