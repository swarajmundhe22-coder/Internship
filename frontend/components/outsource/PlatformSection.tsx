/* ============================================================
   PlatformSection — GIFIP Platform Overview
   Architecture layers + key modules with glass cards
   ============================================================ */
import { motion } from "framer-motion";
import { useInView } from "framer-motion";
import { useRef } from "react";

const CORROSION_IMG = "https://d2xsxph8kpxj0f.cloudfront.net/310519663448417147/bRTxyCJq9mgt5p2skQtMAx/gifip-corrosion-3d-KpQzx977Y9JRdxTVoBRdFV.webp";

const architectureLayers = [
  { label: "User Interface Layer", sub: "React • Next.js • TailwindCSS", color: "#4DFFD2" },
  { label: "Data Input Layer", sub: "Material • Environment • Conditions", color: "#4DFFD2" },
  { label: "Environmental Modeling Engine", sub: "Temperature • Humidity • pH • Salinity", color: "#7BE8D0" },
  { label: "Corrosion Prediction Engine", sub: "Faraday Law • Nernst Equation • Galvanic", color: "#A8D8EA" },
  { label: "Material Degradation Model", sub: "Thickness Loss • Lifespan Prediction", color: "#A8D8EA" },
  { label: "Prevention Recommendation Engine", sub: "Coatings • Cathodic Protection • Inhibitors", color: "#FF6B35" },
  { label: "Visualization Engine", sub: "Three.js • Blender • 3D Simulation", color: "#FF6B35" },
  { label: "Report Generator", sub: "PDF Export • Engineering Reports", color: "#FF8C5A" },
];

const coreModules = [
  {
    num: "A",
    title: "Data Input Layer",
    desc: "Collects environmental and structural parameters including material type, metal composition, humidity, temperature, pH level, salinity, oxygen concentration, and soil composition.",
    tags: ["Material Type", "Temperature", "pH Level", "Salinity"],
  },
  {
    num: "B",
    title: "Environmental Modeling Engine",
    desc: "Calculates how environmental conditions affect corrosion by building a comprehensive chemical environment profile with temperature acceleration factors and electrolyte conductivity.",
    tags: ["ECI Score", "Climate Model", "Pollution Effects"],
  },
  {
    num: "C",
    title: "Corrosion Prediction Engine",
    desc: "The core computational module that determines corrosion probability, type, and rate using electrochemical models including galvanic, pitting, crevice, and stress corrosion cracking.",
    tags: ["Corrosion Rate", "Type ID", "Probability"],
  },
  {
    num: "D",
    title: "Material Degradation Model",
    desc: "Predicts long-term deterioration with outputs including corrosion penetration rate, metal thickness loss, structural integrity score, and predicted infrastructure lifespan.",
    tags: ["Thickness Loss", "Lifespan", "Integrity Score"],
  },
  {
    num: "E",
    title: "Prevention Recommendation Engine",
    desc: "Analyzes simulation results and suggests engineering actions including protective coating selection, cathodic protection installation, material replacement, and corrosion inhibitors.",
    tags: ["Coatings", "Cathodic Protection", "Inhibitors"],
  },
  {
    num: "F",
    title: "Visualization Engine",
    desc: "Three-dimensional simulation shows degradation progression through corrosion spread animations, surface damage simulation, and infrastructure degradation timelines using Three.js.",
    tags: ["3D Animation", "Heat Maps", "Timeline"],
  },
];

function ArchitectureLayer({ layer, index }: { layer: typeof architectureLayers[0]; index: number }) {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: "-50px" });

  return (
    <motion.div
      ref={ref}
      initial={{ x: -30, opacity: 0 }}
      animate={inView ? { x: 0, opacity: 1 } : {}}
      transition={{ duration: 0.5, delay: index * 0.07 }}
      className="flex items-center gap-4 py-3 border-b border-white/5 group hover:border-teal-400/20 transition-colors duration-300"
    >
      <div className="w-6 h-6 flex items-center justify-center border border-white/10 group-hover:border-teal-400/40 transition-colors duration-300">
        <div className="w-1.5 h-1.5 rounded-full" style={{ background: layer.color }} />
      </div>
      <div className="flex-1">
        <div className="text-sm font-medium text-white/80 group-hover:text-white transition-colors duration-300"
          style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
          {layer.label}
        </div>
        <div className="text-xs text-white/30 mt-0.5" style={{ fontFamily: "'DM Mono', monospace" }}>
          {layer.sub}
        </div>
      </div>
      <div className="text-xs text-white/20 group-hover:text-teal-400/60 transition-colors duration-300"
        style={{ fontFamily: "'DM Mono', monospace" }}>
        {String(index + 1).padStart(2, "0")}
      </div>
    </motion.div>
  );
}

