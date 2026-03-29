import type { AppProps } from "next/app";
import { AnimatePresence, motion } from "framer-motion";
import { useRouter } from "next/router";
import { useEffect, useState } from "react";

import { CinematicQualityControl } from "../components/CinematicQualityControl";
import { CinematicWebGLBackdrop } from "../components/CinematicWebGLBackdrop";
import { CinematicQualityProvider } from "../contexts/CinematicQualityContext";
import { useCinematicScrollChoreography } from "../hooks/useCinematicScrollChoreography";
import { useCinematicStorytelling } from "../hooks/useCinematicStorytelling";
import { useRouteCinematicTimeline } from "../hooks/useRouteCinematicTimeline";
import { onLookersBrandDirection } from "../utils/brandDirection";
import { getRoutePage, getRouteTone } from "../utils/cinematicRoute";
import "../styles/globals.css";
import "../styles/outsource.css";
import "../styles/local-simulated.css";
import "mapbox-gl/dist/mapbox-gl.css";

type NavigatorConnection = Navigator & {
  connection?: {
    saveData?: boolean;
  };
};

function resolveFastInteractionMode(): boolean {
  const isDevelopment = process.env.NODE_ENV !== "production";
  if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
    return isDevelopment;
  }

  try {
    const storedMode = window.localStorage.getItem("onlooker_ui_mode");
    if (storedMode === "cinematic") {
      return false;
    }
    if (storedMode === "fast") {
      return true;
    }
  } catch {
    // Ignore storage access issues and fall through to device heuristics.
  }

  const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const lowCpu = typeof navigator.hardwareConcurrency === "number" && navigator.hardwareConcurrency <= 8;
  const saveData = Boolean((navigator as NavigatorConnection).connection?.saveData);
  return isDevelopment || prefersReducedMotion || lowCpu || saveData;
}

export default function App({ Component, pageProps }: AppProps) {
  const router = useRouter();
  const [fastInteractionMode, setFastInteractionMode] = useState<boolean>(process.env.NODE_ENV !== "production");

  useEffect(() => {
    setFastInteractionMode(resolveFastInteractionMode());
  }, []);

  const isOutsourceHome = router.pathname === "/";
  const isAuthRoute = router.pathname.startsWith("/auth");
  const shouldDisableCinematicBackdrop = isOutsourceHome || isAuthRoute || fastInteractionMode;
  const routeTone = getRouteTone(router.pathname);
  const routePage = getRoutePage(router.pathname);
  const timingProfile = onLookersBrandDirection.timingByPage[routePage] ?? onLookersBrandDirection.timingByPage.default;
  const transitionVariant = onLookersBrandDirection.transitionVariant;
  const transitionDuration = fastInteractionMode ? 0.14 : timingProfile.transitionDuration;

  useRouteCinematicTimeline(routeTone, routePage, router.asPath, !fastInteractionMode);
  useCinematicScrollChoreography(router.asPath, !fastInteractionMode);
  useCinematicStorytelling(router.pathname, !fastInteractionMode);

  return (
    <CinematicQualityProvider>
      {!shouldDisableCinematicBackdrop && <CinematicWebGLBackdrop tone={routeTone} />}
      {!shouldDisableCinematicBackdrop && <CinematicQualityControl />}
      <AnimatePresence mode={fastInteractionMode ? "sync" : "wait"} initial={false}>
        <motion.div
          key={router.asPath}
          className="route-transition-shell"
          data-brand-transition={transitionVariant}
          initial={fastInteractionMode ? { opacity: 0.96 } : { opacity: 0, y: 12, filter: "blur(8px) saturate(0.9)" }}
          animate={fastInteractionMode ? { opacity: 1 } : { opacity: 1, y: 0, filter: "blur(0px) saturate(1)" }}
          exit={fastInteractionMode ? { opacity: 0.98 } : { opacity: 0, y: -10, filter: "blur(6px) saturate(1.08)" }}
          transition={{ duration: transitionDuration, ease: fastInteractionMode ? "linear" : [0.14, 0.86, 0.24, 1] }}
        >
          {!fastInteractionMode && (
            <motion.div
              className="route-transition-veil"
              initial={{ opacity: 0.9, scaleY: 1, transformOrigin: "50% 0%" }}
              animate={{ opacity: 0, scaleY: 1.1 }}
              exit={{ opacity: 0.74, scaleY: 1.02, transformOrigin: "50% 100%" }}
              transition={{ duration: timingProfile.transitionDuration + 0.06, ease: [0.12, 0.86, 0.22, 1] }}
            />
          )}
          {!fastInteractionMode && (
            <motion.div
              className="route-transition-grid"
              initial={{ opacity: 0.38, x: 0 }}
              animate={{ opacity: 0, x: -24 }}
              exit={{ opacity: 0.34, x: 28 }}
              transition={{ duration: timingProfile.transitionDuration + 0.08, ease: [0.14, 0.9, 0.22, 1] }}
            />
          )}
          {!fastInteractionMode && (
            <motion.div
              className="route-transition-streak"
              initial={{ opacity: 0.58, x: "-22%" }}
              animate={{ opacity: 0, x: "26%" }}
              exit={{ opacity: 0.42, x: "-14%" }}
              transition={{ duration: timingProfile.transitionDuration + 0.12, ease: [0.16, 1, 0.28, 1] }}
            />
          )}
          <Component {...pageProps} />
        </motion.div>
      </AnimatePresence>
    </CinematicQualityProvider>
  );
}
