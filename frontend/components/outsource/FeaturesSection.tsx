/* ============================================================
   FeaturesSection — 100+ Platform Features
   Grouped by modules with animated reveal cards
   ============================================================ */
import { useState } from "react";
import { motion, AnimatePresence, useInView } from "framer-motion";
import { useRef } from "react";

const featureGroups = [
  {
    id: "material",
    label: "Material Database",
    count: 10,
    features: [
      "Metal database", "Alloy database", "Galvanic series reference",
      "Corrosion resistance index", "Material compatibility tool",
      "Alloy composition viewer", "Corrosion history database",
      "Metal density database", "Electrochemical potential table", "Corrosion case library",
    ],
  },
  {
    id: "environmental",
    label: "Environmental Analysis",
    count: 10,
    features: [
      "Humidity corrosion impact", "Temperature corrosion impact",
      "Salinity corrosion analysis", "Soil chemistry analysis",
      "Atmospheric corrosion analysis", "Marine environment modeling",
      "Industrial pollution impact", "Acid rain corrosion model",
      "Water chemistry modeling", "Climate influence modeling",
    ],
  },
  {
    id: "prediction",
    label: "Corrosion Prediction",
    count: 10,
    features: [
      "Corrosion probability calculator", "Galvanic corrosion predictor",
      "Pitting corrosion predictor", "Crevice corrosion predictor",
      "Stress corrosion cracking model", "Corrosion rate estimator",
      "Electrochemical reaction model", "Metal dissolution simulation",
      "Oxidation simulation", "Electrolysis modeling",
    ],
  },
  {
    id: "simulation",
    label: "Infrastructure Simulation",
    count: 10,
    features: [
      "Pipeline corrosion simulation", "Bridge corrosion simulation",
      "Marine vessel corrosion model", "Storage tank degradation simulation",
      "Offshore platform corrosion model", "Underground pipe corrosion model",
      "Structural steel corrosion model", "Infrastructure lifespan calculator",
      "Degradation progression simulation", "Corrosion spread visualization",
    ],
  },
  {
    id: "visualization",
    label: "Visualization Tools",
    count: 10,
    features: [
      "3D corrosion animation", "Corrosion surface damage rendering",
      "Degradation timeline visualization", "Corrosion heat maps",
      "Environmental risk maps", "Structural damage charts",
      "Corrosion growth graphs", "Metal thickness loss charts",
      "Corrosion comparison charts", "Corrosion severity visual scale",
    ],
  },
  {
    id: "engineering",
    label: "Engineering Tools",
    count: 10,
    features: [
      "Corrosion inspection planner", "Coating selection assistant",
      "Inhibitor recommendation tool", "Material upgrade suggestions",
      "Maintenance schedule generator", "Corrosion risk scoring system",
      "Inspection interval calculator", "Corrosion cost estimator",
      "Structural risk report generator", "Corrosion prevention checklist",
    ],
  },
  {
    id: "reporting",
    label: "Reporting",
    count: 10,
    features: [
      "Corrosion risk report", "Infrastructure health report",
      "Maintenance recommendation report", "Corrosion analysis summary",
      "Inspection planning report", "Corrosion monitoring report",
      "Environmental corrosion profile", "Structural lifespan report",
      "Corrosion cost impact report", "Engineering risk analysis",
    ],
  },
  {
    id: "education",
    label: "Education Tools",
    count: 10,
    features: [
      "Corrosion tutorials", "Corrosion case studies",
      "Corrosion reaction diagrams", "Corrosion prevention guides",
      "Corrosion chemistry explanations", "Corrosion laboratory examples",
      "Corrosion failure analysis", "Corrosion learning simulations",
      "Corrosion training modules", "Corrosion knowledge library",
    ],
  },
  {
    id: "platform",
    label: "Platform Utilities",
    count: 10,
    features: [
      "Project saving", "Simulation history",
      "Parameter presets", "Export reports",
      "Share analysis results", "User dashboard",
      "Corrosion scenario comparison", "Model parameter tuning",
      "Corrosion dataset export", "Infrastructure simulation presets",
    ],
  },
  {
    id: "system",
    label: "System Tools",
    count: 10,
    features: [
      "API integration", "User authentication",
      "Cloud synchronization", "Local simulation mode",
      "Data backup", "Configuration management",
      "Version tracking", "Experiment logging",
      "System analytics", "Performance monitoring",
    ],
  },
];

