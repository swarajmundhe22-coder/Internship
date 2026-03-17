import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ReportViewer } from "../components/ReportViewer";

const useApiMock = {
  run: jest.fn(),
  downloadReportPdf: jest.fn()
};

jest.mock("../hooks/useApi", () => ({
  useApi: () => useApiMock
}));

jest.mock("../components/VisualizationPanel", () => ({
  VisualizationPanel: () => <div data-testid="viz-panel" />
}));

describe("ReportViewer PDF export UX", () => {
  beforeEach(() => {
    jest.clearAllMocks();

    useApiMock.run.mockResolvedValue({
      items: [
        {
          id: "report-1",
          simulation_id: "sim-1",
          report_uri: "https://example.test/report.html",
          status: "ready",
          version: 1,
          created_at: "2026-03-16T00:00:00.000Z",
          updated_at: "2026-03-16T00:00:00.000Z"
        }
      ],
      total: 1,
      page: 1,
      page_size: 1
    });

    useApiMock.downloadReportPdf.mockResolvedValue(new Blob(["pdf"], { type: "application/pdf" }));

    Object.defineProperty(window.URL, "createObjectURL", {
      writable: true,
      value: jest.fn(() => "blob:report-pdf")
    });
    Object.defineProperty(window.URL, "revokeObjectURL", {
      writable: true,
      value: jest.fn()
    });
    jest.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  it("downloads PDF and displays success feedback", async () => {
    render(
      <ReportViewer
        report={{
          generated_at: "2026-03-16T00:00:00.000Z",
          simulation_id: "sim-1",
          material: { name: "Steel" },
          environment: { profile_name: "Marine" },
          metrics: {
            corrosion_rate_mm_per_year: 0.023,
            risk_classification: "high",
            estimated_lifespan_years: 3.6
          },
          recommendation_summary: "Inspect within 90 days.",
          visual_summary: {
            intensity_map: [
              { label: "Outer wall", value: 78 }
            ]
          }
        }}
      />
    );

    await userEvent.click(screen.getByRole("button", { name: "Download PDF" }));

    await waitFor(() => {
      expect(screen.getByText("PDF download started.")).toBeInTheDocument();
    });

    expect(useApiMock.downloadReportPdf).toHaveBeenCalledWith("report-1");
  });
});
