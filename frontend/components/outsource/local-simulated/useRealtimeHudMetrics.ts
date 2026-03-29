import { useEffect, useMemo, useState } from 'react';

type NavigatorWithConnection = Navigator & {
  connection?: {
    rtt?: number;
  };
};

type NavigatorWithDeviceMemory = Navigator & {
  deviceMemory?: number;
};

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

function readBrowserRtt(): number | null {
  if (typeof navigator === 'undefined') {
    return null;
  }

  const rtt = (navigator as NavigatorWithConnection).connection?.rtt;
  if (typeof rtt !== 'number' || !Number.isFinite(rtt) || rtt <= 0) {
    return null;
  }

  return Math.round(rtt);
}

function readHardwareThreads(): number {
  if (typeof navigator === 'undefined' || typeof navigator.hardwareConcurrency !== 'number') {
    return 4;
  }

  return clamp(Math.round(navigator.hardwareConcurrency), 1, 64);
}

function readDeviceMemory(): number {
  if (typeof navigator === 'undefined') {
    return 8;
  }

  const memory = (navigator as NavigatorWithDeviceMemory).deviceMemory;
  if (typeof memory !== 'number' || !Number.isFinite(memory) || memory <= 0) {
    return 8;
  }

  return clamp(memory, 1, 64);
}

export type RealtimeHudMetrics = {
  securityLabel: string;
  encryptionLabel: string;
  latencyMs: number | null;
  latencyLabel: string;
  computeTflops: number;
  computeTflopsLabel: string;
  computeLoadPercent: number;
  computeLoadLabel: string;
  localClockLabel: string;
  liveFeedUtcLabel: string;
};

export function useRealtimeHudMetrics(): RealtimeHudMetrics {
  const [clock, setClock] = useState(() => new Date());
  const [latencyMs, setLatencyMs] = useState<number | null>(null);
  const [fps, setFps] = useState(60);
  const [isOnline, setIsOnline] = useState<boolean>(() => {
    if (typeof navigator === 'undefined') {
      return true;
    }
    return navigator.onLine;
  });

  useEffect(() => {
    const timer = window.setInterval(() => {
      setClock(new Date());
    }, 1000);

    return () => {
      window.clearInterval(timer);
    };
  }, []);

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  useEffect(() => {
    let rafId = 0;
    let frameCounter = 0;
    let accumulator = 0;
    let lastTick = performance.now();

    const loop = (timestamp: number) => {
      const delta = timestamp - lastTick;
      lastTick = timestamp;
      frameCounter += 1;
      accumulator += delta;

      if (accumulator >= 1000) {
        const nextFps = Math.round((frameCounter * 1000) / accumulator);
        setFps(clamp(nextFps, 1, 240));
        frameCounter = 0;
        accumulator = 0;
      }

      rafId = window.requestAnimationFrame(loop);
    };

    rafId = window.requestAnimationFrame(loop);

    return () => {
      window.cancelAnimationFrame(rafId);
    };
  }, []);

  useEffect(() => {
    let cancelled = false;

    const probeLatency = async () => {
      const browserRtt = readBrowserRtt();

      if (!navigator.onLine) {
        if (!cancelled && browserRtt !== null) {
          setLatencyMs(clamp(browserRtt, 1, 999));
        }
        return;
      }

      const controller = new AbortController();
      const timeoutId = window.setTimeout(() => controller.abort(), 4000);
      const startedAt = performance.now();

      try {
        await fetch(`/favicon.ico?probe=${Date.now()}`, {
          method: 'GET',
          cache: 'no-store',
          signal: controller.signal,
        });

        const measured = clamp(Math.round(performance.now() - startedAt), 1, 999);
        const blended = browserRtt === null ? measured : clamp(Math.round((measured + browserRtt) / 2), 1, 999);

        if (!cancelled) {
          setLatencyMs(blended);
        }
      } catch {
        if (!cancelled && browserRtt !== null) {
          setLatencyMs(clamp(browserRtt, 1, 999));
        }
      } finally {
        window.clearTimeout(timeoutId);
      }
    };

    probeLatency();
    const timer = window.setInterval(probeLatency, 5000);

    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, []);

  return useMemo(() => {
    const currentLatency = latencyMs ?? readBrowserRtt();
    const latencyForCompute = currentLatency ?? 18;
    const normalizedFps = clamp(fps, 12, 144);
    const hardwareThreads = readHardwareThreads();
    const memoryGb = readDeviceMemory();

    const computeLoadPercent = Math.round(
      clamp(45 + latencyForCompute * 1.55 + (60 - Math.min(normalizedFps, 60)) * 1.2, 20, 99)
    );

    const computeTflops = Number(
      (((normalizedFps * hardwareThreads * memoryGb) / 90) * (computeLoadPercent / 70)).toFixed(1)
    );

    const isSecure = typeof window !== 'undefined' ? window.isSecureContext : true;

    return {
      securityLabel: !isOnline ? 'Offline' : isSecure ? 'Secure' : 'Insecure',
      encryptionLabel: !isOnline ? 'Link Lost' : isSecure ? 'AES-256-GCM' : 'Unencrypted',
      latencyMs,
      latencyLabel: currentLatency === null ? '--ms' : `${currentLatency}ms`,
      computeTflops,
      computeTflopsLabel: `${computeTflops.toFixed(1)} TFLOPS`,
      computeLoadPercent,
      computeLoadLabel: `${computeLoadPercent}%`,
      localClockLabel: clock.toLocaleTimeString([], {
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      }),
      liveFeedUtcLabel: `${clock.toLocaleTimeString('en-GB', {
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        timeZone: 'UTC',
      })} UTC`,
    };
  }, [clock, fps, isOnline, latencyMs]);
}