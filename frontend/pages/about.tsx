import { motion } from "framer-motion";
import { useState } from "react";

import { ChapterHeader, HudBadge, TacticalButton, TelemetryCard } from "../components/CinematicHud";
import { CinematicScene } from "../components/CinematicScene";
import { LayoutShell } from "../components/LayoutShell";

export default function AboutPage() {
  const [photoMissing, setPhotoMissing] = useState(false);
  const [photoIndex, setPhotoIndex] = useState(0);
  const founderPhotoSources = [
    "/brand/1000878256.jpg",
    "/brand/founder-swaraj.jpg",
    "/brand/founder-swaraj.jpeg",
    "/brand/founder-swaraj.png",
  ];
  const founderQuote = "Predictive intelligence should not feel abstract. It should feel precise, immersive, and decisive.";
  const quoteWords = founderQuote.split(" ");

  return (
    <LayoutShell
      title="About The On Lookers"
      subtitle="Who we are, what we are building, and the mission behind predictive infrastructure intelligence."
    >
      <section className="about-mobile-tight page-polish-about about-editorial-hero mb-5 grid gap-4 lg:grid-cols-[1.15fr_0.85fr]">
        <article className="panel p-6 md:p-7" data-cinematic-reveal="true">
          <p className="type-kicker hud-label">Founder Story</p>
          <h2 className="type-title mt-2 text-softwhite">Built from engineering discipline and cinematic product vision.</h2>
          <p className="type-body mt-3 text-softwhite/78">
            The On Lookers began as a focused idea: predictive infrastructure intelligence should be technically rigorous and deeply understandable for decision-makers.
            Founded by Swaraj Mundhe, a Mechanical Engineering student at PCCOE Pune, the platform is being shaped as a mission-control environment where complex risk data becomes clear, actionable foresight.
          </p>
          <div className="mt-5 flex flex-wrap gap-2">
            <HudBadge label="Founder-Led" tone="primary" />
            <HudBadge label="Predictive Systems" tone="support" />
            <HudBadge label="Cinematic UX" tone="alert" />
          </div>
        </article>

        <article className="panel relative overflow-hidden p-5 md:p-6" data-cinematic-reveal="true">
          <div className="pointer-events-none absolute inset-0">
            <div className="absolute -left-6 top-5 h-20 w-40 rounded-full bg-lagoon/20 blur-2xl" />
            <div className="absolute right-4 top-3 h-16 w-16 rounded-full bg-neoviolet/20 blur-2xl" />
          </div>
          <div className="relative z-10 flex items-start justify-between gap-3">
            <p className="type-kicker hud-label">Founder's Note</p>
            <span className="founder-monogram-badge">SM</span>
          </div>

          <div className="relative z-10 mt-3 grid gap-3 sm:grid-cols-[0.72fr_1fr] sm:items-start">
            <div className="founder-photo-frame">
              {!photoMissing ? (
                <img
                  src={founderPhotoSources[photoIndex]}
                  alt="Founder portrait of Swaraj Mundhe"
                  className="founder-photo-image h-full w-full object-cover"
                  onError={() => {
                    if (photoIndex < founderPhotoSources.length - 1) {
                      setPhotoIndex((current) => current + 1);
                    } else {
                      setPhotoMissing(true);
                    }
                  }}
                />
              ) : (
                <div className="grid h-full w-full place-items-center text-[10px] uppercase tracking-[0.14em] text-softwhite/72">
                  Founder Photo Slot
                </div>
              )}
            </div>

            <blockquote className="founder-quote border-l-2 border-lagoon/60 pl-4 text-sm italic leading-relaxed text-softwhite/82">
              <span aria-hidden="true">"</span>
              {quoteWords.map((word, index) => (
                <motion.span
                  key={`${word}-${index}`}
                  className="inline-block pr-[0.32rem]"
                  initial={{ opacity: 0, y: 7 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true, amount: 0.55 }}
                  transition={{ duration: 0.3, delay: index * 0.02, ease: [0.2, 1, 0.24, 1] }}
                >
                  {word}
                </motion.span>
              ))}
              <span aria-hidden="true">"</span>
            </blockquote>
          </div>
        </article>
      </section>

      <section
        className="story-track page-polish-about about-editorial-flow mb-5 grid gap-4 lg:grid-cols-[0.95fr_1.05fr]"
        data-story-track="true"
        data-story-curve="cinematic"
        data-story-start="top 90%"
        data-story-end="top 32%"
        data-story-scrub="0.52"
        data-story-progress-start="top 90%"
        data-story-progress-end="bottom 12%"
      >
        <article className="story-pin-column panel p-6" data-story-pin="true">
          <ChapterHeader
            eyebrow="Founder"
            title="Swaraj Mundhe"
            description="Founder of The On Lookers and a Mechanical Engineering student at PCCOE Pune, leading the vision and execution of a predictive infrastructure intelligence platform."
          />
          <div className="grid gap-2">
            <p data-story-step="true"><HudBadge label="Role: Founder" tone="primary" /></p>
            <p data-story-step="true"><HudBadge label="Background: Mechanical Engineering, PCCOE Pune" tone="support" /></p>
            <p data-story-step="true"><HudBadge label="Status: Vision And Execution In Progress" tone="alert" /></p>
          </div>
        </article>

        <div className="story-panel-stack">
          <article className="story-panel panel p-5" data-story-panel="true" data-story-ease="power4.out" data-story-offset="24">
            <ChapterHeader
              eyebrow="Mission"
              title="Predictive infrastructure intelligence with precision, clarity, and immersive design."
              description="The On Lookers exists to transform complex engineering data into cinematic, mission-control experiences that help organizations anticipate risk, make informed decisions, and operate with confidence."
            />
          </article>

          <article className="story-panel panel p-5" data-story-panel="true" data-story-ease="power3.out" data-story-offset="18">
            <ChapterHeader
              eyebrow="Identity"
              title="Scientifically rigorous. Visually compelling."
              description="We combine technical correctness with a clean, futuristic interface language so high-stakes intelligence is both trustworthy and immediately actionable."
            />
          </article>
        </div>
      </section>

      <CinematicScene
        tone="briefing"
        sceneLabel="About Sequence"
        narrative="A concise view of our product pillars, operating values, and roadmap placeholders ready for your final content."
      >
        <div className="grid gap-3 md:grid-cols-3">
          <TelemetryCard
            label="Product Pillar"
            value="Predictive"
            detail="Simulation-led corrosion forecasting and risk stratification."
            tone="primary"
          />
          <TelemetryCard
            label="Product Pillar"
            value="Decision-Ready"
            detail="Reports, governance, and comparisons for cross-team alignment."
            tone="support"
          />
          <TelemetryCard
            label="Product Pillar"
            value="Portfolio-Aware"
            detail="Atlas-style visibility into risk concentration and priority."
            tone="alert"
          />
        </div>
      </CinematicScene>

      <section className="mt-4 grid gap-4 md:grid-cols-2">
        <article className="panel p-6" data-cinematic-reveal="true">
          <p className="type-kicker hud-label">Timeline</p>
          <h2 className="type-title text-softwhite">Company Timeline</h2>
          <ul className="mt-3 grid gap-3 text-sm text-softwhite/78">
            <li className="rounded-lg border border-lagoon/30 bg-slatewash/30 p-3">
              <span className="hud-label text-[10px]">2026</span>
              <p className="mt-1">Conceptualized The On Lookers as a predictive intelligence cockpit.</p>
            </li>
          </ul>
        </article>

        <article className="panel p-6" data-cinematic-reveal="true">
          <p className="type-kicker hud-label">Values</p>
          <h2 className="type-title text-softwhite">Values And Operating Principles</h2>
          <ul className="mt-3 grid gap-2 text-sm text-softwhite/78">
            <li><span className="text-softwhite">Precision:</span> Every model and interface must be scientifically correct.</li>
            <li><span className="text-softwhite">Clarity:</span> Intelligence should be presented cleanly and decisively.</li>
            <li><span className="text-softwhite">Immersion:</span> Interfaces should feel cinematic, not transactional.</li>
            <li><span className="text-softwhite">Discipline:</span> Every decision is validated, uncompromising, and professional.</li>
            <li><span className="text-softwhite">Integrity:</span> Built to withstand scrutiny and deliver trust.</li>
          </ul>
        </article>
      </section>

      <section className="panel mt-4 p-6" data-cinematic-reveal="true">
        <ChapterHeader
          eyebrow="Call To Action"
          title="Join us in shaping the future of predictive intelligence."
          description="Step into the Command Grid and experience foresight like never before."
        />
        <div className="mt-5 flex flex-wrap gap-2">
          <TacticalButton href="/dashboard">Enter Command Grid</TacticalButton>
          <TacticalButton href="/simulations" tone="alert">Run Simulation Ops</TacticalButton>
          <TacticalButton href="/reports" tone="support">Open Intelligence Reports</TacticalButton>
        </div>
      </section>
    </LayoutShell>
  );
}
