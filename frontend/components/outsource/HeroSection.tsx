/* ============================================================
   HeroSection — Full-viewport immersive hero
   WebGL particle field + cinematic typography + scroll indicator
   Bioluminescent Deep Ocean aesthetic
   ============================================================ */
import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import ParticleCanvas from "./ParticleCanvas";

const HERO_IMAGE = "https://d2xsxph8kpxj0f.cloudfront.net/310519663448417147/bRTxyCJq9mgt5p2skQtMAx/gifip-hero-bg-A6fYWkbGeyrzV2VMo2dA8h.webp";

const tagLine = "PREDICT • PREVENT • PROTECT";

export default function HeroSection() {
  const [loaded, setLoaded] = useState(false);
  const [counter, setCounter] = useState(0);
  const counterRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    // Loading counter animation
    counterRef.current = setInterval(() => {
      setCounter((prev) => {
        if (prev >= 100) {
          if (counterRef.current) clearInterval(counterRef.current);
          setLoaded(true);
          return 100;
        }
        return prev + Math.floor(Math.random() * 4) + 1;
      });
    }, 25);
    return () => { if (counterRef.current) clearInterval(counterRef.current); };
  }, []);

  const wordVariants = {
    hidden: { y: 80, opacity: 0 },
    visible: (i: number) => ({
      y: 0,
      opacity: 1,
      transition: {
        type: "tween" as const,
        duration: 0.9,
        delay: 0.8 + i * 0.12,
      },
    }),
  };

  const headlineWords = ["Global", "Infrastructure", "Failure", "Intelligence"];

  return (
    <section
      id="hero"
      className="relative w-full min-h-screen flex flex-col overflow-hidden"
      style={{ background: "#050508" }}
    >
      {/* Background hero image with overlay */}
      <div className="absolute inset-0 z-0">
        <img
          src={HERO_IMAGE}
          alt="Molecular corrosion visualization"
          className="w-full h-full object-cover opacity-25"
          style={{ filter: "saturate(1.2) brightness(0.6)" }}
        />
        <div className="absolute inset-0" style={{
          background: "radial-gradient(ellipse 80% 60% at 50% 50%, rgba(77,255,210,0.04) 0%, transparent 70%), linear-gradient(to bottom, rgba(5,5,8,0.3) 0%, rgba(5,5,8,0.7) 60%, #050508 100%)"
        }} />
      </div>

      {/* WebGL Particle Canvas */}
      <div className="absolute inset-0 z-10">
        <ParticleCanvas className="w-full h-full" />
      </div>

      {/* Loading counter overlay */}
      {!loaded && (
        <motion.div
          className="absolute inset-0 z-50 flex flex-col items-center justify-center"
          style={{ background: "#050508" }}
          animate={{ opacity: counter >= 100 ? 0 : 1 }}
          transition={{ duration: 0.6, delay: 0.2 }}
        >
          <div className="section-number mb-4">Initializing Platform</div>
          <div className="text-7xl font-bold text-white" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
            {counter.toString().padStart(3, "0")}
          </div>
          <div className="mt-4 w-48 h-px bg-white/10 relative overflow-hidden">
            <motion.div
              className="absolute inset-y-0 left-0 bg-teal-400"
              style={{ width: `${counter}%` }}
            />
          </div>
        </motion.div>
      )}

      {/* Main content */}
      <div className="relative z-20 flex flex-col justify-between min-h-screen px-6 md:px-10 pt-28 pb-12">
        {/* Top tags strip */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: loaded ? 1 : 0, y: loaded ? 0 : -20 }}
          transition={{ duration: 0.6, delay: 0.5 }}
          className="flex items-center gap-3 flex-wrap"
        >
          {["CORROSION PREDICTION", "MATERIAL SCIENCE", "INFRASTRUCTURE AI", "3D SIMULATION"].map((tag) => (
            <span key={tag} className="horizontal-tag">{tag}</span>
          ))}
        </motion.div>

        {/* Hero headline */}
        <div className="flex-1 flex flex-col justify-center max-w-5xl">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: loaded ? 1 : 0 }}
            transition={{ duration: 0.4, delay: 0.6 }}
            className="section-number mb-6"
          >
            01 — The On Lookers
          </motion.div>

          <div className="overflow-hidden">
            <div className="flex flex-wrap gap-x-4 gap-y-0">
              {headlineWords.map((word, i) => (
                <motion.span
                  key={word}
                  custom={i}
                  variants={wordVariants}
                  initial="hidden"
                  animate={loaded ? "visible" : "hidden"}
                  className="text-6xl md:text-8xl lg:text-9xl font-bold leading-none text-white"
                  style={{ fontFamily: "'Space Grotesk', sans-serif", letterSpacing: "-0.03em" }}
                >
                  {word}
                </motion.span>
              ))}
            </div>
          </div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: loaded ? 1 : 0, y: loaded ? 0 : 20 }}
            transition={{ duration: 0.8, delay: 1.4 }}
            className="mt-6"
          >
            <span
              className="text-5xl md:text-7xl lg:text-8xl font-bold"
              style={{
                fontFamily: "'Space Grotesk', sans-serif",
                letterSpacing: "-0.03em",
                color: "#4DFFD2",
              }}
            >
              Lookers
            </span>
          </motion.div>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: loaded ? 1 : 0, y: loaded ? 0 : 20 }}
            transition={{ duration: 0.8, delay: 1.6 }}
            className="mt-8 text-base md:text-lg text-white/50 max-w-xl leading-relaxed"
            style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 300 }}
          >
            The On Lookers — Advanced infrastructure monitoring and corrosion prediction platform.
            Analyze environmental conditions, chemical reactions, and material properties to
            anticipate degradation before physical failure occurs.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: loaded ? 1 : 0, y: loaded ? 0 : 20 }}
            transition={{ duration: 0.8, delay: 1.8 }}
            className="mt-10 flex items-center gap-4"
          >
            <a href="#simulation" className="btn-primary">
              Run Simulation
            </a>
            <a href="#platform" className="btn-outline flex items-center gap-2">
              <span>Explore Platform</span>
              <span className="text-teal-400">↓</span>
            </a>
          </motion.div>
        </div>

        {/* Bottom stats bar */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: loaded ? 1 : 0, y: loaded ? 0 : 30 }}
          transition={{ duration: 0.8, delay: 2.0 }}
          className="flex flex-col sm:flex-row items-start sm:items-end justify-between gap-6"
        >
          <div className="flex items-center gap-8">
            {[
              { val: "100+", label: "Platform Features" },
              { val: "9", label: "Industries Served" },
              { val: "4", label: "Roadmap Phases" },
            ].map((stat) => (
              <div key={stat.label}>
                <div className="text-2xl font-bold text-white" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
                  {stat.val}
                </div>
                <div className="text-xs text-white/30 mt-0.5" style={{ fontFamily: "'DM Mono', monospace" }}>
                  {stat.label}
                </div>
              </div>
            ))}
          </div>

          <div className="flex items-center gap-3">
            <div className="w-px h-12 bg-white/10" />
            <div className="flex flex-col gap-1">
              <span className="section-number">Scroll to explore</span>
              <div className="flex items-center gap-2">
                <motion.div
                  animate={{ y: [0, 6, 0] }}
                  transition={{ duration: 1.5, repeat: Infinity, ease: "easeInOut" }}
                  className="w-4 h-6 border border-white/20 rounded-full flex items-start justify-center pt-1"
                >
                  <div className="w-0.5 h-1.5 bg-teal-400 rounded-full" />
                </motion.div>
              </div>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Horizontal scrolling tag strip */}
      <div className="relative z-20 border-t border-white/5 overflow-hidden py-3">
        <motion.div
          animate={{ x: [0, -800] }}
          transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
          className="flex items-center gap-6 whitespace-nowrap"
          style={{ width: "max-content" }}
        >
          {Array(4).fill(tagLine.split(" • ")).flat().map((tag, i) => (
            <span key={i} className="section-number px-4">
              {i % 3 === 1 ? <span className="text-teal-400">•</span> : null}
              {" "}{tag}{" "}
            </span>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
