import Link from "next/link";
import { FormEvent, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/router";
import { motion } from "framer-motion";
import { Activity, Eye, EyeOff, Lock, Mail, Shield, Zap } from "lucide-react";

import { CinematicAuthBackdrop } from "../../components/auth/CinematicAuthBackdrop";
import { useApi } from "../../hooks/useApi";
import { AuthTokenResponse, RegistrationOtpChallengeResponse } from "../../types/domain";
import { beginSocialAuth, type SocialProvider } from "../../utils/socialAuth";

const OAUTH_ERROR_CODE_MESSAGES: Record<string, string> = {
  oauth_provider_not_configured: "Google OAuth is not configured on the server. Verify client ID, client secret, and redirect URI in deployment settings.",
  oauth_state_missing: "OAuth state was missing. Retry sign-in from the login page.",
  oauth_state_invalid: "OAuth state validation failed. Retry sign-in and ensure only one login tab is active.",
  oauth_state_provider_mismatch: "OAuth provider mismatch detected. Restart sign-in with the same provider.",
  oauth_nonce_mismatch: "Security nonce check failed during OAuth callback. Retry sign-in.",
  oauth_invalid_grant: "Google rejected the authorization code (expired or revoked grant). Retry sign-in.",
  oauth_invalid_client: "Google OAuth client credentials are invalid. Verify production client configuration.",
  oauth_token_timeout: "Google token exchange timed out. Check network connectivity and retry.",
  oauth_token_network_error: "Google token exchange failed due to a network error. Retry shortly.",
  oauth_google_userinfo_failed: "Unable to fetch your Google profile. Verify granted scopes include openid email profile.",
  oauth_identity_missing: "OAuth response did not include required identity claims.",
};

export default function LoginPage() {
  const router = useRouter();
  const { run, loading, error } = useApi();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [otp, setOtp] = useState("");
  const [otpRequested, setOtpRequested] = useState(false);
  const [otpMessage, setOtpMessage] = useState<string | null>(null);
  const [devOtp, setDevOtp] = useState<string | null>(null);
  const [socialError, setSocialError] = useState<string | null>(null);
  const [socialProviderLoading, setSocialProviderLoading] = useState<SocialProvider | null>(null);
  const oauthError = typeof router.query.oauth_error === "string" ? router.query.oauth_error : null;
  const oauthErrorCode = typeof router.query.oauth_error_code === "string" ? router.query.oauth_error_code : null;
  const mappedOauthError = oauthErrorCode ? OAUTH_ERROR_CODE_MESSAGES[oauthErrorCode] ?? null : null;
  const visibleSocialError =
    socialError ?? mappedOauthError ?? (oauthError === "OAuth sign-in failed" ? "OAuth callback missing token" : oauthError);
  const resolvedNextPath = useMemo(() => {
    const candidate = typeof router.query.next === "string" ? router.query.next : "";
    if (candidate.startsWith("/")) {
      return candidate;
    }
    return "/";
  }, [router.query.next]);

  useEffect(() => {
    if (!router.isReady || typeof window === "undefined") {
      return;
    }

    const existingToken = window.localStorage.getItem("onlooker_token");
    if (existingToken) {
      void router.replace(resolvedNextPath);
    }
  }, [resolvedNextPath, router, router.isReady]);

  async function completeLogin(token: AuthTokenResponse): Promise<void> {
    if (typeof window !== "undefined") {
      window.localStorage.setItem("onlooker_token", token.access_token);
    }
    await router.push(resolvedNextPath);
  }

  async function requestOtp(): Promise<void> {
    const challenge = await run<RegistrationOtpChallengeResponse>("/auth/login/request-otp", {
      method: "POST",
      body: JSON.stringify({ email, password })
    });

    setOtpRequested(true);
    setOtpMessage(`${challenge.message}. Code expires in ${Math.floor(challenge.expires_in_seconds / 60)} minutes.`);
    setDevOtp(challenge.dev_otp ?? null);
  }

  async function verifyOtpAndLogin(): Promise<void> {
    const token = await run<AuthTokenResponse>("/auth/login/verify-otp", {
      method: "POST",
      body: JSON.stringify({ email, otp })
    });

    await completeLogin(token);
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    if (!otpRequested) {
      await requestOtp();
      return;
    }

    await verifyOtpAndLogin();
  }

  async function signInWith(provider: SocialProvider): Promise<void> {
    setSocialError(null);
    setSocialProviderLoading(provider);

    if (typeof router.query.oauth_error === "string") {
      void router.replace("/auth/login", undefined, { shallow: true });
    }

    try {
      await beginSocialAuth(provider, {
        nextPath: resolvedNextPath,
        emailHint: email,
      });
    } catch (socialStartError) {
      console.error("Unable to start social sign-in", socialStartError);
      const socialMessage =
        socialStartError instanceof Error && socialStartError.message
          ? socialStartError.message
          : "Social sign-in is unavailable right now. Please use OTP sign-in or try again later.";
      setSocialError(socialMessage);
    } finally {
      setSocialProviderLoading(null);
    }
  }

  return (
    <div className="relative min-h-screen overflow-hidden bg-black text-slate-100">
      <CinematicAuthBackdrop tone="purple" />

      <div className="relative z-10 flex min-h-screen items-center justify-center px-4 py-8 sm:px-6">
        <motion.section
          initial={{ opacity: 0, y: 22, scale: 0.98, filter: "blur(8px)" }}
          animate={{ opacity: 1, y: 0, scale: 1, filter: "blur(0px)" }}
          transition={{ duration: 0.55, ease: [0.16, 1, 0.3, 1] }}
          className="relative w-full max-w-xl overflow-hidden rounded-3xl border border-violet-400/30 bg-gradient-to-br from-black/90 via-violet-950/45 to-black/92 p-6 shadow-[0_35px_90px_rgba(0,0,0,0.58)] backdrop-blur-2xl sm:p-8"
        >
          <motion.div
            className="pointer-events-none absolute inset-0 bg-gradient-to-b from-violet-400/20 to-transparent"
            animate={{ y: ["-120%", "180%"] }}
            transition={{ duration: 3.4, repeat: Infinity, ease: "linear" }}
          />

          <div className="pointer-events-none absolute inset-0 opacity-10">
            <div
              className="h-full w-full"
              style={{
                backgroundImage:
                  "linear-gradient(rgba(168,85,247,0.5) 1px, transparent 1px), linear-gradient(90deg, rgba(168,85,247,0.5) 1px, transparent 1px)",
                backgroundSize: "30px 30px"
              }}
            />
          </div>

          <div className="relative z-10">
            <div className="mb-7 text-center">
              <motion.div
                className="mb-4 flex items-center justify-center gap-3"
                animate={{ rotate: [0, 4, 0, -4, 0] }}
                transition={{ duration: 5, repeat: Infinity }}
              >
                <Zap className="h-7 w-7 text-violet-300" fill="currentColor" />
                <span className="h-px w-14 bg-gradient-to-r from-transparent via-violet-400/80 to-transparent" />
                <Activity className="h-6 w-6 text-fuchsia-300" />
              </motion.div>

              <p className="text-xs font-semibold uppercase tracking-[0.34em] text-violet-200/80">The On Lookers</p>
              <h1 className="mt-3 bg-gradient-to-b from-white via-violet-100 to-violet-300 bg-clip-text text-4xl font-black tracking-[0.11em] text-transparent sm:text-5xl">
                WELCOME BACK
              </h1>
              <p className="mt-3 font-mono text-xs tracking-[0.28em] text-violet-300/80">&gt; ENTER THE SYSTEM_</p>
            </div>

            <form onSubmit={(event) => void submit(event)} className="space-y-4">
              <div className="relative">
                <Mail className="pointer-events-none absolute left-4 top-1/2 z-10 h-5 w-5 -translate-y-1/2 text-violet-300" />
                <input
                  className="h-14 w-full rounded-xl border border-violet-300/30 bg-black/60 pl-12 pr-4 font-mono tracking-[0.13em] text-white placeholder:text-violet-300/40 focus:border-violet-300 focus:bg-black/80 focus:outline-none focus:ring-2 focus:ring-violet-300/20"
                  type="email"
                  placeholder="NEURAL ID"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  required
                  autoComplete="email"
                  aria-label="Email"
                />
              </div>

              <div className="relative">
                <Lock className="pointer-events-none absolute left-4 top-1/2 z-10 h-5 w-5 -translate-y-1/2 text-violet-300" />
                <input
                  className="h-14 w-full rounded-xl border border-violet-300/30 bg-black/60 pl-12 pr-14 font-mono tracking-[0.13em] text-white placeholder:text-violet-300/40 focus:border-violet-300 focus:bg-black/80 focus:outline-none focus:ring-2 focus:ring-violet-300/20"
                  type={showPassword ? "text" : "password"}
                  placeholder="ACCESS CODE"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  required
                  minLength={8}
                  autoComplete="current-password"
                  aria-label="Password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword((prev) => !prev)}
                  className="absolute right-4 top-1/2 z-10 -translate-y-1/2 text-violet-300 transition hover:scale-110 hover:text-violet-200"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
                </button>
              </div>

              {otpRequested ? (
                <div className="relative">
                  <Shield className="pointer-events-none absolute left-4 top-1/2 z-10 h-5 w-5 -translate-y-1/2 text-violet-300" />
                  <input
                    className="h-14 w-full rounded-xl border border-violet-300/30 bg-black/60 pl-12 pr-4 font-mono tracking-[0.2em] text-white placeholder:text-violet-300/40 focus:border-violet-300 focus:bg-black/80 focus:outline-none focus:ring-2 focus:ring-violet-300/20"
                    type="text"
                    inputMode="numeric"
                    pattern="[0-9]{6}"
                    maxLength={6}
                    placeholder="OTP CODE"
                    value={otp}
                    onChange={(event) => setOtp(event.target.value.replace(/\D/g, "").slice(0, 6))}
                    required
                    aria-label="One-time password"
                  />
                </div>
              ) : null}

              <button
                type="submit"
                disabled={loading}
                className="h-14 w-full rounded-xl border border-violet-300/50 bg-gradient-to-r from-violet-500/40 via-fuchsia-500/35 to-violet-500/40 font-semibold uppercase tracking-[0.18em] text-white shadow-[0_0_0_1px_rgba(168,85,247,0.3),0_18px_34px_rgba(168,85,247,0.25)] transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-65"
              >
                {loading ? "Processing" : otpRequested ? "Verify OTP and Sign In" : "Authenticate"}
              </button>

              {otpRequested ? (
                <button
                  type="button"
                  disabled={loading}
                  onClick={() => {
                    void requestOtp();
                  }}
                  className="h-12 w-full rounded-xl border border-violet-300/30 bg-black/35 font-medium uppercase tracking-[0.12em] text-violet-100 transition hover:border-violet-300/60 disabled:cursor-not-allowed disabled:opacity-65"
                >
                  Resend OTP
                </button>
              ) : null}
            </form>

            {error ? <p className="mt-3 text-sm text-red-300">{error}</p> : null}
            {otpMessage ? <p className="mt-3 text-sm text-violet-100/90">{otpMessage}</p> : null}
            {process.env.NODE_ENV !== "production" && devOtp ? <p className="mt-2 text-xs text-violet-200/70">Dev OTP: {devOtp}</p> : null}

            <div className="mt-6 border-t border-violet-300/20 pt-5">
              <p className="text-center text-xs uppercase tracking-[0.2em] text-violet-200/70">Social Access</p>
              <div className="mt-3 grid gap-2 sm:grid-cols-2">
                <button
                  type="button"
                  disabled={loading || socialProviderLoading !== null}
                  onClick={() => {
                    void signInWith("google");
                  }}
                  className="h-11 rounded-xl border border-violet-300/30 bg-black/35 text-sm font-semibold text-violet-100 transition hover:border-violet-200/70"
                >
                  {socialProviderLoading === "google" ? "Connecting..." : "Continue with Google"}
                </button>
                <button
                  type="button"
                  disabled={loading || socialProviderLoading !== null}
                  onClick={() => {
                    void signInWith("apple");
                  }}
                  className="h-11 rounded-xl border border-violet-300/30 bg-black/35 text-sm font-semibold text-violet-100 transition hover:border-violet-200/70"
                >
                  {socialProviderLoading === "apple" ? "Connecting..." : "Continue with Apple ID"}
                </button>
              </div>
              {visibleSocialError ? <p className="mt-3 text-sm text-amber-200">{visibleSocialError}</p> : null}
            </div>

            <p className="mt-5 text-center text-sm text-violet-100/80">
              New operator?{" "}
              <Link href="/auth/register" className="font-semibold text-violet-200 hover:text-white">
                Initialize Access
              </Link>
            </p>
          </div>
        </motion.section>
      </div>
    </div>
  );
}
