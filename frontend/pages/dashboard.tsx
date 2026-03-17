import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import { ChapterHeader, HudBadge, TacticalButton, TelemetryCard } from "../components/CinematicHud";
import { CinematicScene } from "../components/CinematicScene";
import { LayoutShell } from "../components/LayoutShell";
import { useApi } from "../hooks/useApi";
import {
  AnalyticsSummary,
  RiskDistributionDatum,
  SimulationsOverTimeDatum,
  UsageDatum
} from "../types/domain";
import { phaseStoryboard } from "../utils/storyboard";

function getRiskColor(risk: string): string {
  const key = risk.toLowerCase();
  if (key === "critical") {
    return "bg-signal";
  }
  if (key === "high") {
    return "bg-amber-500";
  }
  if (key === "moderate") {
    return "bg-lagoon";
  }
  return "bg-emerald-500";
}

export default function DashboardPage() {
  const {
    getAnalyticsSummary,
    getMaterialUsage,
    getEnvironmentUsage,
    getRiskDistribution,
    getSimulationsOverTime
  } = useApi();

  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [materialUsage, setMaterialUsage] = useState<UsageDatum[]>([]);
  const [environmentUsage, setEnvironmentUsage] = useState<UsageDatum[]>([]);
  const [riskDistribution, setRiskDistribution] = useState<RiskDistributionDatum[]>([]);
  const [simulationsOverTime, setSimulationsOverTime] = useState<SimulationsOverTimeDatum[]>([]);
  const [analyticsError, setAnalyticsError] = useState<string | null>(null);

  const maxTimeCount = useMemo(
    () => Math.max(...simulationsOverTime.map((item) => item.count), 1),
    [simulationsOverTime]
  );
  const maxUsageCount = useMemo(
    () => Math.max(...materialUsage.map((item) => item.count), ...environmentUsage.map((item) => item.count), 1),
    [materialUsage, environmentUsage]
  );

  useEffect(() => {
    let active = true;

    async function loadAnalytics() {
      try {
        const [summaryData, materialData, environmentData, riskData, overTimeData] = await Promise.all([
          getAnalyticsSummary(),
          getMaterialUsage(),
          getEnvironmentUsage(),
          getRiskDistribution(),
          getSimulationsOverTime()
        ]);

        if (!active) {
          return;
        }

        setSummary(summaryData);
        setMaterialUsage(materialData.slice(0, 6));
        setEnvironmentUsage(environmentData.slice(0, 6));
        setRiskDistribution(riskData);
        setSimulationsOverTime(overTimeData.slice(-10));
      } catch (err) {
        if (!active) {
          return;
        }
        const message = err instanceof Error ? err.message : "Unable to load analytics";
        setAnalyticsError(message);
      }
    }

    void loadAnalytics();

    return () => {
      active = false;
    };
  }, []);

  return (
    <LayoutShell
      title="Engineering Intelligence Dashboard"
      subtitle="Predict corrosion, model risk, and guide intervention with GIFIP-driven analytics."
    >
      <div className="page-polish-dashboard">
      <section className="story-track mb-5 grid gap-4 lg:grid-cols-[0.95fr_1.05fr]" data-story-track="true" data-story-curve="balanced" data-story-start="top 87%" data-story-end="top 38%" data-story-scrub="0.54" data-story-progress-start="top 86%" data-story-progress-end="bottom 14%" data-story-compact-start="top 84%" data-story-compact-beat-start="top 72%">
        <article className="story-pin-column panel p-6" data-story-pin="true">
          <ChapterHeader
            eyebrow="Chapter Sequence"
            title="Mission telemetry translated into action windows."
            description="Pinned command context stays in view while operational cards advance in tactical order."
          />
          <div className="mt-3 grid gap-2 sm:grid-cols-3 lg:grid-cols-1">
            <p data-story-step="true"><HudBadge label="Telemetry ingestion live" tone="primary" /></p>
            <p data-story-step="true"><HudBadge label="Risk classification active" tone="support" /></p>
            <p data-story-step="true"><HudBadge label="Mitigation priority queue armed" tone="alert" /></p>
          </div>
        </article>

        <div className="story-panel-stack">
          <article className="story-panel panel p-5" data-story-panel="true" data-story-ease="power2.out" data-story-offset="24" data-story-scrub="0.52">
            <ChapterHeader
              eyebrow="Chapter 1 / Establishing Shot"
              title="Planetary intelligence HUD synchronized."
              description="Camera lock on mission core, telemetry overlays online, response channels active."
            />
          </article>

          <article className="story-panel panel p-5" data-story-panel="true" data-story-ease="power3.out" data-story-offset="20" data-story-scrub="0.5">
            <ChapterHeader
              eyebrow="Chapter 2 / Tactical Metrics"
              title="Risk and simulation flow are now in combat view."
              description="Scroll-linked pacing guides readers from visibility to decision with no context breaks."
            />
          </article>

          <article className="story-panel panel p-5" data-story-panel="true" data-story-ease="power4.out" data-story-offset="16" data-story-scrub="0.46">
            <ChapterHeader
              eyebrow="Chapter 3 / Execution"
              title="Move from analytics to intervention pathways."
              description="Open simulations, compare scenarios, and publish reports from the same command thread."
            />
            <div className="mt-4 flex flex-wrap gap-2">
              <TacticalButton href="/simulations">Simulate</TacticalButton>
              <TacticalButton href="/simulations/compare" tone="alert">Compare</TacticalButton>
              <TacticalButton href="/reports" tone="support">Report</TacticalButton>
            </div>
          </article>
        </div>
      </section>

      <CinematicScene
        tone="mission"
        sceneLabel="Scene 2 / Mission Control"
        narrative="Planetary hologram online. HUD panels are synchronized for simulations, reports, atlas, and governance operations."
      >
        <div className="grid gap-3 lg:grid-cols-[1.2fr,0.8fr]">
          <section className="pointer-events-none relative h-32 overflow-hidden rounded-xl border border-lagoon/25 bg-slatewash/20">
            <div className="absolute -left-10 top-3 h-24 w-40 animate-row-sheen rounded-full bg-lagoon/20 blur-2xl" />
            <div className="absolute right-4 top-1 h-20 w-32 animate-hud-pulse rounded-full bg-neoviolet/20 blur-2xl" />
            <div className="absolute inset-0 bg-[linear-gradient(90deg,rgba(0,229,255,0.08)_1px,transparent_1px),linear-gradient(rgba(0,229,255,0.06)_1px,transparent_1px)] bg-[size:34px_34px] opacity-40" />
            <div className="absolute left-1/2 top-1/2 h-28 w-28 -translate-x-1/2 -translate-y-1/2 rounded-full border border-lagoon/40 bg-lagoon/10 shadow-neon" />
          </section>

          <aside className="rounded-xl border border-softwhite/20 bg-slatewash/35 p-3">
            <p className="hud-label text-[10px]">Orbit Modules</p>
            <div className="mt-2 grid grid-cols-2 gap-2 text-xs text-softwhite/85">
              <Link href="/simulations" className="rounded-md border border-lagoon/35 bg-lagoon/10 px-2 py-1">Simulations</Link>
              <Link href="/reports" className="rounded-md border border-neoviolet/35 bg-neoviolet/10 px-2 py-1">Reports</Link>
              <Link href="/visualization/global-risk-atlas" className="rounded-md border border-signal/35 bg-signal/10 px-2 py-1">Atlas</Link>
              <Link href="/admin/governance" className="rounded-md border border-emerald-400/35 bg-emerald-500/10 px-2 py-1">Governance</Link>
            </div>
          </aside>
        </div>
      </CinematicScene>

      <section className="panel mb-4 p-6">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div>
            <p className="type-kicker hud-label">Portfolio Analytics</p>
            <p className="type-body text-softwhite/70">Live aggregate telemetry across simulations, reports, and risk posture.</p>
          </div>
        </div>

        {analyticsError && <p className="text-sm text-red-300">{analyticsError}</p>}

        {!analyticsError && (
          <>
            <div className="grid gap-3 md:grid-cols-3">
              <TelemetryCard label="Total Simulations" value={summary?.total_simulations ?? "-"} tone="primary" />
              <TelemetryCard label="Total Reports" value={summary?.total_reports ?? "-"} tone="support" />
              <TelemetryCard label="High Risk Alerts" value={summary?.high_risk_count ?? "-"} tone="alert" />
            </div>

            <div className="mt-4 grid gap-3 lg:grid-cols-2">
              <article className="rounded-lg border border-lagoon/30 bg-slatewash/30 p-4">
                <h3 className="mb-3 text-sm font-semibold text-softwhite">Simulations Over Time</h3>
                <div className="grid gap-2">
                  {simulationsOverTime.map((entry) => (
                    <div key={entry.bucket} className="grid grid-cols-[120px_1fr_50px] items-center gap-2 text-xs">
                      <span className="font-mono text-softwhite/75">{entry.bucket}</span>
                      <div className="h-2 rounded-full bg-slatewash/60">
                        <div
                          className="h-2 rounded-full bg-lagoon"
                          style={{ width: `${Math.max((entry.count / maxTimeCount) * 100, 5)}%` }}
                        />
                      </div>
                      <span className="text-softwhite/75">{entry.count}</span>
                    </div>
                  ))}
                </div>
              </article>

              <article className="rounded-lg border border-signal/30 bg-slatewash/30 p-4">
                <h3 className="mb-3 text-sm font-semibold text-softwhite">Risk Distribution</h3>
                <div className="grid gap-2">
                  {riskDistribution.map((entry) => (
                    <div key={entry.risk_level} className="grid grid-cols-[100px_1fr_50px] items-center gap-2 text-xs">
                      <span className="uppercase text-softwhite/75">{entry.risk_level}</span>
                      <div className="h-2 rounded-full bg-slatewash/60">
                        <div className={`h-2 rounded-full ${getRiskColor(entry.risk_level)}`} style={{ width: `${Math.max(entry.count * 10, 5)}%` }} />
                      </div>
                      <span className="text-softwhite/75">{entry.count}</span>
                    </div>
                  ))}
                </div>
              </article>
            </div>

            <div className="mt-4 grid gap-3 lg:grid-cols-2">
              <article className="rounded-lg border border-neoviolet/30 bg-slatewash/30 p-4">
                <h3 className="mb-3 text-sm font-semibold text-softwhite">Top Materials</h3>
                <div className="grid gap-2">
                  {materialUsage.map((entry) => (
                    <div key={entry.name} className="grid grid-cols-[1fr_120px_40px] items-center gap-2 text-xs">
                      <span className="truncate text-softwhite/75">{entry.name}</span>
                      <div className="h-2 rounded-full bg-slatewash/60">
                        <div
                          className="h-2 rounded-full bg-neoviolet"
                          style={{ width: `${Math.max((entry.count / maxUsageCount) * 100, 5)}%` }}
                        />
                      </div>
                      <span className="text-softwhite/75">{entry.count}</span>
                    </div>
                  ))}
                </div>
              </article>

              <article className="rounded-lg border border-lagoon/30 bg-slatewash/30 p-4">
                <h3 className="mb-3 text-sm font-semibold text-softwhite">Top Environments</h3>
                <div className="grid gap-2">
                  {environmentUsage.map((entry) => (
                    <div key={entry.name} className="grid grid-cols-[1fr_120px_40px] items-center gap-2 text-xs">
                      <span className="truncate text-softwhite/75">{entry.name}</span>
                      <div className="h-2 rounded-full bg-slatewash/60">
                        <div
                          className="h-2 rounded-full bg-lagoon"
                          style={{ width: `${Math.max((entry.count / maxUsageCount) * 100, 5)}%` }}
                        />
                      </div>
                      <span className="text-softwhite/75">{entry.count}</span>
                    </div>
                  ))}
                </div>
              </article>
            </div>
          </>
        )}
      </section>

      <section className="panel mb-4 p-5">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="font-hud text-sm">AAA Storyboard Progression</h2>
          <p className="text-xs text-softwhite/65">Phases 1-10 mapped as cinematic sequence</p>
        </div>
        <div className="grid gap-2 md:grid-cols-2 xl:grid-cols-3">
          {phaseStoryboard.slice(0, 6).map((scene) => (
            <article key={scene.phase} className="rounded-lg border border-softwhite/15 bg-black/20 p-3 text-xs">
              <p className="hud-label text-[9px]">Phase {scene.phase}</p>
              <p className="mt-1 font-semibold text-softwhite">{scene.name}</p>
              <p className="mt-1 text-softwhite/70">{scene.narrative}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        <article className="panel p-6">
          <p className="type-kicker text-softwhite/65">Asset Intelligence</p>
          <h2 className="type-title text-softwhite">Materials Registry</h2>
          <p className="type-body mt-2 text-softwhite/70">Manage electrochemical profiles for alloys and structural materials.</p>
          <div className="mt-4"><TacticalButton href="/materials">Open Materials</TacticalButton></div>
        </article>
        <article className="panel p-6">
          <p className="type-kicker text-softwhite/65">Environmental Chemistry</p>
          <h2 className="type-title text-softwhite">Profile Library</h2>
          <p className="type-body mt-2 text-softwhite/70">Store corrosion-driving exposure environments and chemistry baselines.</p>
          <div className="mt-4"><TacticalButton href="/environments" tone="support">Open Environments</TacticalButton></div>
        </article>
        <article className="panel p-6">
          <p className="type-kicker text-softwhite/65">Failure Forecasting</p>
          <h2 className="type-title text-softwhite">Simulation Operations</h2>
          <p className="type-body mt-2 text-softwhite/70">Run predictive simulations and inspect risk and lifespan outputs.</p>
          <div className="mt-4"><TacticalButton href="/simulations" tone="alert">Open Simulations</TacticalButton></div>
        </article>
        <article className="panel p-6">
          <p className="type-kicker text-softwhite/65">Comparative Insight</p>
          <h2 className="type-title text-softwhite">Scenario Delta Engine</h2>
          <p className="type-body mt-2 text-softwhite/70">Compare two simulation outcomes to quantify corrosion and lifespan deltas.</p>
          <div className="mt-4"><TacticalButton href="/simulations/compare" tone="alert">Open Comparison</TacticalButton></div>
        </article>
        <article className="panel p-6">
          <p className="type-kicker text-softwhite/65">Portfolio Workspace</p>
          <h2 className="type-title text-softwhite">Projects And Access</h2>
          <p className="type-body mt-2 text-softwhite/70">Sign in, create projects, and save strategic simulation scenarios.</p>
          <div className="mt-4"><TacticalButton href="/projects" tone="support">Open Projects</TacticalButton></div>
        </article>
      </section>
      </div>
    </LayoutShell>
  );
}
