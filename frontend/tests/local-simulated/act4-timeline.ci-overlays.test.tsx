import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import Act4Timeline from "../../components/outsource/local-simulated/components/Act4Timeline";

function readBlobAsText(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result));
    reader.onerror = () => reject(reader.error ?? new Error("Failed to read blob."));
    reader.readAsText(blob);
  });
}

jest.mock("recharts", () => {
  const NullRenderer = () => null;

  return {
    ResponsiveContainer: NullRenderer,
    LineChart: NullRenderer,
    AreaChart: NullRenderer,
    BarChart: NullRenderer,
    XAxis: NullRenderer,
    YAxis: NullRenderer,
    CartesianGrid: NullRenderer,
    Tooltip: NullRenderer,
    Line: NullRenderer,
    Area: NullRenderer,
    Bar: NullRenderer,
    ReferenceArea: NullRenderer,
    ReferenceLine: NullRenderer,
  };
});

describe("Act4Timeline CI overlay downloads", () => {
  const createObjectURLMock = jest.fn((_: Blob | MediaSource) => "blob:ci-overlay");
  const revokeObjectURLMock = jest.fn((_: string) => undefined);
  let clickSpy: jest.SpyInstance;

  beforeEach(() => {
    jest.clearAllMocks();

    Object.defineProperty(window.URL, "createObjectURL", {
      writable: true,
      value: createObjectURLMock,
    });
    Object.defineProperty(window.URL, "revokeObjectURL", {
      writable: true,
      value: revokeObjectURLMock,
    });

    clickSpy = jest.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});
  });

  afterEach(() => {
    clickSpy.mockRestore();
  });

  it("renders CI metadata and exports risk and lifespan overlay CSV files", async () => {
    const user = userEvent.setup();

    render(
      <Act4Timeline
        result={{
          riskScore: 72.4,
          corrosionRate: 0.18,
          designCorrosionRate: 0.28,
          predictedLifespan: 18.2,
          degradationTimeline: [
            { year: 0, thickness: 100 },
            { year: 5, thickness: 91 },
            { year: 10, thickness: 82 },
            { year: 15, thickness: 73 },
            { year: 20, thickness: 64 },
          ],
          inputData: {
            assetValue: 60000000,
            downtimeCost: 300000,
          },
          modelVersion: "global-calibrated-v1.1.0",
          regionKey: "north_sea_offshore",
          regionName: "North Sea Offshore",
          assetProfile: "offshore_platform_fixed",
          initialThicknessMm: 28,
          minimumSafeThicknessMm: 18,
          uncertaintyBands: {
            designCorrosionRate: {
              lower: 0.22,
              upper: 0.36,
              confidenceLevel: 0.9,
            },
            riskScore: {
              lower: 64.4,
              upper: 80.4,
              confidenceLevel: 0.9,
            },
            predictedLifespan: {
              lower: 14.2,
              upper: 22.5,
              confidenceLevel: 0.9,
            },
          },
        }}
        narrative="Operational narrative"
        onNext={jest.fn()}
      />
    );

    expect(screen.getByText(/Region Pack: North Sea Offshore/i)).toBeInTheDocument();
    expect(screen.getByText(/^Risk Score CI$/i)).toBeInTheDocument();
    expect(screen.getByText(/^Lifespan CI$/i)).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /Risk CI CSV/i }));
    await user.click(screen.getByRole("button", { name: /Lifespan CI CSV/i }));

    expect(createObjectURLMock).toHaveBeenCalledTimes(2);
    expect(revokeObjectURLMock).toHaveBeenCalledTimes(2);
    expect(clickSpy).toHaveBeenCalledTimes(2);

    const riskCall = createObjectURLMock.mock.calls.at(0);
    if (!riskCall) {
      throw new Error("Expected first CSV blob call for risk overlay.");
    }
    const riskSource = riskCall[0];
    if (!(riskSource instanceof Blob)) {
      throw new Error("Risk overlay source is not a Blob.");
    }
    const riskCsvBlob = riskSource;
    const riskCsv = await readBlobAsText(riskCsvBlob);
    expect(riskCsv).toContain("risk_score_ci_lower");
    expect(riskCsv).toContain("risk_score_ci_upper");
    expect(riskCsv).toContain("confidence_level");

    const lifespanCall = createObjectURLMock.mock.calls.at(1);
    if (!lifespanCall) {
      throw new Error("Expected second CSV blob call for lifespan overlay.");
    }
    const lifespanSource = lifespanCall[0];
    if (!(lifespanSource instanceof Blob)) {
      throw new Error("Lifespan overlay source is not a Blob.");
    }
    const lifespanCsvBlob = lifespanSource;
    const lifespanCsv = await readBlobAsText(lifespanCsvBlob);
    expect(lifespanCsv).toContain("remaining_lifespan_ci_lower_years");
    expect(lifespanCsv).toContain("remaining_lifespan_ci_upper_years");
    expect(lifespanCsv).toContain("confidence_level");
  });
});
