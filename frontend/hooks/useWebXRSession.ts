import { useCallback, useEffect, useMemo, useState } from "react";

export type XRMode = "immersive-vr" | "immersive-ar";
export type XRState = "idle" | "unsupported" | "ready" | "starting" | "active" | "error";

type XRSessionLike = {
  end: () => Promise<void>;
  addEventListener: (event: string, handler: () => void) => void;
};

type XRNavigator = Navigator & {
  xr?: {
    isSessionSupported: (mode: XRMode) => Promise<boolean>;
    requestSession: (mode: XRMode) => Promise<XRSessionLike>;
  };
};

export function useWebXRSession() {
  const [state, setState] = useState<XRState>("idle");
  const [error, setError] = useState<string | null>(null);
  const [supportedModes, setSupportedModes] = useState<XRMode[]>([]);
  const [session, setSession] = useState<XRSessionLike | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function probe() {
      const xr = (navigator as XRNavigator).xr;
      if (!xr) {
        if (!cancelled) {
          setState("unsupported");
        }
        return;
      }

      const modes: XRMode[] = [];
      for (const mode of ["immersive-vr", "immersive-ar"] as XRMode[]) {
        try {
          const supported = await xr.isSessionSupported(mode);
          if (supported) {
            modes.push(mode);
          }
        } catch {
          // Ignore unsupported probe errors and continue checking remaining modes.
        }
      }

      if (!cancelled) {
        setSupportedModes(modes);
        setState(modes.length > 0 ? "ready" : "unsupported");
      }
    }

    void probe();
    return () => {
      cancelled = true;
    };
  }, []);

  const startSession = useCallback(async (mode: XRMode) => {
    const xr = (navigator as XRNavigator).xr;
    if (!xr) {
      setState("unsupported");
      return;
    }

    setError(null);
    setState("starting");
    try {
      const nextSession = await xr.requestSession(mode);
      setSession(nextSession);
      setState("active");
      nextSession.addEventListener("end", () => {
        setSession(null);
        setState("ready");
      });
    } catch (err) {
      setState("error");
      setError(err instanceof Error ? err.message : "WebXR session failed to start");
    }
  }, []);

  const endSession = useCallback(async () => {
    if (!session) {
      return;
    }
    await session.end();
    setSession(null);
    setState("ready");
  }, [session]);

  const label = useMemo(() => {
    if (state === "unsupported") {
      return "Unsupported";
    }
    if (state === "active") {
      return "Active";
    }
    if (state === "starting") {
      return "Starting";
    }
    if (state === "error") {
      return "Error";
    }
    return supportedModes.length > 0 ? `Ready (${supportedModes.join(", ")})` : "Checking";
  }, [state, supportedModes]);

  return {
    state,
    label,
    error,
    supportedModes,
    startSession,
    endSession,
    hasXR: supportedModes.length > 0,
  };
}
