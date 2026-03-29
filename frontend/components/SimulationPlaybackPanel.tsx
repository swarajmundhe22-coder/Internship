import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";

import { PredictionTimelinePoint } from "../types/domain";
import { VisualizationPanel } from "./VisualizationPanel";
import { useNumberScramble } from "../hooks/useNumberScramble";

type SimulationPlaybackPanelProps = {
  timeline: PredictionTimelinePoint[];
  loading?: boolean;
};

const PLAYBACK_INTERVAL_MS = 900;

export function SimulationPlaybackPanel({ timeline, loading = false }: SimulationPlaybackPanelProps) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [activeIndex, setActiveIndex] = useState(0);

  const totalSteps = timeline.length;
  const activePoint = totalSteps > 0 ? timeline[activeIndex] : null;

  useEffect(() => {
    if (activeIndex >= totalSteps && totalSteps > 0) {
      setActiveIndex(totalSteps - 1);
    }
  }, [activeIndex, totalSteps]);

  useEffect(() => {
    if (!isPlaying || totalSteps <= 1) {
      return;
    }

    const timer = window.setInterval(() => {
      setActiveIndex((current) => {
        if (current >= totalSteps - 1) {
          setIsPlaying(false);
          return totalSteps - 1;
        }
        return current + 1;
      });
    }, PLAYBACK_INTERVAL_MS);

    return () => window.clearInterval(timer);
  }, [isPlaying, totalSteps]);

  const intensity = useMemo(() => {
    if (!activePoint) {
      return 0;
    }
    return Math.min(100, activePoint.corrosion_rate_mm_per_year * 240);
  }, [activePoint]);

  const statsData = useMemo(() => {
    if (!activePoint) return [];
    return [
      {
        label: "Offset",
        value: activePoint.offset_hours,
        unit: "h",
        colorClass: "text-softwhite",
        borderClass: "border-lagoon/35",
      },
      {
        label: "Risk",
        value: activePoint.risk_classification,
        unit: "",
        colorClass: "animate-hud-pulse uppercase text-neoviolet",
        borderClass: "border-neoviolet/35",
      },
      {
        label: "Risk Score",
        value: activePoint.risk_score.toFixed(1),
        unit: "",
        colorClass: "text-signal",
        borderClass: "border-signal/35",
      },
      {
        label: "Lifespan",
        value: activePoint.estimated_lifespan_years.toFixed(2),
        unit: "y",
        colorClass: "text-softwhite",
        borderClass: "border-softwhite/20",
      },
    ];
  }, [activePoint]);

  return (
    <section className="panel grid gap-4 p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold text-softwhite">Cinematic Playback</h3>
          <p className="text-sm text-softwhite/70">Holographic progression of predictive corrosion and risk state.</p>
        </div>
        <span className="rounded-full border border-lagoon/55 bg-lagoon/10 px-3 py-1 font-hud text-[10px] uppercase tracking-wide text-lagoon">
          {activePoint ? `Step ${activeIndex + 1} / ${totalSteps}` : "No Frames"}
        </span>
      </div>

      {loading && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="flex flex-col items-center justify-center space-y-3 p-6 rounded-lg border border-lagoon/50 shadow-neon bg-slatewash/20"
        >
          <div className="w-full h-1 bg-lagoon/20 relative overflow-hidden rounded">
            <div className="absolute top-0 left-0 h-full w-1/3 bg-lagoon animate-[ping_1.5s_ease-in-out_infinite]" />
          </div>
          <p className="text-lagoon text-xs font-hud tracking-[0.2em] animate-pulse glow-text">
            INITIALIZING PREDICTIVE ENGINE...
          </p>
        </motion.div>
      )}
      {!loading && totalSteps === 0 && (
        <p className="text-sm text-softwhite/75">Generate a project prediction to begin cinematic playback.</p>
      )}

      {totalSteps > 0 && activePoint && (
        <>
          <div className="grid gap-3 md:grid-cols-4">
            {statsData.map((stat, i) => (
              <StatCard key={stat.label} index={i} {...stat} />
            ))}
          </div>

          <div className="relative overflow-hidden rounded-xl border border-lagoon/35 bg-gradient-to-r from-lagoon/10 via-neoviolet/10 to-signal/10 p-3">
            <div className="absolute inset-0 animate-[pulse_3s_ease-in-out_infinite] bg-white/5" />
            <div className="relative flex items-center gap-3">
              <button
                type="button"
                className="holo-btn rounded-md px-4 py-2 text-sm"
                onClick={() => setIsPlaying((value) => !value)}
              >
                {isPlaying ? "Pause" : "Play"}
              </button>
              <button
                type="button"
                className="holo-btn rounded-md px-4 py-2 text-sm"
                onClick={() => {
                  setIsPlaying(false);
                  setActiveIndex(0);
                }}
              >
                Reset
              </button>
              <input
                aria-label="Playback scrub"
                type="range"
                className="w-full accent-lagoon"
                min={0}
                max={Math.max(0, totalSteps - 1)}
                step={1}
                value={activeIndex}
                onChange={(event) => {
                  setIsPlaying(false);
                  setActiveIndex(Number(event.target.value));
                }}
              />
            </div>
          </div>

          <VisualizationPanel intensity={intensity} />

          <div className="grid grid-cols-6 gap-2 md:grid-cols-12">
            {timeline.map((point, index) => (
              <span
                key={`${point.offset_hours}-${index}`}
                className={`h-2 rounded-full transition-all duration-300 ${
                  index <= activeIndex ? "animate-hud-pulse bg-lagoon shadow-neon" : "bg-softwhite/20"
                }`}
                title={`${point.offset_hours}h | ${point.risk_classification}`}
              />
            ))}
          </div>
        </>
      )}
    </section>
  );
}

function StatCard({ 
  label, 
  value, 
  unit, 
  colorClass, 
  borderClass, 
  index 
}: { 
  label: string; 
  value: string | number; 
  unit: string; 
  colorClass: string; 
  borderClass: string; 
  index: number; 
}) {
  const scrambledValue = useNumberScramble(value);

  return (
    <motion.article
      className={`rounded-lg border ${borderClass} bg-slatewash/40 p-3`}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1, duration: 0.4 }}
    >
      <p className="hud-label text-[10px] text-softwhite/70">{label}</p>
      <p className={`text-lg font-semibold ${colorClass}`}>
        {scrambledValue}{unit ? ` ${unit}` : ""}
      </p>
    </motion.article>
  );
}
