import { render, screen } from "@testing-library/react";

import { ComparePanel } from "../components/ComparePanel";

describe("ComparePanel advanced visuals", () => {
  it("renders export controls and side-by-side hologram cards", () => {
    render(
      <ComparePanel
        comparison={{
          left_simulation_id: "sim-left",
          right_simulation_id: "sim-right",
          corrosion_rate_delta_mm_per_year: 0.032,
          lifespan_delta_years: -2.1,
          risk_transition: "moderate -> high",
          environmental_deltas: { chloride_ppm: 1200, ph: -0.3 },
          material_deltas: { density_kg_m3: 40, electrochemical_potential_v: -0.04 }
        }}
        leftSimulation={{
          id: "sim-left",
          material_id: "m1",
          environment_id: "e1",
          exposed_area_m2: 10,
          exposure_time_hours: 1000,
          corrosion_rate_mm_per_year: 0.11,
          estimated_lifespan_years: 12,
          risk_classification: "moderate",
          version: 1,
          created_at: "2026-03-16T00:00:00Z",
          updated_at: "2026-03-16T00:00:00Z"
        }}
        rightSimulation={{
          id: "sim-right",
          material_id: "m2",
          environment_id: "e2",
          exposed_area_m2: 10,
          exposure_time_hours: 1000,
          corrosion_rate_mm_per_year: 0.16,
          estimated_lifespan_years: 8.2,
          risk_classification: "high",
          version: 1,
          created_at: "2026-03-16T00:00:00Z",
          updated_at: "2026-03-16T00:00:00Z"
        }}
      />
    );

    expect(screen.getByRole("button", { name: "Export PDF Snapshot" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Export Playback Video" })).toBeInTheDocument();
    expect(screen.getByText("Left Hologram")).toBeInTheDocument();
    expect(screen.getByText("Right Hologram")).toBeInTheDocument();
    expect(screen.getByText("moderate -> high")).toBeInTheDocument();
  });
});
