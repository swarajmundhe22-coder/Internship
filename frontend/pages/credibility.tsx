import { ChapterHeader, HudBadge, TacticalButton, TelemetryCard } from "../components/CinematicHud";
import { CinematicScene } from "../components/CinematicScene";
import { LayoutShell } from "../components/LayoutShell";

const milestones = [
  { year: "2026", title: "Platform Vision Initiated", detail: "The On Lookers conceptualized as a predictive infrastructure cockpit." },
  { year: "2026", title: "Cinematic UX Layer Built", detail: "Scroll-driven mission narrative and route transition framework deployed." },
  { year: "2026", title: "OTP Security Stack Activated", detail: "Registration and mandatory login OTP flows validated through live SMTP delivery." },
];

export default function CredibilityPage() {
  return (
    <LayoutShell
      title="Credibility"
      subtitle="Milestones, recognition cues, and roadmap confidence delivered with deliberate cinematic pacing."
    >
      <section
        className="story-track page-polish-dashboard mb-5 grid gap-4 lg:grid-cols-[0.95fr_1.05fr]"
        data-story-track="true"
        data-story-curve="cinematic"
        data-story-start="top 90%"
        data-story-end="top 34%"
        data-story-scrub="0.56"
        data-story-progress-start="top 90%"
        data-story-progress-end="bottom 12%"
      >
        <article className="story-pin-column panel p-6" data-story-pin="true">
          <ChapterHeader
            eyebrow="Reputation Layer"
            title="Credibility is revealed as a timeline, not a claim."
            description="Signals of trust appear in sequence, giving each milestone visual weight and contextual clarity."
          />
          <div className="mt-4 flex flex-wrap gap-2">
            <HudBadge label="Verified Build" tone="primary" />
            <HudBadge label="Operational Security" tone="support" />
            <HudBadge label="Roadmap Confidence" tone="alert" />
          </div>
        </article>

        <div className="story-panel-stack">
          {milestones.map((milestone, index) => (
            <article
              key={`${milestone.year}-${milestone.title}`}
              className="story-panel panel p-5"
              data-story-panel="true"
              data-story-offset={index === 0 ? "24" : "18"}
              data-story-ease={index % 2 === 0 ? "power4.out" : "power3.out"}
            >
              <p className="hud-label text-[10px]">{milestone.year}</p>
              <h3 className="mt-2 text-xl font-semibold text-softwhite">{milestone.title}</h3>
              <p className="mt-2 text-sm text-softwhite/76">{milestone.detail}</p>
            </article>
          ))}
        </div>
      </section>

      <CinematicScene
        tone="briefing"
        sceneLabel="Scene / Recognition Board"
        narrative="Credibility cards fade in as weighted proof points across product, engineering, and governance."
      >
        <div className="grid gap-3 md:grid-cols-3">
          <TelemetryCard
            label="Recognition"
            value="Security"
            detail="Mandatory OTP sign-in and traceable auth events with audit-ready logging."
            tone="primary"
          />
          <TelemetryCard
            label="Recognition"
            value="Experience"
            detail="Cinematic interface framework with route-aware storytelling choreography."
            tone="support"
          />
          <TelemetryCard
            label="Recognition"
            value="Reliability"
            detail="Structured backend architecture with verification-first delivery cadence."
            tone="alert"
          />
        </div>
      </CinematicScene>

      <section className="panel mt-4 self-start p-6" data-cinematic-reveal="true">
        <ChapterHeader
          eyebrow="Closing Scene"
          title="Ready to enter the command grid."
          description="Continue from credibility into active operations and run the next simulation narrative live."
        />
        <div className="mt-5 flex flex-wrap gap-2">
          <TacticalButton href="/auth/login">Enter With OTP</TacticalButton>
          <TacticalButton href="/dashboard" tone="support">Open Dashboard</TacticalButton>
          <TacticalButton href="/expertise" tone="alert">Back To Expertise</TacticalButton>
        </div>
      </section>
    </LayoutShell>
  );
}
