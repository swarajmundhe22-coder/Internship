/* ============================================================
   RoadmapSection — 4-Phase Startup Roadmap
   Timeline visualization with phase details
   ============================================================ */
import { motion, useInView } from "framer-motion";
import { useRef, useState } from "react";

const phases = [
  {
    num: "01",
    title: "Research Prototype",
    timeline: "0–6 months",
    status: "active",
    goal: "Working MVP",
    deliverables: [
      "Corrosion prediction engine",
      "Environmental modeling module",
      "Material database (core metals)",
      "Basic visualization module",
      "Algorithm validation framework",
    ],
    color: "#4DFFD2",
  },
  {
    num: "02",
    title: "Engineering Tool Platform",
    timeline: "6–18 months",
    status: "planned",
    goal: "Engineers begin using the platform",
    deliverables: [
      "Infrastructure simulation modules",
      "Report generation system",
      "Industry-specific datasets",
      "3D visualization engine",
      "API integration layer",
    ],
    color: "#7BE8D0",
  },
  {
    num: "03",
    title: "SaaS Platform",
    timeline: "2–4 years",
    status: "future",
    goal: "Commercial deployment",
    deliverables: [
      "Predictive maintenance analytics",
      "Infrastructure monitoring tools",
      "Enterprise dashboards",
      "Multi-tenant architecture",
      "Subscription billing system",
    ],
    color: "#FF8C5A",
  },
  {
    num: "04",
    title: "Infrastructure Intelligence Network",
    timeline: "4+ years",
    status: "vision",
    goal: "Global predictive infrastructure platform",
    deliverables: [
      "IoT sensor network integration",
      "Satellite environmental data feeds",
      "Digital infrastructure twins",
      "Global corrosion risk atlas",
      "Real-time monitoring network",
    ],
    color: "#FF6B35",
  },
];

const statusConfig = {
  active: { label: "In Progress", color: "#4DFFD2" },
  planned: { label: "Planned", color: "#7BE8D0" },
  future: { label: "Future", color: "#FF8C5A" },
  vision: { label: "Vision", color: "#FF6B35" },
};

export default function RoadmapSection() {
  const [activePhase, setActivePhase] = useState(0);
  const titleRef = useRef(null);
  const titleInView = useInView(titleRef, { once: true });

  const phase = phases[activePhase];

  return (
    <section id="roadmap" className="relative py-32" style={{ background: "#07070d" }}>
      <div className="container">
        {/* Header */}
        <div ref={titleRef} className="mb-16">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={titleInView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: 0.6 }}
            className="section-number mb-6"
          >
            07 — Roadmap
          </motion.div>
          <motion.h2
            initial={{ opacity: 0, y: 30 }}
            animate={titleInView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: 0.7, delay: 0.1 }}
            className="text-4xl md:text-5xl font-bold text-white leading-tight"
            style={{ fontFamily: "'Space Grotesk', sans-serif", letterSpacing: "-0.03em" }}
          >
            Startup{" "}
            <span style={{ color: "#4DFFD2" }}>Roadmap</span>
          </motion.h2>
        </div>

        {/* Timeline track */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7 }}
          viewport={{ once: true }}
          className="relative mb-12"
        >
          {/* Progress line */}
          <div className="absolute top-5 left-0 right-0 h-px bg-white/8" />
          <div
            className="absolute top-5 left-0 h-px transition-all duration-500"
            style={{
              width: `${(activePhase / (phases.length - 1)) * 100}%`,
              background: "linear-gradient(to right, #4DFFD2, #FF6B35)",
            }}
          />

          <div className="flex justify-between relative">
            {phases.map((p, i) => (
              <button
                key={p.num}
                onClick={() => setActivePhase(i)}
                className="flex flex-col items-center gap-3 group"
              >
                <div
                  className="w-10 h-10 rounded-full border-2 flex items-center justify-center text-xs font-bold transition-all duration-300 z-10"
                  style={{
                    borderColor: i <= activePhase ? p.color : "rgba(255,255,255,0.1)",
                    background: i === activePhase ? p.color + "20" : i < activePhase ? p.color + "10" : "rgba(5,5,8,1)",
                    color: i <= activePhase ? p.color : "rgba(255,255,255,0.3)",
                    fontFamily: "'DM Mono', monospace",
                  }}
                >
                  {p.num}
                </div>
                <div className="hidden md:block text-center">
                  <div
                    className="text-xs font-medium transition-colors duration-300"
                    style={{
                      fontFamily: "'Space Grotesk', sans-serif",
                      color: i === activePhase ? "#fff" : "rgba(255,255,255,0.3)",
                    }}
                  >
                    {p.title}
                  </div>
                  <div className="text-xs mt-0.5" style={{
                    fontFamily: "'DM Mono', monospace",
                    color: i <= activePhase ? p.color + "80" : "rgba(255,255,255,0.15)",
                  }}>
                    {p.timeline}
                  </div>
                </div>
              </button>
            ))}
          </div>
        </motion.div>

        {/* Phase detail */}
        <motion.div
          key={activePhase}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="glass-card p-8"
        >
          <div className="flex flex-col lg:flex-row gap-8">
            <div className="lg:w-1/2">
              <div className="flex items-center gap-3 mb-4">
                <span
                  className="text-xs px-2 py-1"
                  style={{
                    fontFamily: "'DM Mono', monospace",
                    color: statusConfig[phase.status as keyof typeof statusConfig].color,
                    border: `1px solid ${statusConfig[phase.status as keyof typeof statusConfig].color}30`,
                    background: statusConfig[phase.status as keyof typeof statusConfig].color + "10",
                  }}
                >
                  {statusConfig[phase.status as keyof typeof statusConfig].label}
                </span>
                <span className="text-xs text-white/30" style={{ fontFamily: "'DM Mono', monospace" }}>
                  {phase.timeline}
                </span>
              </div>

              <h3
                className="text-3xl font-bold text-white mb-2"
                style={{ fontFamily: "'Space Grotesk', sans-serif", letterSpacing: "-0.02em" }}
              >
                Phase {phase.num}
              </h3>
              <h4
                className="text-xl font-medium mb-4"
                style={{ fontFamily: "'Space Grotesk', sans-serif", color: phase.color }}
              >
                {phase.title}
              </h4>
              <p className="text-sm text-white/40 leading-relaxed" style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 300 }}>
                Goal: {phase.goal}
              </p>
            </div>

            <div className="lg:w-1/2">
              <div className="section-number mb-4">Key Deliverables</div>
              <div className="space-y-2">
                {phase.deliverables.map((item, i) => (
                  <motion.div
                    key={item}
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.3, delay: i * 0.08 }}
                    className="flex items-center gap-3 py-2.5 border-b border-white/5"
                  >
                    <div className="w-1 h-1 rounded-full flex-shrink-0" style={{ background: phase.color }} />
                    <span className="text-sm text-white/60" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
                      {item}
                    </span>
                  </motion.div>
                ))}
              </div>
            </div>
          </div>
        </motion.div>

        {/* Navigation buttons */}
        <div className="flex justify-between mt-6">
          <button
            onClick={() => setActivePhase(Math.max(0, activePhase - 1))}
            disabled={activePhase === 0}
            className="btn-outline disabled:opacity-30"
          >
            ← Previous Phase
          </button>
          <button
            onClick={() => setActivePhase(Math.min(phases.length - 1, activePhase + 1))}
            disabled={activePhase === phases.length - 1}
            className="btn-outline disabled:opacity-30"
          >
            Next Phase →
          </button>
        </div>
      </div>
    </section>
  );
}
