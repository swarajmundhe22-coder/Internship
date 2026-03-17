import { useRouter } from "next/router";
import { useEffect, useMemo } from "react";

export default function OAuthCallbackPage() {
  const router = useRouter();

  const nextPath = useMemo(() => {
    const value = router.query.next;
    if (typeof value === "string" && value.trim()) {
      return value;
    }
    return "/projects";
  }, [router.query.next]);

  useEffect(() => {
    if (!router.isReady) {
      return;
    }

    const accessToken = typeof router.query.access_token === "string" ? router.query.access_token : "";
    const refreshToken = typeof router.query.refresh_token === "string" ? router.query.refresh_token : "";
    const error = typeof router.query.error === "string" ? router.query.error : "";
    const errorDescription = typeof router.query.error_description === "string" ? router.query.error_description : "";

    if (typeof window !== "undefined") {
      if (accessToken) {
        window.localStorage.setItem("onlooker_token", accessToken);
      }
      if (refreshToken) {
        window.localStorage.setItem("onlooker_refresh_token", refreshToken);
      }
    }

    if (accessToken) {
      void router.replace(nextPath);
      return;
    }

    const failureMessage = errorDescription || error || "OAuth sign-in failed";
    void router.replace(`/auth/login?oauth_error=${encodeURIComponent(failureMessage)}`);
  }, [nextPath, router, router.isReady, router.query.access_token, router.query.error, router.query.error_description, router.query.refresh_token]);

  return (
    <div className="outsource-home min-h-screen flex items-center justify-center" style={{ background: "#050508", color: "#f0f0f5" }}>
      <div className="rounded-lg border border-white/15 bg-white/5 px-6 py-5 text-center">
        <p className="section-number">OAuth Callback</p>
        <h1 className="mt-2 text-xl font-semibold">Finalizing secure sign-in...</h1>
        <p className="mt-2 text-sm text-white/70">Please wait while we complete your authentication session.</p>
      </div>
    </div>
  );
}
