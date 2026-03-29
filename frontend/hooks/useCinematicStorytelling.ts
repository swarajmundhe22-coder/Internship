import { useEffect } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/dist/ScrollTrigger";

function parseNumber(value: string | undefined, fallback: number): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

export function useCinematicStorytelling(pathname: string, enabled = true): void {
  useEffect(() => {
    if (!enabled) {
      return;
    }

    if (typeof window === "undefined" || typeof window.matchMedia !== "function") {
      return;
    }

    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      return;
    }

    const routeEnabled =
      pathname === "/" ||
      pathname === "/dashboard" ||
      pathname === "/simulations" ||
      pathname === "/reports" ||
      pathname === "/expertise" ||
      pathname === "/credibility";
    if (!routeEnabled) {
      return;
    }

    gsap.registerPlugin(ScrollTrigger);

    const storyTracks = gsap.utils.toArray<HTMLElement>("[data-story-track='true']");
    if (storyTracks.length === 0) {
      return;
    }

    const compact = window.matchMedia("(max-width: 1024px)").matches;
    const triggers: ScrollTrigger[] = [];
    const animations: gsap.core.Animation[] = [];

    storyTracks.forEach((track) => {
      const trackCurve = track.dataset.storyCurve ?? "balanced";
      const trackProgressStart = track.dataset.storyProgressStart ?? "top 84%";
      const trackProgressEnd = track.dataset.storyProgressEnd ?? "bottom 16%";
      const trackProgressScrub = parseNumber(track.dataset.storyProgressScrub, 0.8);
      const compactRevealStart = track.dataset.storyCompactStart ?? "top 82%";
      const compactBeatStart = track.dataset.storyCompactBeatStart ?? "top 72%";

      const chapterStart = track.dataset.storyStart ?? (trackCurve === "snappy" ? "top 90%" : "top 86%");
      const chapterEnd = track.dataset.storyEnd ?? (trackCurve === "snappy" ? "top 48%" : "top 42%");
      const chapterScrub = parseNumber(track.dataset.storyScrub, trackCurve === "snappy" ? 0.42 : 0.55);
      const chapterEase = track.dataset.storyEase ?? (trackCurve === "cinematic" ? "power4.out" : "power2.out");

      const pinTarget = track.querySelector<HTMLElement>("[data-story-pin='true']");
      const chapters = Array.from(track.querySelectorAll<HTMLElement>("[data-story-panel='true'], [data-story-chapter='true']"));
      const beats = Array.from(track.querySelectorAll<HTMLElement>("[data-story-step='true'], [data-cutscene-beat='true']"));

      gsap.set(track, { "--story-progress": 0 });
      const progressTween = gsap.to(track, {
        "--story-progress": 1,
        ease: "none",
        scrollTrigger: {
          trigger: track,
          start: trackProgressStart,
          end: trackProgressEnd,
          scrub: trackProgressScrub
        }
      });
      animations.push(progressTween);
      if (progressTween.scrollTrigger) {
        triggers.push(progressTween.scrollTrigger);
      }

      if (chapters.length === 0) {
        return;
      }

      if (compact) {
        const reveal = gsap.fromTo(
          chapters,
          { autoAlpha: 0, y: 20 },
          {
            autoAlpha: 1,
            y: 0,
            duration: 0.65,
            stagger: 0.1,
            ease: chapterEase,
            scrollTrigger: {
              trigger: track,
              start: compactRevealStart,
              once: true
            }
          }
        );
        animations.push(reveal);
        if (reveal.scrollTrigger) {
          triggers.push(reveal.scrollTrigger);
        }

        if (beats.length > 0) {
          const beatReveal = gsap.fromTo(
            beats,
            { autoAlpha: 0, y: 12 },
            {
              autoAlpha: 1,
              y: 0,
              duration: 0.5,
              stagger: 0.08,
              ease: "power2.out",
              scrollTrigger: {
                trigger: track,
                start: compactBeatStart,
                once: true
              }
            }
          );
          animations.push(beatReveal);
          if (beatReveal.scrollTrigger) {
            triggers.push(beatReveal.scrollTrigger);
          }
        }

        return;
      }

      if (pinTarget && chapters.length > 1) {
        const pinLength = Math.max((chapters.length - 1) * (window.innerHeight * 0.74), window.innerHeight * 0.7);
        const pinTrigger = ScrollTrigger.create({
          trigger: track,
          start: "top top+=80",
          end: `+=${pinLength}`,
          pin: pinTarget,
          pinSpacing: false,
          scrub: 0.7,
          invalidateOnRefresh: true
        });
        triggers.push(pinTrigger);
      }

      chapters.forEach((chapter, index) => {
        const panelEase = chapter.dataset.storyEase ?? chapterEase;
        const panelStart = chapter.dataset.storyStart ?? chapterStart;
        const panelEnd = chapter.dataset.storyEnd ?? chapterEnd;
        const panelScrub = parseNumber(chapter.dataset.storyScrub, chapterScrub);
        const panelOffset = parseNumber(chapter.dataset.storyOffset, index === 0 ? 0 : 28);
        const panelScale = parseNumber(chapter.dataset.storyScale, index === 0 ? 1 : 0.985);

        const chapterBeat = gsap.timeline({
          scrollTrigger: {
            trigger: chapter,
            start: panelStart,
            end: panelEnd,
            scrub: panelScrub,
            invalidateOnRefresh: true
          }
        });

        chapterBeat.fromTo(
          chapter,
          { autoAlpha: index === 0 ? 1 : 0.18, y: index === 0 ? 0 : panelOffset, scale: panelScale },
          { autoAlpha: 1, y: 0, scale: 1, duration: 0.7, ease: panelEase }
        );

        if (index < chapters.length - 1) {
          chapterBeat.to(chapter, { autoAlpha: 0.32, y: -16, duration: 0.45, ease: "power1.inOut" }, 0.72);
        }

        animations.push(chapterBeat);
        if (chapterBeat.scrollTrigger) {
          triggers.push(chapterBeat.scrollTrigger);
        }
      });

      if (beats.length > 0) {
        const stagger = gsap.fromTo(
          beats,
          { autoAlpha: 0, y: 16 },
          {
            autoAlpha: 1,
            y: 0,
            duration: 0.7,
            stagger: 0.1,
            ease: "power3.out",
            scrollTrigger: {
              trigger: track,
              start: "top 68%",
              once: true
            }
          }
        );
        animations.push(stagger);
        if (stagger.scrollTrigger) {
          triggers.push(stagger.scrollTrigger);
        }
      }
    });

    return () => {
      triggers.forEach((trigger) => trigger.kill());
      animations.forEach((animation) => animation.kill());
    };
  }, [enabled, pathname]);
}
