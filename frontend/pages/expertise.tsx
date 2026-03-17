import Link from "next/link";

import { ChapterHeader, TacticalButton, TelemetryCard } from "../components/CinematicHud";
import { CinematicScene } from "../components/CinematicScene";
import { LayoutShell } from "../components/LayoutShell";

const capabilityScenes = [
  {
    title: "Predictive Intelligence",
    detail: "Translate degradation signals into foresight with explainable simulation models and confidence views.",
    tone: "primary" as const,
  },
  {
    title: "Simulation Direction",
    detail: "Run scenario sequences with material, climate, and intervention controls in one cinematic command lane.",
    tone: "support" as const,
  },
  {
    title: "Cinematic UX Systems",
    detail: "Build mission-grade interfaces where narrative pacing and decision context move together.",
    tone: "alert" as const,
  },
  {
    title: "Governance Readiness",
    detail: "Deliver audit-safe traces, approvals, and report outputs for executive and engineering stakeholders.",
    tone: "primary" as const,
  },
];

export default function ExpertisePage() {
  return (
    <LayoutShell
      title="Expertise"
      subtitle="Strategy, creative systems, and technical execution revealed as cinematic production scenes."
    >
      <section
        className="story-track page-polish-home mb-5 grid gap-4 lg:grid-cols-[1.02fr_0.98fr]"
        data-story-track="true"
        data-story-curve="cinematic"
        data-story-start="top 90%"
        data-story-end="top 34%"
        data-story-scrub="0.56"
        data-story-progress-start="top 90%"
        data-story-progress-end="bottom 12%"
      >
        <article className="story-pin-column panel p-6 md:p-7" data-story-pin="true">
          <ChapterHeader
            eyebrow="Production Storyboard"
            title="Capabilities presented as scenes, not static blocks."
            description="Each capability enters with measured pacing and layered context, so teams read strategy and execution as one motion narrative."
          />
          <ol className="landing-steps mt-4 grid gap-3">
            <li data-story-step="true"><span>01</span><p>Strategic framing sets constraints, outcomes, and risk tolerance.</p></li>
            <li data-story-step="true"><span>02</span><p>Creative direction transforms complexity into clear story-driven interfaces.</p></li>
            <li data-story-step="true"><span>03</span><p>Technical production operationalizes data into reliable decision systems.</p></li>
          </ol>
        </article>

        <div className="story-panel-stack">
          {capabilityScenes.map((scene, index) => (
            <article
              key={scene.title}
              className="story-panel panel p-5 md:p-6"
              data-story-panel="true"
              data-story-offset={index === 0 ? "24" : "18"}
              data-story-ease={index % 2 === 0 ? "power4.out" : "power3.out"}
            >
              <TelemetryCard
                label="Capability"
                value={scene.title}
                detail={scene.detail}
                tone={scene.tone}
              />
            </article>
          ))}
        </div>
      </section>

      <CinematicScene
        tone="mission"
        sceneLabel="Scene / Expertise Grid"
        narrative="Hover-reactive capability cards create micro-interactions that reinforce depth and momentum."
      >
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <Link href="/simulations" className="landing-tile" data-cinematic-reveal="true">
            <h3>Strategy</h3>
            <p>Roadmap architecture for predictive programs and portfolio-level value capture.</p>
          </Link>
          <Link href="/dashboard" className="landing-tile" data-cinematic-reveal="true">
            <h3>Creative</h3>
            <p>Narrative-grade visual language with cinematic pacing and motion discipline.</p>
          </Link>
          <Link href="/visualization/mission-control" className="landing-tile" data-cinematic-reveal="true">
            <h3>Tech</h3>
            <p>High-fidelity implementation across data, interaction, and visualization layers.</p>
          </Link>
          <Link href="/admin/governance" className="landing-tile" data-cinematic-reveal="true">
            <h3>Production</h3>
            <p>Reliable delivery with governance, resilience, and repeatable deployment standards.</p>
          </Link>
        </div>
      </CinematicScene>

      <section className="panel mt-4 self-start p-6" data-cinematic-reveal="true">
        <ChapterHeader
          eyebrow="Next Scene"
          title="Move from capability to proof."
          description="Continue into the credibility sequence to review milestones, recognition points, and roadmap confidence signals."
        />
        <div className="mt-5 flex flex-wrap gap-2">
          <TacticalButton href="/credibility">Open Credibility Scene</TacticalButton>
          <TacticalButton href="/" tone="support">Back To Identity</TacticalButton>
        </div>
      </section>
    </LayoutShell>
  );
}
