import React from "react";
import { act, render, waitFor } from "@testing-library/react";

import { useLocalSimPlatform } from "../../components/outsource/local-simulated/useLocalSimPlatform";
import {
  clearTelemetryBuffer,
  getTelemetryBuffer,
} from "../../components/outsource/local-simulated/telemetry";
import { apiFetch } from "../../utils/api";
import {
  askCopilot,
  attachSimulationToProject,
  getAccessTokenClaims,
  runSimulationWithPersistence,
} from "../../components/outsource/local-simulated/backendClient";
import { toast } from "sonner";

jest.mock("../../utils/api", () => ({
  apiFetch: jest.fn(),
}));

jest.mock("sonner", () => ({
  toast: {
    success: jest.fn(),
    error: jest.fn(),
    info: jest.fn(),
  },
}));

jest.mock("../../components/outsource/local-simulated/backendClient", () => ({
  askCopilot: jest.fn(),
  attachSimulationToProject: jest.fn(),
  getAccessTokenClaims: jest.fn(),
  runSimulationWithPersistence: jest.fn(),
}));

type HookValue = ReturnType<typeof useLocalSimPlatform>;

function HookHarness(props: { onRender: (value: HookValue) => void }) {
  const value = useLocalSimPlatform();
  props.onRender(value);
  return null;
}

describe("useLocalSimPlatform", () => {
  const apiFetchMock = apiFetch as unknown as jest.Mock;
  const askCopilotMock = askCopilot as unknown as jest.Mock;
  const attachSimulationToProjectMock = attachSimulationToProject as unknown as jest.Mock;
  const getAccessTokenClaimsMock = getAccessTokenClaims as unknown as jest.Mock;
  const runSimulationWithPersistenceMock = runSimulationWithPersistence as unknown as jest.Mock;

  beforeEach(() => {
    jest.clearAllMocks();
    clearTelemetryBuffer();
    window.localStorage.clear();

    getAccessTokenClaimsMock.mockReturnValue({
      sub: "user-1",
      email: "operator@example.com",
      role: "engineer",
    });

    apiFetchMock.mockImplementation((path: string, init?: RequestInit) => {
      if (path === "/projects" && (!init?.method || init.method === "GET")) {
        return Promise.resolve([]);
      }

      if (path === "/projects" && init?.method === "POST") {
        return Promise.resolve({ id: "proj-created" });
      }

      return Promise.reject(new Error(`Unexpected call: ${path}`));
    });

    askCopilotMock.mockResolvedValue("Narrative output");
    attachSimulationToProjectMock.mockResolvedValue(undefined);
    runSimulationWithPersistenceMock.mockResolvedValue({
      riskScore: 55,
      corrosionRate: 0.04,
      predictedLifespan: 18,
      degradationTimeline: [{ year: 0, thickness: 100 }],
      capexRequirement: 1000,
      projectedROI: 2.5,
      lifecycleExtension: 4.2,
      esgCompliance: 82,
      interventions: [],
      recommendationSummary: "summary",
      riskBand: "medium",
      backendSimulationId: "sim-1",
    });
  });

  it("restores auth and emits project refresh telemetry", async () => {
    let latest: HookValue | undefined;

    render(<HookHarness onRender={(value) => {
      latest = value;
    }} />);

    await waitFor(() => {
      expect(latest?.isAuthReady).toBe(true);
    });

    await waitFor(() => {
      expect(apiFetchMock).toHaveBeenCalledWith("/projects");
    });

    const names = getTelemetryBuffer().map((event) => event.name);

    expect(names).toContain("auth.session.restored");
    expect(names).toContain("projects.refresh.started");
    expect(names).toContain("projects.refresh.succeeded");
  });

  it("runs simulation orchestration and emits completion events", async () => {
    let latest: HookValue | undefined;

    render(<HookHarness onRender={(value) => {
      latest = value;
    }} />);

    await waitFor(() => {
      expect(latest?.isAuthReady).toBe(true);
    });

    await act(async () => {
      await latest?.startSimulation({
        material: "Carbon Steel",
        structure: "Pipeline",
      });
    });

    await waitFor(() => {
      expect(runSimulationWithPersistenceMock).toHaveBeenCalledTimes(1);
    });

    expect(apiFetchMock).toHaveBeenCalledWith(
      "/projects",
      expect.objectContaining({
        method: "POST",
      })
    );

    expect(attachSimulationToProjectMock).toHaveBeenCalled();
    expect((toast.success as unknown as jest.Mock).mock.calls.length).toBeGreaterThan(0);

    const names = getTelemetryBuffer().map((event) => event.name);
    expect(names).toContain("orchestration.simulation.started");
    expect(names).toContain("orchestration.simulation.completed");
  });
});