function ModuleCard({ module, index }: { module: typeof coreModules[0]; index: number }) {
  const ref = useRef(null);
  const inView = useInView(ref, { once: true, margin: "-80px" });

  return (
    <motion.div
      ref={ref}
      initial={{ y: 40, opacity: 0 }}
      animate={inView ? { y: 0, opacity: 1 } : {}}
      transition={{ duration: 0.6, delay: index * 0.1 }}
      className="glass-card p-6 group hover:border-teal-400/20 transition-all duration-400"
    >
      <div className="flex items-start justify-between mb-4">
        <div className="w-10 h-10 flex items-center justify-center border border-teal-400/20 text-teal-400 font-bold text-sm"
          style={{ fontFamily: "'DM Mono', monospace" }}>
          {module.num}
        </div>
        <span className="section-number">Module</span>
      </div>
      <h3 className="text-lg font-bold text-white mb-3" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
        {module.title}
      </h3>
      <p className="text-sm text-white/40 leading-relaxed mb-4" style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 300 }}>
        {module.desc}
      </p>
      <div className="flex flex-wrap gap-2">
        {module.tags.map((tag) => (
          <span key={tag} className="text-xs px-2 py-1 border border-white/10 text-white/40"
            style={{ fontFamily: "'DM Mono', monospace" }}>
            {tag}
          </span>
        ))}
      </div>
    </motion.div>
  );
}

export default function PlatformSection() {
  const titleRef = useRef(null);
  const titleInView = useInView(titleRef, { once: true });

  return (
    <section id="platform" className="relative py-32" style={{ background: "#050508" }}>
      <div className="container">
        {/* Section header */}
        <div className="flex flex-col lg:flex-row gap-16 mb-20">
          <div className="lg:w-1/2" ref={titleRef}>
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={titleInView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.6 }}
              className="section-number mb-6"
            >
              02 — Platform Overview
            </motion.div>
            <motion.h2
              initial={{ opacity: 0, y: 30 }}
              animate={titleInView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.7, delay: 0.1 }}
              className="text-5xl md:text-6xl font-bold text-white leading-tight"
              style={{ fontFamily: "'Space Grotesk', sans-serif", letterSpacing: "-0.03em" }}
            >
              Modular{" "}
              <span style={{ color: "#4DFFD2" }}>System</span>
              <br />Architecture
            </motion.h2>
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={titleInView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.7, delay: 0.2 }}
              className="mt-6 text-base text-white/40 leading-relaxed max-w-md"
              style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 300 }}
            >
              GIFIP follows a modular system architecture designed to integrate environmental
              chemistry analysis, material science modeling, and predictive computational simulation.
            </motion.p>
          </div>

          {/* Architecture stack */}
          <div className="lg:w-1/2">
            <div className="glass-card p-6">
              <div className="section-number mb-4">System Stack</div>
              {architectureLayers.map((layer, i) => (
                <ArchitectureLayer key={layer.label} layer={layer} index={i} />
              ))}
            </div>
          </div>
        </div>

        {/* Section divider */}
        <div className="section-divider mb-20" />

        {/* Core modules grid */}
        <div className="mb-12">
          <div className="section-number mb-4">Architecture Components</div>
          <h3 className="text-3xl font-bold text-white" style={{ fontFamily: "'Space Grotesk', sans-serif", letterSpacing: "-0.02em" }}>
            Core Engine Modules
          </h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-24">
          {coreModules.map((module, i) => (
            <ModuleCard key={module.num} module={module} index={i} />
          ))}
        </div>

        {/* Feature image */}
        <motion.div
          initial={{ opacity: 0, scale: 0.97 }}
          whileInView={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
          className="relative overflow-hidden"
          style={{ height: "480px" }}
        >
          <img
            src={CORROSION_IMG}
            alt="3D corrosion analysis visualization"
            className="w-full h-full object-cover"
            style={{ filter: "saturate(1.1) brightness(0.75)" }}
          />
          <div className="absolute inset-0" style={{
            background: "linear-gradient(to right, rgba(5,5,8,0.8) 0%, transparent 40%, transparent 60%, rgba(5,5,8,0.8) 100%), linear-gradient(to bottom, transparent 60%, rgba(5,5,8,0.9) 100%)"
          }} />
          <div className="absolute bottom-8 left-8 right-8 flex items-end justify-between">
            <div>
              <div className="section-number mb-2">Visualization Engine</div>
              <div className="text-2xl font-bold text-white" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
                3D Corrosion Analysis
              </div>
              <div className="text-sm text-white/40 mt-1" style={{ fontFamily: "'DM Mono', monospace" }}>
                Real-time structural degradation simulation
              </div>
            </div>
            <div className="flex items-center gap-3">
              <div className="w-2 h-2 rounded-full bg-teal-400 pulse-ring" />
              <span className="text-xs text-teal-400" style={{ fontFamily: "'DM Mono', monospace" }}>Live Simulation</span>
            </div>
          </div>
        </motion.div>
      </div>
    </section>
  );
}
