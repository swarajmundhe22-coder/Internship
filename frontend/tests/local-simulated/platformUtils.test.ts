import {
  displayNameFromEmail,
  generateScenarioId,
  hydrateProjects,
  loadScenarioMap,
  persistScenarioMap,
} from "../../components/outsource/local-simulated/platformUtils";
import type {
  BackendProjectRecord,
  LocalScenario,
} from "../../components/outsource/local-simulated/types";

describe("platformUtils", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("formats display name from email local-part tokens", () => {
    expect(displayNameFromEmail("jane_doe.engineer@example.com")).toBe("Jane Doe Engineer");
    expect(displayNameFromEmail("@example.com")).toBe("Operator");
  });

  it("persists and restores scenario map", () => {
    const scenarios: LocalScenario[] = [
      {
        id: "scn-1",
        name: "Baseline",
        data: { material: "Carbon Steel" },
        result: { riskScore: 42 },
        createdAt: "2026-03-29T00:00:00.000Z",
      },
    ];

    persistScenarioMap({ "proj-1": scenarios });

    expect(loadScenarioMap()).toEqual({ "proj-1": scenarios });
  });

  it("returns an empty map for malformed storage payload", () => {
    window.localStorage.setItem("onlooker_local_simulated_scenarios_v1", "{invalid-json");
    expect(loadScenarioMap()).toEqual({});
  });

  it("hydrates project scenarios preferring locally stored scenarios", () => {
    const metadataScenario: LocalScenario = {
      id: "meta-scn",
      name: "Metadata",
      data: { material: "Carbon Steel" },
      result: { riskScore: 50 },
      createdAt: "2026-03-29T00:00:00.000Z",
    };

    const storedScenario: LocalScenario = {
      id: "stored-scn",
      name: "Stored",
      data: { material: "Duplex" },
      result: { riskScore: 20 },
      createdAt: "2026-03-29T00:00:00.000Z",
    };

    const projectRecord: BackendProjectRecord = {
      id: "proj-1",
      name: "North Sea Asset",
      user_id: "owner-1",
      metadata: {
        parameters: { structure: "Pipeline" },
        scenarios: [metadataScenario],
      },
      created_at: "2026-03-29T00:00:00.000Z",
      updated_at: "2026-03-29T00:00:00.000Z",
    };

    const hydrated = hydrateProjects([projectRecord], { "proj-1": [storedScenario] });

    expect(hydrated).toHaveLength(1);
    expect(hydrated[0].scenarios).toEqual([storedScenario]);
    expect(hydrated[0].ownerId).toBe("owner-1");
  });

  it("generates a non-empty scenario id", () => {
    expect(generateScenarioId().length).toBeGreaterThan(5);
  });
});
