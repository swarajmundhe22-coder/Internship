import { ReactNode } from "react";
import { motion } from "framer-motion";

type SceneTone = "opening" | "mission" | "battle" | "briefing" | "world" | "finale";

type CinematicSceneProps = {
  tone: SceneTone;
  sceneLabel: string;
  narrative: string;
  children?: ReactNode;
};

export function CinematicScene({ tone, sceneLabel, narrative, children }: CinematicSceneProps) {
  return (
    <motion.section
      className={`cinematic-stage cinematic-tone-${tone} relative overflow-hidden rounded-2xl border border-lagoon/25 p-5 md:p-6`}
      data-cinematic-reveal="true"
      initial={{ opacity: 0, y: 26, scale: 0.985 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
    >
      <div className="cinematic-stars" />
      <div className="cinematic-nebula" />
      <div className="cinematic-scanlines" />
      <div className="cinematic-vignette" />
      <div className="cinematic-grain" />

      <motion.div className="relative z-10 flex flex-wrap items-start justify-between gap-3" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ delay: 0.08, duration: 0.45 }}>
        <p className="scene-chip">{sceneLabel}</p>
        <p className="max-w-2xl text-right text-xs text-softwhite/80 md:text-sm">{narrative}</p>
      </motion.div>

      {children && <div className="relative z-10 mt-4">{children}</div>}
    </motion.section>
  );
}
