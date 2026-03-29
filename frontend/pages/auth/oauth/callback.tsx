import { useRouter } from "next/router";
import { useEffect, useMemo } from "react";

import { LOCAL_SOCIAL_PENDING_KEY, type LocalSocialPending } from "../../../utils/socialAuth";

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

    const url = typeof window !== "undefined" ? new URL(window.location.href) : null;
    const query = url?.searchParams;
    const hashParams = new URLSearchParams(url?.hash?.startsWith("#") ? url.hash.slice(1) : "");

    const readParam = (name: string): string => {
      const fromQuery = query?.get(name);
      if (typeof fromQuery === "string" && fromQuery.trim()) {
        return fromQuery;
      }
      const fromHash = hashParams.get(name);
      if (typeof fromHash === "string" && fromHash.trim()) {
        return fromHash;
      }
      const fromRouter = router.query[name];
      return typeof fromRouter === "string" ? fromRouter : "";
    };

    const accessToken = readParam("access_token");
    const refreshToken = readParam("refresh_token");
    const error = readParam("error");
    const errorDescription = readParam("error_description");
    const nextFromUrl = readParam("next");
    const resolvedNextPath = nextFromUrl || nextPath;

    const clearPendingLocalFallback = () => {
      if (typeof window === "undefined") {
        return;
      }
      window.sessionStorage.removeItem(LOCAL_SOCIAL_PENDING_KEY);
    };

    const readPendingLocalFallback = (): LocalSocialPending | null => {
      if (typeof window === "undefined") {
        return null;
      }

      const raw = window.sessionStorage.getItem(LOCAL_SOCIAL_PENDING_KEY);
      if (!raw) {
        return null;
      }

      try {
        const parsed = JSON.parse(raw) as LocalSocialPending;
        if (!parsed?.provider || !parsed?.email || !parsed?.externalSubject) {
          return null;
        }
        return parsed;
      } catch {
        return null;
      }
    };

    if (typeof window !== "undefined") {
      if (accessToken) {
        window.localStorage.setItem("onlooker_token", accessToken);
      }
      if (refreshToken) {
        window.localStorage.setItem("onlooker_refresh_token", refreshToken);
      }
    }

    if (accessToken) {
      clearPendingLocalFallback();
      void router.replace(resolvedNextPath);
      return;
    }

    if (!error && !errorDescription) {
      const pending = readPendingLocalFallback();
      if (pending && pending.attempts < 1 && typeof window !== "undefined") {
        const apiBase = (process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1").replace(/\/+$/, "");
        const callbackUrl = new URL(`${window.location.origin}/auth/oauth/callback`);
        callbackUrl.searchParams.set("next", pending.nextPath || resolvedNextPath);

        const retryUrl = new URL(`${apiBase}/auth/sso/local-fallback/start`);
        retryUrl.searchParams.set("provider", pending.provider);
        retryUrl.searchParams.set("email", pending.email);
        retryUrl.searchParams.set("external_subject", pending.externalSubject);
        retryUrl.searchParams.set("return_to", callbackUrl.toString());

        window.sessionStorage.setItem(
          LOCAL_SOCIAL_PENDING_KEY,
          JSON.stringify({ ...pending, attempts: pending.attempts + 1 })
        );
        window.location.assign(retryUrl.toString());
        return;
      }
    }

    clearPendingLocalFallback();

    const failureMessage = errorDescription || error || "OAuth callback missing token";
    void router.replace(`/auth/login?oauth_error=${encodeURIComponent(failureMessage)}`);
  }, [nextPath, router, router.isReady, router.query]);

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
