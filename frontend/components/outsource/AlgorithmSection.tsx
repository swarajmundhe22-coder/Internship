/* ============================================================
   AlgorithmSection — Prediction Algorithm Workflow
   Step-by-step flow with animated connectors
   ============================================================ */
import { motion, useInView } from "framer-motion";
import { useRef } from "react";

const MOLECULAR_IMG = "https://d2xsxph8kpxj0f.cloudfront.net/310519663448417147/bRTxyCJq9mgt5p2skQtMAx/gifip-molecular-7jZLtibVfo6z8fV3oNsbM6.webp";

const algorithmSteps = [
  {
    step: "01",
    title: "Parameter Collection",
    desc: "User provides input parameters: Material Type, Temperature, Humidity, Salinity, pH Level, Oxygen Concentration, Surface Coating.",
    formula: "Input: {M, T, H, pH, S, O₂, C}",
    color: "#4DFFD2",
  },
  {
    step: "02",
    title: "Environmental Risk Score",
    desc: "Calculate environmental aggressiveness. High humidity, high salinity, and acidic environments significantly increase corrosion risk.",
    formula: "ECI = f(T_factor × H_factor × EC × CR)",
    color: "#7BE8D0",
  },
  {
    step: "03",
    title: "Electrochemical Modeling",
    desc: "Models electrochemical reactions at the metal surface using Faraday's Law of Electrolysis, Nernst Equation, and Galvanic potential analysis.",
    formula: "E_corr = E° - (RT/nF) × ln([Red]/[Ox])",
    color: "#A8D8EA",
  },
  {
    step: "04",
    title: "Corrosion Type Identification",
    desc: "Based on conditions: If salinity high → pitting corrosion. If dissimilar metals → galvanic corrosion. If tensile stress → stress corrosion cracking.",
    formula: "Type = classify(S, ΔE, σ_stress)",
    color: "#A8D8EA",
  },
  {
    step: "05",
    title: "Corrosion Rate Calculation",
    desc: "Estimates corrosion penetration rate using electrochemical current density and material properties in mm/year or µm/year.",
    formula: "CR = (K × i_corr × EW) / ρ",
    color: "#FF8C5A",
  },
  {
    step: "06",
    title: "Structural Lifespan Prediction",
    desc: "Computes thickness loss over time. Remaining Thickness = Initial Thickness − Corrosion Rate × Time.",
    formula: "T_rem(t) = T₀ − CR × t",
    color: "#FF6B35",
  },
  {
    step: "07",
    title: "Risk Classification",
    desc: "System assigns a rating: Low Risk, Moderate Risk, High Risk, or Critical Risk based on structural integrity score.",
    formula: "Risk ∈ {Low, Moderate, High, Critical}",
    color: "#FF6B35",
  },
  {
    step: "08",
    title: "Prevention Strategy Selection",
    desc: "System chooses best mitigation: Coating System, Cathodic Protection, Material Replacement, or Environmental Control.",
    formula: "Strategy = optimize(cost, effectiveness, risk)",
    color: "#FF4444",
  },
];

const riskLevels = [
  { label: "Low Risk", range: "0–25%", badge: "risk-badge-low", desc: "Normal maintenance schedule" },
  { label: "Moderate Risk", range: "26–50%", badge: "risk-badge-moderate", desc: "Increased inspection frequency" },
  { label: "High Risk", range: "51–75%", badge: "risk-badge-high", desc: "Immediate preventive action" },
  { label: "Critical Risk", range: "76–100%", badge: "risk-badge-critical", desc: "Emergency intervention required" },
];

function StepCard({ step, index }: { step: typeof algorithmSteps[0]; index: number }) {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: "-60px" });

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, x: index % 2 === 0 ? -30 : 30 }}
      animate={inView ? { opacity: 1, x: 0 } : {}}
      transition={{ duration: 0.6, delay: 0.1 }}
      className="relative flex gap-6"
    >
      {/* Connector line */}
      {index < algorithmSteps.length - 1 && (
        <div className="absolute left-5 top-12 w-px h-full" style={{ background: "linear-gradient(to bottom, rgba(77,255,210,0.2), transparent)" }} />
      )}

      {/* Step number */}
      <div className="flex-shrink-0 w-10 h-10 flex items-center justify-center border text-xs font-bold z-10"
        style={{
          borderColor: step.color + "40",
          color: step.color,
          background: step.color + "10",
          fontFamily: "'DM Mono', monospace",
        }}>
        {step.step}
      </div>

      {/* Content */}
      <div className="flex-1 pb-8">
        <div className="flex items-start justify-between gap-4 mb-2">
          <h3 className="text-lg font-bold text-white" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
            {step.title}
          </h3>
        </div>
        <p className="text-sm text-white/40 leading-relaxed mb-3" style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 300 }}>
          {step.desc}
        </p>
        <div className="inline-block px-3 py-1.5 border border-white/8 text-xs text-teal-400/70"
          style={{ fontFamily: "'DM Mono', monospace", background: "rgba(77,255,210,0.04)" }}>
          {step.formula}
        </div>
      </div>
    </motion.div>
  );
}