export default function FeaturesSection() {
  const [activeGroup, setActiveGroup] = useState("material");
  const titleRef = useRef(null);
  const titleInView = useInView(titleRef, { once: true });

  const active = featureGroups.find((g) => g.id === activeGroup) || featureGroups[0];

  return (
    <section id="features" className="relative py-32" style={{ background: "#050508" }}>
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
              04 — Features
            </motion.div>
            <motion.h2
              initial={{ opacity: 0, y: 30 }}
              animate={titleInView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.7, delay: 0.1 }}
              className="text-4xl md:text-5xl font-bold text-white leading-tight"
              style={{ fontFamily: "'Space Grotesk', sans-serif", letterSpacing: "-0.03em" }}
            >
              100+ Platform{" "}
              <span style={{ color: "#4DFFD2" }}>Features</span>
            </motion.h2>
          </div>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={titleInView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: 0.7, delay: 0.2 }}
            className="text-sm text-white/40 max-w-sm"
            style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 300 }}
          >
            Comprehensive engineering intelligence across 10 specialized modules,
            covering every aspect of corrosion prediction and infrastructure management.
          </motion.div>
        </div>

        <div className="flex flex-col lg:flex-row gap-8">
          {/* Left: Group tabs */}
          <div className="lg:w-72 flex-shrink-0">
            <div className="space-y-1">
              {featureGroups.map((group, i) => (
                <motion.button
                  key={group.id}
                  initial={{ opacity: 0, x: -20 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.4, delay: i * 0.05 }}
                  viewport={{ once: true }}
                  onClick={() => setActiveGroup(group.id)}
                  className={`w-full flex items-center justify-between px-4 py-3 text-left transition-all duration-300 ${
                    activeGroup === group.id
                      ? "border-l-2 border-teal-400 bg-teal-400/5 text-white"
                      : "border-l-2 border-transparent text-white/40 hover:text-white/70 hover:border-white/20"
                  }`}
                >
                  <span className="text-sm font-medium" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
                    {group.label}
                  </span>
                  <span className="text-xs" style={{
                    fontFamily: "'DM Mono', monospace",
                    color: activeGroup === group.id ? "#4DFFD2" : "rgba(255,255,255,0.2)"
                  }}>
                    {group.count}
                  </span>
                </motion.button>
              ))}
            </div>
          </div>

          {/* Right: Feature list */}
          <div className="flex-1">
            <AnimatePresence mode="wait">
              <motion.div
                key={activeGroup}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.4 }}
                className="glass-card p-8"
              >
                <div className="flex items-center justify-between mb-6">
                  <div>
                    <div className="section-number mb-1">{active.count} features</div>
                    <h3 className="text-2xl font-bold text-white" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
                      {active.label}
                    </h3>
                  </div>
                  <div className="text-4xl font-bold text-white/5" style={{ fontFamily: "'DM Mono', monospace" }}>
                    {String(featureGroups.findIndex(g => g.id === activeGroup) + 1).padStart(2, "0")}
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {active.features.map((feature, i) => (
                    <motion.div
                      key={feature}
                      initial={{ opacity: 0, x: 10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ duration: 0.3, delay: i * 0.04 }}
                      className="flex items-center gap-3 py-2.5 border-b border-white/5 group"
                    >
                      <div className="w-1 h-1 rounded-full bg-teal-400/50 group-hover:bg-teal-400 transition-colors duration-300 flex-shrink-0" />
                      <span className="text-sm text-white/60 group-hover:text-white/90 transition-colors duration-300"
                        style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
                        {feature}
                      </span>
                    </motion.div>
                  ))}
                </div>
              </motion.div>
            </AnimatePresence>

            {/* Future features callout */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
              viewport={{ once: true }}
              className="mt-4 glass-card-orange p-6"
            >
              <div className="flex items-start gap-4">
                <div className="w-8 h-8 flex items-center justify-center border border-orange-400/30 text-orange-400 text-xs flex-shrink-0"
                  style={{ fontFamily: "'DM Mono', monospace" }}>
                  +
                </div>
                <div>
                  <div className="section-number mb-1" style={{ color: "rgba(255,107,53,0.5)" }}>Future Expansion</div>
                  <div className="text-sm font-bold text-white/80 mb-2" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
                    300+ Advanced Features Roadmap
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {["IoT Sensor Integration", "Satellite Environmental Data", "Digital Twin Modeling", "AI Degradation Forecasting", "Real-time Monitoring", "Global Risk Atlas"].map((f) => (
                      <span key={f} className="text-xs px-2 py-1 border border-orange-400/20 text-orange-400/60"
                        style={{ fontFamily: "'DM Mono', monospace" }}>
                        {f}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </div>
    </section>
  );
}
