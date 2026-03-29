import { createTraceContext, emitDomainEvent, emitTelemetryEvent, type TraceContext } from "./telemetry";

type RetryableError = Error & {
  kind?: string;
  status?: number;
  detail?: string;
};

export type RetryExecutionOptions = {
  operation: string;
  path: string;
  method: string;
  traceContext?: Partial<TraceContext>;
  maxAttempts?: number;
  baseDelayMs?: number;
  maxDelayMs?: number;
  jitterRatio?: number;
  random?: () => number;
};

const RETRYABLE_STATUS_CODES = new Set([408, 425, 429, 500, 502, 503, 504]);

export function toErrorSummary(error: unknown): Record<string, unknown> {
  const typed = error as RetryableError;

  return {
    kind: typed?.kind ?? "unknown",
    status: typeof typed?.status === "number" ? typed.status : undefined,
    message: typed?.message ?? "Unexpected error",
    detail: typed?.detail,
  };
}

export function isRetryableError(error: unknown): boolean {
  const typed = error as RetryableError;

  if (typed?.kind === "network") {
    return true;
  }

  if (typeof typed?.status === "number" && RETRYABLE_STATUS_CODES.has(typed.status)) {
    return true;
  }

  return false;
}

export function calculateBackoffDelayMs(
  attempt: number,
  options?: {
    baseDelayMs?: number;
    maxDelayMs?: number;
    jitterRatio?: number;
    random?: () => number;
  }
): number {
  const baseDelayMs = options?.baseDelayMs ?? 200;
  const maxDelayMs = options?.maxDelayMs ?? 2000;
  const jitterRatio = options?.jitterRatio ?? 0.2;
  const random = options?.random ?? Math.random;

  const exponentialDelay = Math.min(maxDelayMs, baseDelayMs * 2 ** Math.max(attempt - 1, 0));
  const jitterWindow = exponentialDelay * jitterRatio;
  const jitter = (random() * 2 - 1) * jitterWindow;

  return Math.max(0, Math.round(exponentialDelay + jitter));
}

export function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => {
    setTimeout(resolve, ms);
  });
}

export async function withRetry<T>(
  runOperation: () => Promise<T>,
  options: RetryExecutionOptions
): Promise<T> {
  const maxAttempts = options.maxAttempts ?? 3;
  const traceContext = createTraceContext(options.traceContext);

  let attempt = 1;

  while (attempt <= maxAttempts) {
    try {
      const value = await runOperation();

      if (attempt > 1) {
        emitTelemetryEvent({
          category: "api_retry",
          name: "api.retry.recovered",
          context: traceContext,
          payload: {
            operation: options.operation,
            path: options.path,
            method: options.method,
            attempt,
          },
        });
      }

      return value;
    } catch (error) {
      const retryable = isRetryableError(error);
      const hasRemainingAttempt = attempt < maxAttempts;

      if (!retryable || !hasRemainingAttempt) {
        emitTelemetryEvent({
          category: "api_retry",
          name: "api.retry.exhausted",
          severity: "error",
          context: traceContext,
          payload: {
            operation: options.operation,
            path: options.path,
            method: options.method,
            attempt,
            maxAttempts,
            retryable,
            ...toErrorSummary(error),
          },
        });
        throw error;
      }

      const delayMs = calculateBackoffDelayMs(attempt, {
        baseDelayMs: options.baseDelayMs,
        maxDelayMs: options.maxDelayMs,
        jitterRatio: options.jitterRatio,
        random: options.random,
      });

      emitTelemetryEvent({
        category: "api_retry",
        name: "api.retry.scheduled",
        severity: "warn",
        context: traceContext,
        payload: {
          operation: options.operation,
          path: options.path,
          method: options.method,
          attempt,
          nextAttempt: attempt + 1,
          delayMs,
          ...toErrorSummary(error),
        },
      });

      await sleep(delayMs);
      attempt += 1;
    }
  }

  throw new Error("Retry loop exited unexpectedly");
}

export async function executeCriticalApiRequest<T>(
  request: () => Promise<T>,
  options: RetryExecutionOptions
): Promise<T> {
  const traceContext = createTraceContext(options.traceContext);
  const startedAt = Date.now();

  emitDomainEvent(
    "api.request.started",
    {
      operation: options.operation,
      path: options.path,
      method: options.method,
    },
    traceContext
  );

  try {
    const result = await withRetry(request, {
      ...options,
      traceContext,
    });

    emitDomainEvent(
      "api.request.succeeded",
      {
        operation: options.operation,
        path: options.path,
        method: options.method,
        durationMs: Date.now() - startedAt,
      },
      traceContext
    );

    return result;
  } catch (error) {
    emitDomainEvent(
      "api.request.failed",
      {
        operation: options.operation,
        path: options.path,
        method: options.method,
        durationMs: Date.now() - startedAt,
        ...toErrorSummary(error),
      },
      traceContext,
      "error"
    );

    throw error;
  }
}
