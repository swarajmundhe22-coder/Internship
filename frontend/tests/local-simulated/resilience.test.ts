import {
  calculateBackoffDelayMs,
  isRetryableError,
  withRetry,
} from "../../components/outsource/local-simulated/resilience";
import {
  clearTelemetryBuffer,
  getTelemetryBuffer,
} from "../../components/outsource/local-simulated/telemetry";

describe("resilience", () => {
  beforeEach(() => {
    clearTelemetryBuffer();
  });

  it("classifies network and transient HTTP errors as retryable", () => {
    expect(isRetryableError(Object.assign(new Error("network"), { kind: "network" }))).toBe(true);
    expect(isRetryableError(Object.assign(new Error("overloaded"), { status: 503 }))).toBe(true);
    expect(isRetryableError(Object.assign(new Error("bad request"), { status: 400 }))).toBe(false);
  });

  it("computes deterministic backoff when jitter is disabled", () => {
    expect(calculateBackoffDelayMs(1, { baseDelayMs: 100, jitterRatio: 0, random: () => 0.5 })).toBe(100);
    expect(calculateBackoffDelayMs(2, { baseDelayMs: 100, jitterRatio: 0, random: () => 0.5 })).toBe(200);
  });

  it("retries a transient failure and emits retry telemetry", async () => {
    const runOperation = jest
      .fn<Promise<string>, []>()
      .mockRejectedValueOnce(Object.assign(new Error("service unavailable"), { status: 503 }))
      .mockResolvedValueOnce("ok");

    await expect(
      withRetry(runOperation, {
        operation: "projects.list",
        path: "/projects",
        method: "GET",
        maxAttempts: 3,
        baseDelayMs: 1,
        jitterRatio: 0,
      })
    ).resolves.toBe("ok");

    expect(runOperation).toHaveBeenCalledTimes(2);

    const names = getTelemetryBuffer().map((event) => event.name);
    expect(names).toContain("api.retry.scheduled");
    expect(names).toContain("api.retry.recovered");
  });

  it("does not retry non-retryable errors and emits exhausted telemetry", async () => {
    const runOperation = jest
      .fn<Promise<string>, []>()
      .mockRejectedValue(Object.assign(new Error("invalid"), { status: 400 }));

    await expect(
      withRetry(runOperation, {
        operation: "projects.create",
        path: "/projects",
        method: "POST",
        maxAttempts: 3,
        baseDelayMs: 1,
        jitterRatio: 0,
      })
    ).rejects.toThrow("invalid");

    expect(runOperation).toHaveBeenCalledTimes(1);

    const names = getTelemetryBuffer().map((event) => event.name);
    expect(names).toContain("api.retry.exhausted");
  });
});
