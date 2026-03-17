import { act, fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { SimulationPlaybackPanel } from "../components/SimulationPlaybackPanel";

jest.mock("../components/VisualizationPanel", () => ({
  VisualizationPanel: ({ intensity }: { intensity: number }) => <div data-testid="viz">Intensity {intensity}</div>
}));

describe("SimulationPlaybackPanel", () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });

  it("supports play and scrub controls over timeline frames", async () => {
    const user = userEvent.setup({ advanceTimers: jest.advanceTimersByTime });
    render(
      <SimulationPlaybackPanel
        timeline={[
          {
            offset_hours: 0,
            corrosion_rate_mm_per_year: 0.1,
            estimated_lifespan_years: 10,
            risk_score: 40,
            risk_classification: "moderate"
          },
          {
            offset_hours: 24,
            corrosion_rate_mm_per_year: 0.14,
            estimated_lifespan_years: 8.5,
            risk_score: 62,
            risk_classification: "high"
          },
          {
            offset_hours: 48,
            corrosion_rate_mm_per_year: 0.2,
            estimated_lifespan_years: 6.8,
            risk_score: 83,
            risk_classification: "critical"
          }
        ]}
      />
    );

    expect(screen.getByText("Step 1 / 3")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Play" }));

    act(() => {
      jest.advanceTimersByTime(1000);
    });

    expect(screen.getByText("Step 2 / 3")).toBeInTheDocument();

    const scrub = screen.getByLabelText("Playback scrub");
    fireEvent.change(scrub, { target: { value: "2" } });

    expect(screen.getByText("Step 3 / 3")).toBeInTheDocument();
    expect(screen.getByText("critical")).toBeInTheDocument();
  });
});
