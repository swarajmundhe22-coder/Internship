import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import AdminGovernancePage from "../pages/admin/governance";

jest.mock("next/link", () => {
  return function MockLink({ href, children, ...props }: any) {
    const resolvedHref = typeof href === "string" ? href : href?.pathname ?? "";
    return <a href={resolvedHref} {...props}>{children}</a>;
  };
});

jest.mock("next/router", () => ({
  useRouter: () => ({
    query: {},
    isReady: true,
    pathname: "/admin/governance",
    push: jest.fn()
  })
}));

const useApiMock = {
  loading: false,
  error: null,
  apiError: null,
  generateDossier: jest.fn().mockResolvedValue({
    dossier_id: "dos-1",
    tenant_id: "tenant-1",
    simulation_id: "sim-1",
    format: "pdf",
    industry_module: "energy_grid",
    artifact_uri: "s3://dossiers/dos-1.pdf",
    status: "generated"
  }),
  exportDeck: jest.fn().mockResolvedValue({
    deck_id: "deck-1",
    tenant_id: "tenant-1",
    project_id: "proj-1",
    export_type: "pptx",
    artifact_uri: "s3://decks/deck-1.pptx",
    status: "exported"
  }),
  manageConsortium: jest.fn().mockResolvedValue({
    id: "cons-1",
    tenant_id: "tenant-1",
    tier: "global_utility",
    status: "active",
    created_at: "2026-03-16T00:00:00Z",
    updated_at: "2026-03-16T00:00:00Z"
  }),
  getConsortiumDashboard: jest.fn().mockResolvedValue({
    tenant_id: "tenant-1",
    tier: "global_utility",
    compliance_status: "compliant",
    foresight_index: 0.88,
    consortium_voting_enabled: true,
    active_dossiers_30d: 3,
    active_decks_30d: 2,
    generated_at: "2026-03-16T00:00:00Z"
  })
};

jest.mock("../hooks/useApi", () => ({
  useApi: () => useApiMock
}));

describe("AdminGovernancePage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("renders governance control sections", async () => {
    render(<AdminGovernancePage />);

    expect(await screen.findByText("Governance Command Surface")).toBeInTheDocument();
    expect(screen.getByText("Dossier Generation")).toBeInTheDocument();
    expect(screen.getByText("Investor Deck Export")).toBeInTheDocument();
    expect(screen.getByText("Consortium Membership")).toBeInTheDocument();
  });

  it("executes governance actions via typed hook methods", async () => {
    const user = userEvent.setup();
    render(<AdminGovernancePage />);

    const tenantInputs = screen.getAllByLabelText("Tenant ID");
    await user.type(tenantInputs[0], "tenant-1");
    await user.type(screen.getByLabelText("Simulation ID"), "sim-1");
    await user.type(screen.getByLabelText("Project ID"), "proj-1");

    await user.click(screen.getByRole("button", { name: "Generate Dossier" }));
    expect(useApiMock.generateDossier).toHaveBeenCalledWith({
      tenant_id: "tenant-1",
      simulation_id: "sim-1",
      format: "pdf",
      industry_module: "energy_grid"
    });

    await user.click(screen.getByRole("button", { name: "Export Deck" }));
    expect(useApiMock.exportDeck).toHaveBeenCalledWith({
      tenant_id: "tenant-1",
      project_id: "proj-1",
      export_type: "pptx"
    });

    await user.click(screen.getByRole("button", { name: "Apply Membership Action" }));
    expect(useApiMock.manageConsortium).toHaveBeenCalledWith({
      tenant_id: "tenant-1",
      action: "join"
    });

    await user.click(screen.getByRole("button", { name: "Load Dashboard" }));
    expect(useApiMock.getConsortiumDashboard).toHaveBeenCalledWith("tenant-1");

    expect(await screen.findByText("Governance Action Log")).toBeInTheDocument();
  });
});
