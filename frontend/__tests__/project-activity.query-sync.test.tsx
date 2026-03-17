import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ProjectActivityPage from "../pages/projects/[id]/activity";

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
    pathname: "/projects/[id]/activity",
    push: pushMock
  })
}));

const useApiMock = {
  getProjectActivity: jest.fn(),
  loading: false,
  error: null
};

jest.mock("../hooks/useApi", () => ({
  useApi: () => useApiMock
}));

describe("ProjectActivityPage query sync", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    useApiMock.getProjectActivity.mockResolvedValue([]);
  });

  it("pushes URL query updates when action filter changes", async () => {
    render(<ProjectActivityPage />);

    const actionSelect = await screen.findByLabelText("Action");
    await userEvent.selectOptions(actionSelect, "collaborator_added");

    await waitFor(() => {
      expect(pushMock).toHaveBeenCalled();
    });

    const hadActionUpdate = pushMock.mock.calls.some((call) => {
      const payload = call[0];
      return payload?.query?.action === "collaborator_added";
    });

    expect(hadActionUpdate).toBe(true);
  });
});
