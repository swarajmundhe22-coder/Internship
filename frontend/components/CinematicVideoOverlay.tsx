import React, { useRef, useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Play, Volume2, ShieldAlert } from "lucide-react";

type VideoOverlayProps = {
  src: string;
  triggeredByConfidence?: number;
  threshold?: number;
  label?: string;
};

/**
 * Full-screen 4K/8K hyper-realistic video overlay for The On Looker.
 * Features HDR bloom, volumetric lighting simulations, and film-grade grading.
 * Triggered dynamically based on predictive model confidence.
 */
export function CinematicVideoOverlay({
  src,
  triggeredByConfidence = 1.0,
  threshold = 0.9,
  label = "SYSTEM ALERT: LOW CONFIDENCE"
}: VideoOverlayProps) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isActive, setIsActive] = useState(false);

  useEffect(() => {
    let playPromise: Promise<void> | undefined;
    
    if (triggeredByConfidence < threshold) {
      setIsActive(true);
      if (videoRef.current) {
        // High-performance play with restriction handling
        playPromise = videoRef.current.play();
        playPromise?.catch((err) => {
          console.warn("Cinematic overlay play restricted:", err.message);
        });
      }
    } else {
      setIsActive(false);
      if (videoRef.current) {
        videoRef.current.pause();
      }
    }

    return () => {
      if (playPromise) {
        playPromise.then(() => {
          videoRef.current?.pause();
        }).catch(() => {});
      }
    };
  }, [triggeredByConfidence, threshold]);

  return (
    <AnimatePresence>
      {isActive && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 pointer-events-none overflow-hidden"
        >
          {/* 4K/8K Video Layer with preloading and hardware acceleration */}
          <video
            ref={videoRef}
            src={src}
            muted
            loop
            playsInline
            preload="auto"
            className="w-full h-full object-cover scale-105 contrast-125 brightness-75 saturate-150 will-change-transform"
          />

          {/* HDR Bloom & Color Grading Overlays */}
          <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-black/60 mix-blend-multiply" />
          <div className="absolute inset-0 bg-cyan-500/10 mix-blend-overlay animate-pulse" />
          
          {/* Volumetric Lighting simulation */}
          <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(0,229,255,0.15),transparent_70%)]" />

          {/* HUD Overlay for Confidence Alerts */}
          <div className="absolute bottom-12 left-12 right-12 flex justify-between items-end pointer-events-auto">
            <div className="space-y-2">
              <div className="flex items-center gap-3 text-red-500">
                <ShieldAlert className="w-6 h-6 animate-ping" />
                <span className="text-xs font-display font-bold uppercase tracking-[0.4em]">{label}</span>
              </div>
              <div className="text-4xl font-display font-black text-white uppercase tracking-tighter">
                Confidence Level: {(triggeredByConfidence * 100).toFixed(1)}%
              </div>
            </div>
            
            <div className="flex gap-4">
              <div className="p-4 border border-white/20 backdrop-blur-md bg-black/40">
                <Volume2 className="w-5 h-5 text-white/60" />
              </div>
              <div className="px-8 py-4 bg-red-600 text-white font-display font-black uppercase tracking-widest text-xs">
                Manual Override Required
              </div>
            </div>
          </div>

          {/* Film Grain & Scanlines */}
          <div className="absolute inset-0 opacity-[0.03] pointer-events-none bg-[url('https://grainy-gradients.vercel.app/noise.svg')]" />
        </motion.div>
      )}
    </AnimatePresence>
  );
}
