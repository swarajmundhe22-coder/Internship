import { createContext, ReactNode, useContext, useEffect, useMemo, useState } from "react";

export type CinematicQuality = "high" | "medium" | "low";

type QualityConfig = {
  pixelRatioMax: number;
  bloomBase: number;
  bloomBoost: number;
  starCount: number;
  filmIntensity: number;
};

const qualityConfig: Record<CinematicQuality, QualityConfig> = {
  high: {
    pixelRatioMax: 2,
    bloomBase: 1,
    bloomBoost: 1.35,
    starCount: 1900,
    filmIntensity: 0.28
  },
  medium: {
    pixelRatioMax: 1.45,
    bloomBase: 0.82,
    bloomBoost: 0.95,
    starCount: 1300,
    filmIntensity: 0.18
  },
  low: {
    pixelRatioMax: 1,
    bloomBase: 0.56,
    bloomBoost: 0.62,
    starCount: 720,
    filmIntensity: 0.09
  }
};

type CinematicQualityContextValue = {
  quality: CinematicQuality;
  setQuality: (next: CinematicQuality) => void;
  config: QualityConfig;
};

const CinematicQualityContext = createContext<CinematicQualityContextValue | null>(null);

function getAutoDefault(): CinematicQuality {
  if (typeof window === "undefined") {
    return "high";
  }

  const memory = (navigator as Navigator & { deviceMemory?: number }).deviceMemory;
  const cores = navigator.hardwareConcurrency ?? 8;

  if (memory && memory <= 4) {
    return "low";
  }

  if (cores <= 4) {
    return "medium";
  }

  return "high";
}

export function CinematicQualityProvider({ children }: { children: ReactNode }) {
  const [quality, setQuality] = useState<CinematicQuality>("high");

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    const stored = window.localStorage.getItem("onlooker_cinematic_quality") as CinematicQuality | null;
    if (stored === "high" || stored === "medium" || stored === "low") {
      setQuality(stored);
      return;
    }

    setQuality(getAutoDefault());
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") {
      return;
    }

    window.localStorage.setItem("onlooker_cinematic_quality", quality);
    document.documentElement.dataset.cinematicQuality = quality;
  }, [quality]);

  const value = useMemo<CinematicQualityContextValue>(
    () => ({ quality, setQuality, config: qualityConfig[quality] }),
    [quality]
  );

  return <CinematicQualityContext.Provider value={value}>{children}</CinematicQualityContext.Provider>;
}

export function useCinematicQuality(): CinematicQualityContextValue {
  const context = useContext(CinematicQualityContext);
  if (!context) {
    throw new Error("useCinematicQuality must be used within CinematicQualityProvider");
  }
  return context;
}
