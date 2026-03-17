import { CinematicRoutePage, CinematicRouteTone } from "./cinematicRoute";

export type BrandTransitionVariant = "aperture" | "streak" | "scan";

export type BrandSceneDirection = {
  heroScale: number;
  heroYOffset: number;
  ringTiltX: number;
  ringTiltY: number;
  energySpin: number;
  bloomLift: number;
  colorBias: string;
};

export type BrandTimingProfile = {
  panelRevealDuration: number;
  panelRevealEase: string;
  chipPulseDuration: number;
  transitionDuration: number;
};

export type BrandAssetOverrides = {
  logoMarkUrl?: string;
  heroNormalMapUrl?: string;
  noiseTextureUrl?: string;
};

export type BrandIntensitySettings = {
  transitionAggressiveness: number;
  cameraMovementIntensity: number;
  parallaxIntensity: number;
  uiPulseIntensity: number;
  glowIntensity: number;
};

export type BrandMoodLines = {
  home: string;
  dashboard: string;
  simulations: string;
  reports: string;
  admin: string;
};

export type BrandDirectionConfig = {
  transitionVariant: BrandTransitionVariant;
  sceneByTone: Record<CinematicRouteTone, BrandSceneDirection>;
  timingByPage: Record<CinematicRoutePage, BrandTimingProfile>;
  intensity: BrandIntensitySettings;
  moodLines: BrandMoodLines;
  assetOverrides: BrandAssetOverrides;
};

// User-editable brand surface for The On Lookers signature DNA.
export const onLookersBrandDirection: BrandDirectionConfig = {
  transitionVariant: "streak",
  intensity: {
    transitionAggressiveness: 9,
    cameraMovementIntensity: 8,
    parallaxIntensity: 7,
    uiPulseIntensity: 6,
    glowIntensity: 9
  },
  moodLines: {
    home: "bold cinematic immersive",
    dashboard: "tactical confident futuristic",
    simulations: "intense kinetic predictive",
    reports: "authoritative precise cinematic",
    admin: "secure controlled elite"
  },
  assetOverrides: {
    logoMarkUrl: "/brand/onlookers-mark.svg",
    heroNormalMapUrl: "/brand/planet-normal.png",
    noiseTextureUrl: "/brand/transition-noise.png"
  },
  sceneByTone: {
    opening: {
      heroScale: 1.02,
      heroYOffset: 0.18,
      ringTiltX: 0.6,
      ringTiltY: 0.1,
      energySpin: 1.2,
      bloomLift: 0.34,
      colorBias: "#43e6ff"
    },
    mission: {
      heroScale: 1.06,
      heroYOffset: 0.08,
      ringTiltX: 0.64,
      ringTiltY: 0.15,
      energySpin: 1.34,
      bloomLift: 0.3,
      colorBias: "#5fd3ff"
    },
    battle: {
      heroScale: 1.12,
      heroYOffset: -0.03,
      ringTiltX: 0.7,
      ringTiltY: 0.24,
      energySpin: 1.62,
      bloomLift: 0.4,
      colorBias: "#ff9f43"
    },
    briefing: {
      heroScale: 1,
      heroYOffset: 0.14,
      ringTiltX: 0.56,
      ringTiltY: 0.17,
      energySpin: 1.08,
      bloomLift: 0.28,
      colorBias: "#a584ff"
    },
    world: {
      heroScale: 1.1,
      heroYOffset: 0.04,
      ringTiltX: 0.67,
      ringTiltY: 0.14,
      energySpin: 1.48,
      bloomLift: 0.38,
      colorBias: "#44ffe1"
    },
    finale: {
      heroScale: 1.14,
      heroYOffset: 0.02,
      ringTiltX: 0.72,
      ringTiltY: 0.26,
      energySpin: 1.58,
      bloomLift: 0.42,
      colorBias: "#ffd071"
    }
  },
  timingByPage: {
    home: {
      panelRevealDuration: 0.56,
      panelRevealEase: "expo.out",
      chipPulseDuration: 1.22,
      transitionDuration: 0.5
    },
    dashboard: {
      panelRevealDuration: 0.54,
      panelRevealEase: "expo.out",
      chipPulseDuration: 1.3,
      transitionDuration: 0.48
    },
    simulations: {
      panelRevealDuration: 0.5,
      panelRevealEase: "expo.out",
      chipPulseDuration: 1.14,
      transitionDuration: 0.46
    },
    reports: {
      panelRevealDuration: 0.53,
      panelRevealEase: "expo.out",
      chipPulseDuration: 1.22,
      transitionDuration: 0.47
    },
    projects: {
      panelRevealDuration: 0.53,
      panelRevealEase: "expo.out",
      chipPulseDuration: 1.28,
      transitionDuration: 0.47
    },
    visualization: {
      panelRevealDuration: 0.5,
      panelRevealEase: "expo.out",
      chipPulseDuration: 1.18,
      transitionDuration: 0.46
    },
    admin: {
      panelRevealDuration: 0.5,
      panelRevealEase: "power3.out",
      chipPulseDuration: 1.32,
      transitionDuration: 0.46
    },
    auth: {
      panelRevealDuration: 0.46,
      panelRevealEase: "power3.out",
      chipPulseDuration: 1.36,
      transitionDuration: 0.44
    },
    default: {
      panelRevealDuration: 0.52,
      panelRevealEase: "expo.out",
      chipPulseDuration: 1.24,
      transitionDuration: 0.47
    }
  }
};