export default function AlgorithmSection() {
  const titleRef = useRef(null);
  const titleInView = useInView(titleRef, { once: true });

  return (
    <section id="algorithm" className="relative py-32" style={{ background: "#07070d" }}>
      <div className="container">
        <div className="flex flex-col lg:flex-row gap-16">
          {/* Left: Algorithm steps */}
          <div className="lg:w-1/2">
            <div ref={titleRef}>
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={titleInView ? { opacity: 1, y: 0 } : {}}
                transition={{ duration: 0.6 }}
                className="section-number mb-6"
              >
                03 — Algorithm
              </motion.div>
              <motion.h2
                initial={{ opacity: 0, y: 30 }}
                animate={titleInView ? { opacity: 1, y: 0 } : {}}
                transition={{ duration: 0.7, delay: 0.1 }}
                className="text-4xl md:text-5xl font-bold text-white leading-tight mb-4"
                style={{ fontFamily: "'Space Grotesk', sans-serif", letterSpacing: "-0.03em" }}
              >
                Prediction{" "}
                <span style={{ color: "#4DFFD2" }}>Algorithm</span>
                <br />Workflow
              </motion.h2>
              <motion.p
                initial={{ opacity: 0, y: 20 }}
                animate={titleInView ? { opacity: 1, y: 0 } : {}}
                transition={{ duration: 0.7, delay: 0.2 }}
                className="text-sm text-white/40 leading-relaxed mb-12 max-w-md"
                style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 300 }}
              >
                An 8-step computational pipeline that transforms raw environmental and
                material parameters into actionable corrosion predictions and prevention strategies.
              </motion.p>
            </div>

            <div className="space-y-0">
              {algorithmSteps.map((step, i) => (
                <StepCard key={step.step} step={step} index={i} />
              ))}
            </div>
          </div>

          {/* Right: Visual + Risk classification */}
          <div className="lg:w-1/2 space-y-8">
            {/* Molecular image */}
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              whileInView={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.8 }}
              viewport={{ once: true }}
              className="relative overflow-hidden"
              style={{ height: "320px" }}
            >
              <img
                src={MOLECULAR_IMG}
                alt="Molecular corrosion simulation"
                className="w-full h-full object-cover"
                style={{ filter: "saturate(1.1) brightness(0.8)" }}
              />
              <div className="absolute inset-0" style={{
                background: "linear-gradient(to bottom, transparent 50%, rgba(7,7,13,0.9) 100%)"
              }} />
              <div className="absolute bottom-6 left-6">
                <div className="section-number mb-1">Electrochemical Model</div>
                <div className="text-lg font-bold text-white" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
                  Iron Oxide Crystal Formation
                </div>
              </div>
            </motion.div>

            {/* Risk classification */}
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7 }}
              viewport={{ once: true }}
              className="glass-card p-6"
            >
              <div className="section-number mb-4">Risk Classification System</div>
              <div className="space-y-3">
                {riskLevels.map((risk, i) => (
                  <motion.div
                    key={risk.label}
                    initial={{ opacity: 0, x: 20 }}
                    whileInView={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.4, delay: i * 0.1 }}
                    viewport={{ once: true }}
                    className="flex items-center justify-between py-3 border-b border-white/5"
                  >
                    <div className="flex items-center gap-3">
                      <span className={`text-xs px-2 py-1 ${risk.badge}`}
                        style={{ fontFamily: "'DM Mono', monospace" }}>
                        {risk.label}
                      </span>
                      <span className="text-xs text-white/30" style={{ fontFamily: "'DM Mono', monospace" }}>
                        {risk.desc}
                      </span>
                    </div>
                    <span className="text-xs text-white/40" style={{ fontFamily: "'DM Mono', monospace" }}>
                      {risk.range}
                    </span>
                  </motion.div>
                ))}
              </div>
            </motion.div>

            {/* Tech stack */}
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7, delay: 0.1 }}
              viewport={{ once: true }}
              className="glass-card p-6"
            >
              <div className="section-number mb-4">Free Technology Stack</div>
              <div className="grid grid-cols-2 gap-4">
                {[
                  { cat: "Frontend", tools: ["React", "Next.js", "TailwindCSS"] },
                  { cat: "Backend", tools: ["Python", "FastAPI"] },
                  { cat: "Scientific", tools: ["NumPy", "SciPy", "Pandas"] },
                  { cat: "Visualization", tools: ["Three.js", "Blender"] },
                  { cat: "Database", tools: ["PostgreSQL", "SQLite"] },
                  { cat: "AI Models", tools: ["Ollama", "Open LLM"] },
                ].map((group) => (
                  <div key={group.cat}>
                    <div className="text-xs text-teal-400/60 mb-2" style={{ fontFamily: "'DM Mono', monospace" }}>
                      {group.cat}
                    </div>
                    {group.tools.map((tool) => (
                      <div key={tool} className="text-sm text-white/60 py-0.5" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
                        {tool}
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            </motion.div>
          </div>
        </div>
      </div>
    </section>
  );
}
