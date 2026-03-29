export type TelemetryCategory = "domain_event" | "api_retry";
export type TelemetrySeverity = "info" | "warn" | "error";

export type TraceContext = {
  traceId: string;
  actorId?: string;
  projectId?: string;
};

export type TelemetryEvent<TPayload extends Record<string, unknown> = Record<string, unknown>> = {
  id: string;
  category: TelemetryCategory;
  name: string;
  severity: TelemetrySeverity;
  timestamp: string;
  traceId?: string;
  actorId?: string;
  projectId?: string;
  payload: TPayload;
};

export type TelemetryListener = (event: TelemetryEvent) => void;

const listeners = new Set<TelemetryListener>();
const eventBuffer: TelemetryEvent[] = [];
const MAX_BUFFER_SIZE = 300;

function nextId(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return Math.random().toString(36).slice(2, 12);
}

function pushToBuffer(event: TelemetryEvent): void {
  eventBuffer.push(event);
  if (eventBuffer.length > MAX_BUFFER_SIZE) {
    eventBuffer.shift();
  }
}

function maybeConsoleDebug(event: TelemetryEvent): void {
  if (typeof window === "undefined") {
    return;
  }

  const debugWindow = window as Window & { __ONLOOKER_TELEMETRY_DEBUG__?: boolean };
  if (!debugWindow.__ONLOOKER_TELEMETRY_DEBUG__) {
    return;
  }

  // Keep this opt-in to avoid noise in production by default.
  console.debug(`[telemetry] ${event.name}`, event);
}

export function subscribeTelemetry(listener: TelemetryListener): () => void {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

export function getTelemetryBuffer(): TelemetryEvent[] {
  return [...eventBuffer];
}

export function clearTelemetryBuffer(): void {
  eventBuffer.length = 0;
}

export function createTraceContext(seed: Partial<TraceContext> = {}): TraceContext {
  return {
    traceId: seed.traceId ?? nextId(),
    actorId: seed.actorId,
    projectId: seed.projectId,
  };
}

export function emitTelemetryEvent<TPayload extends Record<string, unknown>>(input: {
  category: TelemetryCategory;
  name: string;
  payload: TPayload;
  severity?: TelemetrySeverity;
  context?: Partial<TraceContext>;
}): TelemetryEvent<TPayload> {
  const event: TelemetryEvent<TPayload> = {
    id: nextId(),
    category: input.category,
    name: input.name,
    severity: input.severity ?? "info",
    timestamp: new Date().toISOString(),
    traceId: input.context?.traceId,
    actorId: input.context?.actorId,
    projectId: input.context?.projectId,
    payload: input.payload,
  };

  pushToBuffer(event);
  maybeConsoleDebug(event);

  listeners.forEach((listener) => {
    try {
      listener(event);
    } catch (error) {
      console.error("Telemetry listener error", error);
    }
  });

  return event;
}

export function emitDomainEvent<TPayload extends Record<string, unknown>>(
  name: string,
  payload: TPayload,
  context?: Partial<TraceContext>,
  severity: TelemetrySeverity = "info"
): TelemetryEvent<TPayload> {
  return emitTelemetryEvent({
    category: "domain_event",
    name,
    payload,
    context,
    severity,
  });
}
