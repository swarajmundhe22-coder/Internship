import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import GlobalRiskAtlasPage from "../pages/visualization/global-risk-atlas";

jest.mock("next/dynamic", () => () => {
  return function MockAtlasMap(props: { points: unknown[] }) {
    return <div data-testid="atlas-map-mock">points:{props.points.length}</div>;
  };
});

jest.mock("next/link", () => {
  return function MockLink({ href, children, ...props }: any) {
    const resolvedHref = typeof href === "string" ? href : href?.pathname ?? "";
    return <a href={resolvedHref} {...props}>{children}</a>;
  };
});

jest.mock("next/router", () => ({
  useRouter: () => ({
    pathname: "/visualization/global-risk-atlas",
    push: jest.fn()
  })
}));

const intelligenceMock = {
  loading: false,
  error: null as string | null,
  history: {},
  overlayPoints: [] as Array<Record<string, unknown>>,
  runIoTIngest: jest.fn().mockResolvedValue({ status: "ingested", sensor_id: "sensor-atlas-01" }),
  runSatelliteIngest: jest.fn().mockResolvedValue({ status: "imagery_ingested", region: "north-sea" }),
  runAtlasGenerate: jest.fn().mockResolvedValue({ status: "generated" }),
  runAtlasExport: jest.fn().mockResolvedValue({ status: "exported", export_type: "pdf" }),
  loadLatestAtlas: jest.fn().mockResolvedValue({ status: "loaded" }),
  runMaintenanceSchedule: jest.fn().mockResolvedValue({ recommendation: "Routine check" })
};

jest.mock("../hooks/useIntelligence", () => ({
  useIntelligence: () => intelligenceMock
}));

describe("GlobalRiskAtlasPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    intelligenceMock.loading = false;
    intelligenceMock.error = null;
    intelligenceMock.history = {};
    intelligenceMock.overlayPoints = [];
  });

  it("renders pending statuses and executes atlas control actions", async () => {
    const user = userEvent.setup();
    render(<GlobalRiskAtlasPage />);

    expect(screen.getByText("Overlay points loaded: 0")).toBeInTheDocument();
    expect(screen.getByText("Atlas generation: pending")).toBeInTheDocument();
    expect(screen.getByTestId("atlas-map-mock")).toHaveTextContent("points:0");

    await user.type(screen.getByPlaceholderText("Tenant UUID"), "tenant-123");

    await user.click(screen.getByRole("button", { name: "Generate Atlas" }));
    expect(intelligenceMock.runAtlasGenerate).toHaveBeenCalledWith({
      tenant_id: "tenant-123",
      region: "north-sea",
      export_type: "map_snapshot"
    });

    await user.click(screen.getByRole("button", { name: "Load Latest Atlas" }));
    expect(intelligenceMock.loadLatestAtlas).toHaveBeenCalledWith("tenant-123", "north-sea");
  });

  it("shows transitioned status state when hook history updates", () => {
    intelligenceMock.history = {
      iot: { sensor_id: "sensor-atlas-01", status: "ingested" },
      satellite: { region: "north-sea", status: "imagery_ingested" },
      atlasGenerated: { status: "generated" },
      atlasExported: { status: "exported", export_type: "pdf" },
      atlasLatest: { region: "north-sea" },
      maintenance: { recommendation: "Immediate inspection" }
    };
    intelligenceMock.overlayPoints = [{ id: "p1" }, { id: "p2" }];

    render(<GlobalRiskAtlasPage />);

    expect(screen.getByText("IoT ingest: sensor-atlas-01 | ingested")).toBeInTheDocument();
    expect(screen.getByText("Satellite ingest: north-sea | imagery_ingested")).toBeInTheDocument();
    expect(screen.getByText("Atlas generation: generated")).toBeInTheDocument();
    expect(screen.getByText("Atlas export: pdf | exported")).toBeInTheDocument();
    expect(screen.getByText("Latest atlas cache: north-sea | loaded")).toBeInTheDocument();
    expect(screen.getByText("Overlay points loaded: 2")).toBeInTheDocument();
    expect(screen.getByText("Maintenance: Immediate inspection")).toBeInTheDocument();
    expect(screen.getByTestId("atlas-map-mock")).toHaveTextContent("points:2");
  });
});
