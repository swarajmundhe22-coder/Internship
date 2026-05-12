import type { AppProps } from "next/app";
import { AnimatePresence, motion } from "framer-motion";
import { useRouter } from "next/router";
import { ReactLenis } from 'lenis/react';

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

export default function App({ Component, pageProps }: AppProps) {
  const router = useRouter();
  const isOutsourceHome = router.pathname === "/";
  const isAuthRoute = router.pathname.startsWith("/auth");
  const shouldDisableCinematicBackdrop = isOutsourceHome || isAuthRoute;
  const routeTone = getRouteTone(router.pathname);
  const routePage = getRoutePage(router.pathname);
  const timingProfile = onLookersBrandDirection.timingByPage[routePage] ?? onLookersBrandDirection.timingByPage.default;
  const transitionVariant = onLookersBrandDirection.transitionVariant;

  useRouteCinematicTimeline(routeTone, routePage, router.asPath);
  useCinematicScrollChoreography(router.asPath);
  useCinematicStorytelling(router.pathname);

  return (
    <CinematicQualityProvider>
      <ReactLenis root>
        {!shouldDisableCinematicBackdrop && <CinematicWebGLBackdrop tone={routeTone} />}
        {!shouldDisableCinematicBackdrop && <CinematicQualityControl />}
        <AnimatePresence mode="wait" initial={false}>
          <motion.div
            key={router.asPath}
            className="route-transition-shell"
            data-brand-transition={transitionVariant}
            initial={{ opacity: 0, y: 12, filter: "blur(8px) saturate(0.9)" }}
            animate={{ opacity: 1, y: 0, filter: "blur(0px) saturate(1)" }}
            exit={{ opacity: 0, y: -10, filter: "blur(6px) saturate(1.08)" }}
            transition={{ duration: timingProfile.transitionDuration, ease: [0.14, 0.86, 0.24, 1] }}
          >
            <motion.div
              className="route-transition-veil"
              initial={{ opacity: 0.9, scaleY: 1, transformOrigin: "50% 0%" }}
              animate={{ opacity: 0, scaleY: 1.1 }}
              exit={{ opacity: 0.74, scaleY: 1.02, transformOrigin: "50% 100%" }}
              transition={{ duration: timingProfile.transitionDuration + 0.06, ease: [0.12, 0.86, 0.22, 1] }}
            />
            <motion.div
              className="route-transition-grid"
              initial={{ opacity: 0.38, x: 0 }}
              animate={{ opacity: 0, x: -24 }}
              exit={{ opacity: 0.34, x: 28 }}
              transition={{ duration: timingProfile.transitionDuration + 0.08, ease: [0.14, 0.9, 0.22, 1] }}
            />
            <motion.div
              className="route-transition-streak"
              initial={{ opacity: 0.58, x: "-22%" }}
              animate={{ opacity: 0, x: "26%" }}
              exit={{ opacity: 0.42, x: "-14%" }}
              transition={{ duration: timingProfile.transitionDuration + 0.12, ease: [0.16, 1, 0.28, 1] }}
            />
            <Component {...pageProps} />
          </motion.div>
        </AnimatePresence>
      </ReactLenis>
    </CinematicQualityProvider>
  );
}
