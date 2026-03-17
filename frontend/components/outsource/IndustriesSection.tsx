/* ============================================================
   IndustriesSection — 9 Industries served by GIFIP
   Horizontal scrolling cards with hover effects
   ============================================================ */
import { motion, useInView } from "framer-motion";
import { useRef } from "react";

const industries = [
  {
    num: "01",
    title: "Oil & Gas Pipelines",
    desc: "Predict corrosion in transmission and distribution pipelines across onshore and offshore environments.",
    icon: "⬡",
    accent: "#4DFFD2",
  },
  {
    num: "02",
    title: "Bridge Engineering",
    desc: "Assess structural steel degradation in bridges exposed to atmospheric and marine environments.",
    icon: "⬡",
    accent: "#7BE8D0",
  },
  {
    num: "03",
    title: "Marine Shipbuilding",
    desc: "Model hull corrosion, propeller degradation, and ballast tank deterioration in seawater.",
    icon: "⬡",
    accent: "#A8D8EA",
  },
  {
    num: "04",
    title: "Automotive Manufacturing",
    desc: "Analyze body panel and chassis corrosion resistance across diverse climate conditions.",
    icon: "⬡",
    accent: "#A8D8EA",
  },
  {
    num: "05",
    title: "Energy Power Plants",
    desc: "Monitor turbine blade, boiler tube, and cooling system degradation in high-temperature environments.",
    icon: "⬡",
    accent: "#FF8C5A",
  },
  {
    num: "06",
    title: "Chemical Processing",
    desc: "Predict vessel, reactor, and piping corrosion in aggressive chemical environments.",
    icon: "⬡",
    accent: "#FF6B35",
  },
  {
    num: "07",
    title: "Construction Infrastructure",
    desc: "Evaluate rebar corrosion in concrete structures and steel frame building degradation.",
    icon: "⬡",
    accent: "#FF6B35",
  },
  {
    num: "08",
    title: "Railway Infrastructure",
    desc: "Assess track, bridge, and rolling stock corrosion in varying atmospheric conditions.",
    icon: "⬡",
    accent: "#FF4444",
  },
  {
    num: "09",
    title: "Offshore Drilling Platforms",
    desc: "Simulate corrosion on jacket structures, risers, and subsea equipment in deep marine environments.",
    icon: "⬡",
    accent: "#FF3535",
  },
];

export default function IndustriesSection() {
  const titleRef = useRef(null);
  const titleInView = useInView(titleRef, { once: true });

  return (
    <section id="industries" className="relative py-32 overflow-hidden" style={{ background: "#050508" }}>
      {/* Background gradient */}
      <div className="absolute inset-0 pointer-events-none" style={{
        background: "radial-gradient(ellipse 60% 40% at 80% 50%, rgba(77,255,210,0.03) 0%, transparent 70%)"
      }} />

      <div className="container">
        {/* Header */}
        <div ref={titleRef} className="flex flex-col lg:flex-row items-start lg:items-end justify-between gap-8 mb-16">
          <div>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={titleInView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.6 }}
              className="section-number mb-6"
            >
              06 — Industries
            </motion.div>
            <motion.h2
              initial={{ opacity: 0, y: 30 }}
              animate={titleInView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.7, delay: 0.1 }}
              className="text-4xl md:text-5xl font-bold text-white leading-tight"
              style={{ fontFamily: "'Space Grotesk', sans-serif", letterSpacing: "-0.03em" }}
            >
              9 Critical{" "}
              <span style={{ color: "#4DFFD2" }}>Industries</span>
            </motion.h2>
          </div>
          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={titleInView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: 0.7, delay: 0.2 }}
            className="text-sm text-white/40 max-w-sm"
            style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 300 }}
          >
            GIFIP serves the most corrosion-critical sectors globally, providing
            specialized prediction models for each industry's unique environmental challenges.
          </motion.p>
        </div>

        {/* Industries grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {industries.map((industry, i) => (
            <motion.div
              key={industry.num}
              initial={{ opacity: 0, y: 30 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: i * 0.07 }}
              viewport={{ once: true, margin: "-60px" }}
              className="group relative glass-card p-6 hover:border-white/15 transition-all duration-400 overflow-hidden"
            >
              {/* Hover accent */}
              <div
                className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-400"
                style={{ background: `radial-gradient(ellipse 60% 60% at 20% 20%, ${industry.accent}08 0%, transparent 70%)` }}
              />

              <div className="relative z-10">
                <div className="flex items-start justify-between mb-4">
                  <span className="text-xs text-white/20 font-bold" style={{ fontFamily: "'DM Mono', monospace" }}>
                    {industry.num}
                  </span>
                  <div
                    className="w-2 h-2 rounded-full opacity-40 group-hover:opacity-100 transition-opacity duration-300"
                    style={{ background: industry.accent }}
                  />
                </div>

                <h3
                  className="text-lg font-bold text-white/80 group-hover:text-white mb-3 transition-colors duration-300"
                  style={{ fontFamily: "'Space Grotesk', sans-serif" }}
                >
                  {industry.title}
                </h3>

                <p
                  className="text-sm text-white/35 leading-relaxed group-hover:text-white/50 transition-colors duration-300"
                  style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 300 }}
                >
                  {industry.desc}
                </p>

                <div
                  className="mt-4 pt-4 border-t border-white/5 flex items-center justify-between"
                >
                  <span
                    className="text-xs opacity-0 group-hover:opacity-100 transition-opacity duration-300"
                    style={{ color: industry.accent, fontFamily: "'DM Mono', monospace" }}
                  >
                    View Module →
                  </span>
                  <div
                    className="h-px flex-1 mx-4 opacity-0 group-hover:opacity-100 transition-opacity duration-300"
                    style={{ background: `linear-gradient(to right, ${industry.accent}40, transparent)` }}
                  />
                </div>
              </div>
            </motion.div>
          ))}
        </div>

        {/* Stats row */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7 }}
          viewport={{ once: true }}
          className="mt-16 grid grid-cols-2 md:grid-cols-4 gap-px border border-white/5"
          style={{ background: "rgba(255,255,255,0.03)" }}
        >
          {[
            { val: "$2.5T", label: "Annual global corrosion cost" },
            { val: "3.4%", label: "Of global GDP lost to corrosion" },
            { val: "25-30%", label: "Preventable with modern methods" },
            { val: "50yr+", label: "Infrastructure lifespan extension" },
          ].map((stat) => (
            <div key={stat.label} className="p-8 border-r border-white/5 last:border-r-0">
              <div className="text-3xl font-bold text-white mb-2" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
                {stat.val}
              </div>
              <div className="text-xs text-white/30" style={{ fontFamily: "'DM Mono', monospace" }}>
                {stat.label}
              </div>
            </div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
