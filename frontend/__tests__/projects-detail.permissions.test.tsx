import { render, screen, waitFor } from "@testing-library/react";
import ProjectDetailPage from "../pages/projects/[id]";

const pushMock = jest.fn();

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
    pathname: "/projects/[id]",
    push: pushMock
  })
}));

jest.mock("../hooks/useUrlQueryState", () => ({
  useUrlQueryState: () => ({
    state: {
      page: "1",
      page_size: "10",
      material_id: "",
      environment_id: "",
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
  getProjectCollaborators: jest.fn(),
  addProjectCollaborator: jest.fn(),
  updateProjectCollaborator: jest.fn(),
  deleteProjectCollaborator: jest.fn()
};

jest.mock("../hooks/useApi", () => ({
  useApi: () => useApiMock
}));

describe("ProjectDetailPage collaborator permissions", () => {
  beforeEach(() => {
    jest.clearAllMocks();

    const token = `header.${window.btoa(JSON.stringify({ sub: "viewer-user" }))}.signature`;
    window.localStorage.setItem("onlooker_token", token);

    useApiMock.run.mockImplementation(async (path: string) => {
      if (path.startsWith("/projects/proj-1")) {
        return {
          id: "proj-1",
          name: "Rig A",
          created_at: "2026-03-16T00:00:00.000Z",
          simulations: {
            items: [
              {
                simulation_id: "sim-1",
                material: "Steel",
                environment: "Marine",
                risk_level: "high",
                lifespan_years: 3.2,
                created_at: "2026-03-15T00:00:00.000Z"
              }
            ],
            total: 1,
            page: 1,
            page_size: 10
          }
        };
      }

      if (path.startsWith("/materials")) {
        return { items: [], total: 0, page: 1, page_size: 200 };
      }

      if (path.startsWith("/environment")) {
        return { items: [], total: 0, page: 1, page_size: 200 };
      }

      throw new Error(`Unexpected path: ${path}`);
    });

    useApiMock.getProjectCollaborators.mockResolvedValue([
      {
        user_id: "viewer-user",
        email: "viewer@onlooker.ai",
        role: "Viewer",
        joined_at: "2026-03-01T00:00:00.000Z"
      }
    ]);
  });

  it("hides owner-only collaborator controls and disables project actions for Viewer role", async () => {
    render(<ProjectDetailPage />);

    await screen.findByText("Read-only collaborator access");
    expect(screen.queryByRole("button", { name: "Add Collaborator" })).not.toBeInTheDocument();

    await waitFor(() => {
      const openSimulation = screen.getByRole("link", { name: "Open Simulation" });
      expect(openSimulation).toHaveAttribute("aria-disabled", "true");
    });
  });
});
