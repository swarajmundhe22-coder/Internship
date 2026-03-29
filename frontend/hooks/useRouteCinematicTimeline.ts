import { useEffect } from "react";
import gsap from "gsap";

import { onLookersBrandDirection } from "../utils/brandDirection";
import { CinematicRoutePage, CinematicRouteTone } from "../utils/cinematicRoute";

const toneAccent: Record<CinematicRouteTone, string> = {
  opening: "#00e5ff",
  mission: "#5fd3ff",
  battle: "#ff9f43",
  briefing: "#a584ff",
  world: "#44ffe1",
  finale: "#ffd071"
};

export function useRouteCinematicTimeline(
  tone: CinematicRouteTone,
  routePage: CinematicRoutePage,
  routeKey: string,
  enabled = true
): void {
  useEffect(() => {
    if (!enabled) {
      return;
    }

    if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
      return;
    }

    const timing = onLookersBrandDirection.timingByPage[routePage] ?? onLookersBrandDirection.timingByPage.default;

    const context = gsap.context(() => {
      document.documentElement.dataset.routeTone = tone;
      document.documentElement.dataset.routePage = routePage;
      document.documentElement.dataset.brandTransition = onLookersBrandDirection.transitionVariant;

      const timeline = gsap.timeline({ defaults: { ease: timing.panelRevealEase } });
      timeline
        .fromTo(".scene-chip", { y: 12, autoAlpha: 0 }, { y: 0, autoAlpha: 1, duration: timing.panelRevealDuration * 0.66, stagger: 0.03 }, 0)
        .fromTo(".hud-label", { autoAlpha: 0.62 }, { autoAlpha: 1, duration: timing.panelRevealDuration * 0.76, stagger: 0.018 }, 0.06)
        .fromTo(".panel", { autoAlpha: 0, y: 14 }, { autoAlpha: 1, y: 0, duration: timing.panelRevealDuration, stagger: 0.024 }, 0.03)
        .fromTo(
          ".scene-chip",
          { boxShadow: "0 0 0 rgba(0, 0, 0, 0)", borderColor: "rgba(0,229,255,0.2)" },
          {
            boxShadow: `0 0 24px ${toneAccent[tone]}66`,
            borderColor: toneAccent[tone],
            duration: timing.panelRevealDuration * 0.74,
            yoyo: true,
            repeat: 1
          },
          0.12
        );

      const eventTimeline = gsap.timeline({ repeat: -1, repeatDelay: 2.8 });
      eventTimeline
        .to(".quality-console", { boxShadow: `0 0 0 1px ${toneAccent[tone]}66, 0 0 22px ${toneAccent[tone]}44`, duration: timing.chipPulseDuration * 0.56 })
        .to(".quality-console", { boxShadow: "0 0 0 1px rgba(0,229,255,0.2), 0 0 0 rgba(0,0,0,0)", duration: timing.chipPulseDuration * 0.56 });
    });

    return () => {
      context.revert();
    };
  }, [enabled, tone, routePage, routeKey]);
}
