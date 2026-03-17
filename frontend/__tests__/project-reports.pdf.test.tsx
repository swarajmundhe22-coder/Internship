import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ProjectReportsPage from "../pages/projects/[id]/reports";

jest.mock("next/link", () => {
  return function MockLink({ href, children, ...props }: any) {
    const resolvedHref = typeof href === "string" ? href : href?.pathname ?? "";
    return <a href={resolvedHref} {...props}>{children}</a>;
  };
});

jest.mock("next/router", () => ({
  useRouter: () => ({
    query: { id: "proj-1" },
    isReady: true,
    pathname: "/projects/[id]/reports",
    push: jest.fn()
  })
}));

jest.mock("../hooks/useUrlQueryState", () => ({
  useUrlQueryState: () => ({
    state: {
      page: "1",
      page_size: "10",
      simulation_id: "",
      risk_level: "",
      created_from: "",
      created_to: ""
    },
    setQuery: jest.fn(),
    isReady: true
  })
}));

const useApiMock = {
  run: jest.fn(),
  loading: false,
  error: null,
  downloadReportPdf: jest.fn()
};

jest.mock("../hooks/useApi", () => ({
  useApi: () => useApiMock
}));

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((res, rej) => {
    resolve = res;
    reject = rej;
  });
  return { promise, resolve, reject };
}

describe("ProjectReportsPage PDF button UX", () => {
  beforeEach(() => {
    jest.clearAllMocks();

    useApiMock.run.mockImplementation(async (path: string) => {
      if (path.includes("/reports")) {
        return {
          items: [
            {
              report_id: "r-1",
              report_uri: "https://example.test/report.html",
              simulation_id: "sim-1",
              material: "Steel",
              environment: "Marine",
              simulation_risk_level: "high",
              risk_level: "high",
              lifespan_years: 3.4,
              created_at: "2026-03-16T00:00:00.000Z"
            }
          ],
          total: 1,
          page: 1,
          page_size: 10
        };
      }

      return {
        id: "proj-1",
        name: "Rig A",
        created_at: "2026-03-16T00:00:00.000Z",
        simulations: { items: [], total: 0, page: 1, page_size: 1 }
      };
    });

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

  it("shows loading state during PDF generation and success feedback after completion", async () => {
    const pending = deferred<Blob>();
    useApiMock.downloadReportPdf.mockReturnValue(pending.promise);

    render(<ProjectReportsPage />);

    const button = await screen.findByRole("button", { name: "Download PDF" });
    await userEvent.click(button);

    expect(await screen.findByRole("button", { name: "Preparing PDF..." })).toBeDisabled();

    pending.resolve(new Blob(["pdf"], { type: "application/pdf" }));

    await waitFor(() => {
      expect(screen.getByText("PDF download started.")).toBeInTheDocument();
    });
  });

  it("surfaces an error message when PDF download fails", async () => {
    useApiMock.downloadReportPdf.mockRejectedValue(new Error("PDF engine unavailable"));

    render(<ProjectReportsPage />);

    const button = await screen.findByRole("button", { name: "Download PDF" });
    await userEvent.click(button);

    await waitFor(() => {
      expect(screen.getByText("PDF engine unavailable")).toBeInTheDocument();
    });
  });
});
