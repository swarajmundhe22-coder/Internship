import { render, waitFor } from "@testing-library/react";

import OAuthCallbackPage from "../pages/auth/oauth/callback";

const replaceMock = jest.fn();

jest.mock("next/router", () => ({
  useRouter: () => ({
    isReady: true,
    query: {},
    replace: replaceMock,
  }),
}));

describe("OAuth callback page", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    window.localStorage.clear();
    window.sessionStorage.clear();
    window.history.pushState({}, "", "/auth/oauth/callback");
  });

  it("stores query tokens and redirects web flow", async () => {
    window.history.pushState(
      {},
      "",
      "/auth/oauth/callback?access_token=query-access&refresh_token=query-refresh&next=%2Fdashboard"
    );

    render(<OAuthCallbackPage />);

    await waitFor(() => {
      expect(replaceMock).toHaveBeenCalledWith("/dashboard");
    });

    expect(window.localStorage.getItem("onlooker_token")).toBe("query-access");
    expect(window.localStorage.getItem("onlooker_refresh_token")).toBe("query-refresh");
  });

  it("stores hash tokens and redirects mobile flow", async () => {
    window.history.pushState(
      {},
      "",
      "/auth/oauth/callback#access_token=hash-access&refresh_token=hash-refresh&next=%2Fprojects%2F42"
    );

    render(<OAuthCallbackPage />);

    await waitFor(() => {
      expect(replaceMock).toHaveBeenCalledWith("/projects/42");
    });

    expect(window.localStorage.getItem("onlooker_token")).toBe("hash-access");
    expect(window.localStorage.getItem("onlooker_refresh_token")).toBe("hash-refresh");
  });

  it("forwards oauth error code to login route", async () => {
    window.history.pushState(
      {},
      "",
      "/auth/oauth/callback?error=oauth_invalid_grant&oauth_error_code=oauth_invalid_grant&error_description=Grant%20revoked"
    );

    render(<OAuthCallbackPage />);

    await waitFor(() => {
      expect(replaceMock).toHaveBeenCalled();
    });

    const redirectTarget = String(replaceMock.mock.calls[0][0]);
    expect(redirectTarget).toContain("/auth/login?");
    expect(redirectTarget).toContain("oauth_error=Grant+revoked");
    expect(redirectTarget).toContain("oauth_error_code=oauth_invalid_grant");
  });

  it("uses existing local token when callback url no longer has tokens", async () => {
    window.localStorage.setItem("onlooker_token", "existing-token");
    window.history.pushState({}, "", "/auth/oauth/callback?next=%2F");

    render(<OAuthCallbackPage />);

    await waitFor(() => {
      expect(replaceMock).toHaveBeenCalledWith("/");
    });

    const firstRedirect = String(replaceMock.mock.calls[0][0]);
    expect(firstRedirect.startsWith("/auth/login?")).toBe(false);
  });
});
