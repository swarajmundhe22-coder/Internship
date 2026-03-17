/* ============================================================
   SimulationSection — Interactive Corrosion Simulation Dashboard
   Parameter inputs + real-time result display
   ============================================================ */
import { useState, useCallback } from "react";
import { motion, useInView } from "framer-motion";
import { useRef } from "react";

const PIPELINE_IMG = "https://d2xsxph8kpxj0f.cloudfront.net/310519663448417147/bRTxyCJq9mgt5p2skQtMAx/gifip-pipeline-dBTKxatiKZ7AMZ7Wi5sYbz.webp";

const materials = ["Carbon Steel", "Stainless Steel 316", "Aluminum 6061", "Copper Alloy", "Cast Iron", "Galvanized Steel"];
const environments = ["Marine Coastal", "Industrial Atmosphere", "Underground Soil", "Freshwater", "Seawater", "Acidic Chemical"];

interface SimParams {
  material: string;
  environment: string;
  temperature: number;
  humidity: number;
  ph: number;
  salinity: number;
  oxygen: number;
  thickness: number;
}

function computeCorrosion(params: SimParams) {
  const { temperature, humidity, ph, salinity, oxygen, thickness } = params;

  const tempFactor = 1 + (temperature - 20) * 0.02;
  const humidFactor = humidity > 80 ? 1.8 : humidity > 60 ? 1.3 : 1.0;
  const phFactor = ph < 4 ? 2.5 : ph < 7 ? 1.5 : ph > 10 ? 1.8 : 1.0;
  const salinityFactor = 1 + salinity * 0.015;
  const oxygenFactor = 1 + oxygen * 0.05;

  const eci = (tempFactor * humidFactor * phFactor * salinityFactor * oxygenFactor).toFixed(2);
  const baseRate = params.material.includes("Stainless") ? 0.01 : params.material.includes("Aluminum") ? 0.008 : 0.05;
  const corrosionRate = (baseRate * parseFloat(eci)).toFixed(4);
  const lifespan = Math.floor(thickness / parseFloat(corrosionRate));
  const riskScore = Math.min(100, Math.floor(parseFloat(eci) * 15));

  let riskLevel: string;
  let riskClass: string;
  if (riskScore < 25) { riskLevel = "Low Risk"; riskClass = "risk-badge-low"; }
  else if (riskScore < 50) { riskLevel = "Moderate Risk"; riskClass = "risk-badge-moderate"; }
  else if (riskScore < 75) { riskLevel = "High Risk"; riskClass = "risk-badge-high"; }
  else { riskLevel = "Critical Risk"; riskClass = "risk-badge-critical"; }

  let corrosionType = "Uniform Corrosion";
  if (salinity > 5 && ph < 7) corrosionType = "Pitting Corrosion";
  else if (salinity > 8) corrosionType = "Galvanic Corrosion";
  else if (ph < 4) corrosionType = "Crevice Corrosion";
  else if (temperature > 60) corrosionType = "Stress Corrosion Cracking";

  let prevention = "Standard Coating System";
  if (riskScore > 75) prevention = "Cathodic Protection + Material Replacement";
  else if (riskScore > 50) prevention = "Cathodic Protection + Inhibitors";
  else if (riskScore > 25) prevention = "Protective Coating + Monitoring";

  return { eci, corrosionRate, lifespan, riskScore, riskLevel, riskClass, corrosionType, prevention };
}

