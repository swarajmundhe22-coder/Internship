import { useEffect } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/dist/ScrollTrigger";

import { onLookersBrandDirection } from "../utils/brandDirection";
import { getRoutePage } from "../utils/cinematicRoute";

export function useCinematicScrollChoreography(routeKey: string): void {
  useEffect(() => {
    if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
      return;
    }

    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      return;
    }

    gsap.registerPlugin(ScrollTrigger);
    const compact = window.matchMedia("(max-width: 900px)").matches;
    const routePage = getRoutePage(window.location.pathname);
    const timing = onLookersBrandDirection.timingByPage[routePage] ?? onLookersBrandDirection.timingByPage.default;
    const intensity = onLookersBrandDirection.intensity;
    const parallaxMultiplier = Math.max(0.6, intensity.parallaxIntensity / 5);
    const pulseGlow = 12 + intensity.glowIntensity;
    const pulseLift = Math.max(1, intensity.uiPulseIntensity / 4);

    const sections = gsap.utils.toArray<HTMLElement>(
      ".cinematic-stage, .panel, [data-cinematic-reveal='true'], .landing-tile, .telemetry-card, .module-pill"
    );
    const triggers: ScrollTrigger[] = [];
    const animations: gsap.core.Tween[] = [];

    const root = document.documentElement;
    gsap.set(root, { "--scroll-progress": 0 });

    const progressTween = gsap.to(root, {
      "--scroll-progress": 1,
      ease: "none",
      scrollTrigger: {
        trigger: document.documentElement,
        start: "top top",
        end: "bottom bottom",
        scrub: true
      }
    });
    animations.push(progressTween);
    if (progressTween.scrollTrigger) {
      triggers.push(progressTween.scrollTrigger);
    }

    sections.forEach((section, index) => {
      const tween = gsap.fromTo(
        section,
        { opacity: 0, y: 42, rotateX: 6, scale: 0.985 },
        {
          opacity: 1,
          y: 0,
          rotateX: 0,
          scale: 1,
          duration: timing.panelRevealDuration,
          ease: timing.panelRevealEase,
          delay: Math.min(index * 0.04, 0.22),
          scrollTrigger: {
            trigger: section,
            start: compact ? "top 92%" : "top 86%",
            end: compact ? "top 50%" : "top 35%",
            scrub: false,
            once: true
          }
        }
      );
      animations.push(tween);

      if (tween.scrollTrigger) {
        triggers.push(tween.scrollTrigger);
      }
    });

    const parallaxNodes = gsap.utils.toArray<HTMLElement>("[data-scroll-parallax]");
    parallaxNodes.forEach((node) => {
      const speedBase = node.dataset.scrollParallax === "fast" ? 22 : node.dataset.scrollParallax === "medium" ? 15 : 10;
      const speed = speedBase * parallaxMultiplier;
      const tween = gsap.to(node, {
        yPercent: speed,
        ease: "none",
        scrollTrigger: {
          trigger: node.closest("section,article,main") ?? node,
          start: "top bottom",
          end: "bottom top",
          scrub: 1.2
        }
      });
      animations.push(tween);
      if (tween.scrollTrigger) {
        triggers.push(tween.scrollTrigger);
      }
    });

    const parallaxTween = gsap.to(".cinematic-stars", {
      yPercent: 12 * parallaxMultiplier,
      xPercent: -6 * parallaxMultiplier,
      ease: "none",
      scrollTrigger: {
        trigger: document.documentElement,
        start: "top top",
        end: "bottom bottom",
        scrub: compact ? 0.8 : 1.5
      }
    });


    const chipPulse = gsap.fromTo(
      ".scene-chip, .module-pill-active",
      { boxShadow: "0 0 0 rgba(0,0,0,0)", y: 0 },
      {
        boxShadow: `0 0 ${pulseGlow}px color-mix(in srgb, var(--route-accent) 55%, transparent)`,
        y: -pulseLift,
        duration: timing.chipPulseDuration,
        repeat: -1,
        yoyo: true,
        ease: "sine.inOut",
        stagger: 0.18
      }
    );
    animations.push(chipPulse);
    if (parallaxTween.scrollTrigger) {
      triggers.push(parallaxTween.scrollTrigger);
    }
    animations.push(parallaxTween);

    return () => {
      triggers.forEach((trigger) => trigger.kill());
      animations.forEach((animation) => animation.kill());
    };
  }, [routeKey]);
}
