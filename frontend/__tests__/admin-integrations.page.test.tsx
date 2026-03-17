import { render, screen } from "@testing-library/react";

import AdminIntegrationsPage from "../pages/admin/integrations";

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
    pathname: "/admin/integrations",
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

describe("AdminIntegrationsPage", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    useApiMock.run.mockImplementation(async (path: string) => {
      if (path.startsWith("/integrations/api-tokens")) {
        return [];
      }
      if (path.startsWith("/integrations/webhooks")) {
        if (path.includes("deliveries")) {
          return { items: [], total: 0, page: 1, page_size: 25 };
        }
        return [];
      }
      return { items: [], total: 0, page: 1, page_size: 25 };
    });
  });

  it("renders enterprise integration management sections", async () => {
    render(<AdminIntegrationsPage />);

    expect(await screen.findByText("Enterprise Integrations")).toBeInTheDocument();
    expect(screen.getByText("API Tokens")).toBeInTheDocument();
    expect(screen.getByText("Report Webhooks")).toBeInTheDocument();
    expect(screen.getByText("Webhook Delivery Logs")).toBeInTheDocument();
  });
});