export default function SimulationSection() {
  const [params, setParams] = useState<SimParams>({
    material: "Carbon Steel",
    environment: "Marine Coastal",
    temperature: 25,
    humidity: 75,
    ph: 6.5,
    salinity: 3.5,
    oxygen: 8,
    thickness: 10,
  });

  const [simulated, setSimulated] = useState(false);
  const [running, setRunning] = useState(false);
  const results = computeCorrosion(params);

  const titleRef = useRef(null);
  const titleInView = useInView(titleRef, { once: true });

  const handleSimulate = useCallback(() => {
    setRunning(true);
    setTimeout(() => {
      setRunning(false);
      setSimulated(true);
    }, 1800);
  }, []);

  const SliderInput = ({ label, value, min, max, step, unit, onChange }: {
    label: string; value: number; min: number; max: number; step: number; unit: string;
    onChange: (v: number) => void;
  }) => (
    <div className="space-y-2">
      <div className="flex justify-between items-center">
        <span className="text-xs text-white/50" style={{ fontFamily: "'DM Mono', monospace" }}>{label}</span>
        <span className="text-xs text-teal-400" style={{ fontFamily: "'DM Mono', monospace" }}>
          {value}{unit}
        </span>
      </div>
      <div className="relative h-1 bg-white/10 rounded-full">
        <div
          className="absolute inset-y-0 left-0 bg-teal-400 rounded-full transition-all duration-200"
          style={{ width: `${((value - min) / (max - min)) * 100}%` }}
        />
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={value}
          onChange={(e) => onChange(parseFloat(e.target.value))}
          className="absolute inset-0 w-full opacity-0 cursor-pointer"
          style={{ height: "100%" }}
        />
      </div>
    </div>
  );

  return (
    <section id="simulation" className="relative py-32" style={{ background: "#07070d" }}>
      <div className="container">
        {/* Header */}
        <div ref={titleRef} className="mb-16">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={titleInView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: 0.6 }}
            className="section-number mb-6"
          >
            05 — Simulation
          </motion.div>
          <motion.h2
            initial={{ opacity: 0, y: 30 }}
            animate={titleInView ? { opacity: 1, y: 0 } : {}}
            transition={{ duration: 0.7, delay: 0.1 }}
            className="text-4xl md:text-5xl font-bold text-white leading-tight"
            style={{ fontFamily: "'Space Grotesk', sans-serif", letterSpacing: "-0.03em" }}
          >
            Corrosion{" "}
            <span style={{ color: "#4DFFD2" }}>Simulation</span>
            <br />Dashboard
          </motion.h2>
        </div>

        <div className="flex flex-col xl:flex-row gap-8">
          {/* Left: Parameter inputs */}
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            whileInView={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.7 }}
            viewport={{ once: true }}
            className="xl:w-96 flex-shrink-0 glass-card p-6 space-y-6"
          >
            <div className="section-number">Input Parameters</div>

            {/* Material select */}
            <div className="space-y-2">
              <span className="text-xs text-white/50" style={{ fontFamily: "'DM Mono', monospace" }}>Material Type</span>
              <div className="grid grid-cols-2 gap-1">
                {materials.map((m) => (
                  <button
                    key={m}
                    onClick={() => setParams(p => ({ ...p, material: m }))}
                    className={`px-2 py-1.5 text-xs text-left transition-all duration-200 ${
                      params.material === m
                        ? "border border-teal-400/40 text-teal-400 bg-teal-400/5"
                        : "border border-white/8 text-white/40 hover:text-white/70 hover:border-white/20"
                    }`}
                    style={{ fontFamily: "'DM Mono', monospace" }}
                  >
                    {m}
                  </button>
                ))}
              </div>
            </div>

            {/* Environment select */}
            <div className="space-y-2">
              <span className="text-xs text-white/50" style={{ fontFamily: "'DM Mono', monospace" }}>Environment</span>
              <div className="grid grid-cols-2 gap-1">
                {environments.map((e) => (
                  <button
                    key={e}
                    onClick={() => setParams(p => ({ ...p, environment: e }))}
                    className={`px-2 py-1.5 text-xs text-left transition-all duration-200 ${
                      params.environment === e
                        ? "border border-teal-400/40 text-teal-400 bg-teal-400/5"
                        : "border border-white/8 text-white/40 hover:text-white/70 hover:border-white/20"
                    }`}
                    style={{ fontFamily: "'DM Mono', monospace" }}
                  >
                    {e}
                  </button>
                ))}
              </div>
            </div>

            {/* Sliders */}
            <div className="space-y-4">
              <SliderInput label="Temperature (°C)" value={params.temperature} min={-10} max={80} step={1} unit="°C"
                onChange={(v) => setParams(p => ({ ...p, temperature: v }))} />
              <SliderInput label="Humidity (%)" value={params.humidity} min={10} max={100} step={1} unit="%"
                onChange={(v) => setParams(p => ({ ...p, humidity: v }))} />
              <SliderInput label="pH Level" value={params.ph} min={0} max={14} step={0.1} unit=""
                onChange={(v) => setParams(p => ({ ...p, ph: v }))} />
              <SliderInput label="Salinity (g/L)" value={params.salinity} min={0} max={40} step={0.1} unit="g/L"
                onChange={(v) => setParams(p => ({ ...p, salinity: v }))} />
              <SliderInput label="Oxygen (mg/L)" value={params.oxygen} min={0} max={20} step={0.1} unit="mg/L"
                onChange={(v) => setParams(p => ({ ...p, oxygen: v }))} />
              <SliderInput label="Wall Thickness (mm)" value={params.thickness} min={1} max={50} step={0.5} unit="mm"
                onChange={(v) => setParams(p => ({ ...p, thickness: v }))} />
            </div>

            <button
              onClick={handleSimulate}
              disabled={running}
              className="w-full btn-primary flex items-center justify-center gap-3"
            >
              {running ? (
                <>
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                    className="w-3 h-3 border border-current border-t-transparent rounded-full"
                  />
                  <span>Computing...</span>
                </>
              ) : (
                <span>Run Simulation</span>
              )}
            </button>
          </motion.div>

          {/* Right: Results + visualization */}
          <div className="flex-1 space-y-6">
            {/* Results panel */}
            <motion.div
              initial={{ opacity: 0, x: 30 }}
              whileInView={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.7 }}
              viewport={{ once: true }}
              className="glass-card p-6"
            >
              <div className="flex items-center justify-between mb-6">
                <div className="section-number">Simulation Results</div>
                {simulated && (
                  <div className="flex items-center gap-2">
                    <div className="w-1.5 h-1.5 rounded-full bg-teal-400 pulse-ring" />
                    <span className="text-xs text-teal-400" style={{ fontFamily: "'DM Mono', monospace" }}>Analysis Complete</span>
                  </div>
                )}
              </div>

              {!simulated ? (
                <div className="flex flex-col items-center justify-center py-16 text-center">
                  <div className="text-4xl font-bold text-white/10 mb-4" style={{ fontFamily: "'DM Mono', monospace" }}>—</div>
                  <div className="text-sm text-white/30" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
                    Configure parameters and run simulation to see results
                  </div>
                </div>
              ) : (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ duration: 0.6 }}
                >
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                    {[
                      { label: "Corrosion Rate", val: `${results.corrosionRate}`, unit: "mm/yr" },
                      { label: "Est. Lifespan", val: `${results.lifespan}`, unit: "years" },
                      { label: "Risk Score", val: `${results.riskScore}`, unit: "/ 100" },
                      { label: "ECI Index", val: results.eci, unit: "" },
                    ].map((stat) => (
                      <div key={stat.label} className="border border-white/8 p-4">
                        <div className="text-xs text-white/30 mb-1" style={{ fontFamily: "'DM Mono', monospace" }}>{stat.label}</div>
                        <div className="text-2xl font-bold text-white" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
                          {stat.val}
                          <span className="text-sm text-white/30 ml-1">{stat.unit}</span>
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="border border-white/8 p-4">
                      <div className="text-xs text-white/30 mb-2" style={{ fontFamily: "'DM Mono', monospace" }}>Risk Level</div>
                      <span className={`text-sm px-3 py-1 ${results.riskClass}`}
                        style={{ fontFamily: "'DM Mono', monospace" }}>
                        {results.riskLevel}
                      </span>
                    </div>
                    <div className="border border-white/8 p-4">
                      <div className="text-xs text-white/30 mb-2" style={{ fontFamily: "'DM Mono', monospace" }}>Corrosion Type</div>
                      <div className="text-sm text-white/80" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
                        {results.corrosionType}
                      </div>
                    </div>
                    <div className="border border-white/8 p-4">
                      <div className="text-xs text-white/30 mb-2" style={{ fontFamily: "'DM Mono', monospace" }}>Prevention Strategy</div>
                      <div className="text-sm text-white/80" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
                        {results.prevention}
                      </div>
                    </div>
                  </div>

                  {/* Risk bar */}
                  <div className="mt-6">
                    <div className="flex justify-between items-center mb-2">
                      <span className="text-xs text-white/30" style={{ fontFamily: "'DM Mono', monospace" }}>Structural Integrity</span>
                      <span className="text-xs text-white/50" style={{ fontFamily: "'DM Mono', monospace" }}>
                        {100 - results.riskScore}%
                      </span>
                    </div>
                    <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${100 - results.riskScore}%` }}
                        transition={{ duration: 1.2, ease: "easeOut" }}
                        className="h-full rounded-full"
                        style={{
                          background: results.riskScore > 75 ? "#FF3535" : results.riskScore > 50 ? "#FF6B35" : results.riskScore > 25 ? "#FFD24D" : "#4DFFD2"
                        }}
                      />
                    </div>
                  </div>
                </motion.div>
              )}
            </motion.div>

            {/* Pipeline visualization */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.7 }}
              viewport={{ once: true }}
              className="relative overflow-hidden"
              style={{ height: "260px" }}
            >
              <img
                src={PIPELINE_IMG}
                alt="Pipeline corrosion simulation"
                className="w-full h-full object-cover"
                style={{ filter: "saturate(1.1) brightness(0.7)" }}
              />
              <div className="absolute inset-0" style={{
                background: "linear-gradient(to bottom, transparent 40%, rgba(7,7,13,0.9) 100%)"
              }} />
              <div className="absolute bottom-6 left-6 right-6 flex items-end justify-between">
                <div>
                  <div className="section-number mb-1">Infrastructure Simulation</div>
                  <div className="text-lg font-bold text-white" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
                    Pipeline Corrosion Analysis
                  </div>
                </div>
                <div className="text-xs text-white/40" style={{ fontFamily: "'DM Mono', monospace" }}>
                  {params.material} • {params.environment}
                </div>
              </div>
            </motion.div>
          </div>
        </div>
      </div>
    </section>
  );
}
