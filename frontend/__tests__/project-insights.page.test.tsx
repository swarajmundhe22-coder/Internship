import { render, screen } from "@testing-library/react";

import ProjectInsightsPage from "../pages/projects/[id]/insights";

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
    pathname: "/projects/[id]/insights",
    push: jest.fn()
  })
}));

const useApiMock = {
  run: jest.fn(),
  loading: false,
  error: null
};

jest.mock("../hooks/useApi", () => ({
  useApi: () => useApiMock
}));

describe("ProjectInsightsPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    useApiMock.run.mockResolvedValue({
      project_id: "proj-1",
      generated_at: "2026-03-16T00:00:00Z",
      summary: "AI summary",
      recommendations: ["Inspect offshore segment"],
      anomalies: [{ code: "RISK_SPIKE", severity: "critical", message: "Rapid escalation" }]
    });
  });

  it("renders insight HUD content", async () => {
    render(<ProjectInsightsPage />);

    expect(await screen.findByText("AI Risk Summary")).toBeInTheDocument();
    expect(screen.getByText("AI summary")).toBeInTheDocument();
    expect(screen.getByText("Inspect offshore segment")).toBeInTheDocument();
    expect(screen.getByText("RISK_SPIKE")).toBeInTheDocument();
  });
});
