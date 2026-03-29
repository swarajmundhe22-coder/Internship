import { apiFetch } from "./api";
import type { AuthTokenResponse } from "../types/domain";

export type SocialProvider = "google" | "apple";

export type LocalSocialPending = {
  provider: SocialProvider;
  email: string;
  externalSubject: string;
  nextPath: string;
  attempts: number;
};

type SocialAuthOptions = {
  nextPath?: string;
  emailHint?: string;
};

type OAuthAuthorizePayload = {
  authorization_url?: string;
};

type HttpLikeError = {
  status?: number;
  detail?: string;
  message?: string;
};

type FirebaseLikeError = {
  code?: string;
  message?: string;
};

type GoogleFirebaseModule = {
  auth: import("firebase/auth").Auth;
  googleProvider: import("firebase/auth").GoogleAuthProvider;
  signInWithPopup: typeof import("firebase/auth").signInWithPopup;
  isFirebaseAuthConfigured?: () => boolean;
};

type SsoExchangePayload = {
  provider: SocialProvider;
  email: string;
  external_subject: string;
};

const PROVIDER_LABELS: Record<SocialProvider, string> = {
  google: "Google",
  apple: "Apple ID",
};

const LOCAL_FALLBACK_EMAIL_STORAGE_KEY = "onlooker_local_social_fallback_email";
export const LOCAL_SOCIAL_PENDING_KEY = "onlooker_local_social_pending_v1";

function isValidEmailAddress(value: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
}

function getFirebaseErrorCode(error: unknown): string {
  if (!error || typeof error !== "object") {
    return "";
  }

  const candidate = error as FirebaseLikeError;
  return candidate.code?.toLowerCase() ?? "";
}

function isFirebaseUnauthorizedDomain(error: unknown): boolean {
  if (getFirebaseErrorCode(error) === "auth/unauthorized-domain") {
    return true;
  }

  if (!error || typeof error !== "object") {
    return false;
  }

  const candidate = error as FirebaseLikeError;
  const message = candidate.message?.toLowerCase() ?? "";
  return message.includes("auth/unauthorized-domain") || message.includes("unauthorized-domain");
}

function isFirebasePopupDismissed(error: unknown): boolean {
  const code = getFirebaseErrorCode(error);
  return code === "auth/popup-closed-by-user" || code === "auth/cancelled-popup-request";
}

function isFirebaseConfigurationError(error: unknown): boolean {
  const code = getFirebaseErrorCode(error);
  if (
    code === "auth/configuration-not-found" ||
    code === "auth/operation-not-allowed" ||
    code === "auth/operation-not-supported-in-this-environment" ||
    code === "auth/invalid-api-key"
  ) {
    return true;
  }

  if (!error || typeof error !== "object") {
    return false;
  }

  const message = (error as FirebaseLikeError).message?.toLowerCase() ?? "";
  return (
    message.includes("configuration-not-found") ||
    message.includes("operation-not-allowed") ||
    message.includes("operation-not-supported-in-this-environment") ||
    message.includes("invalid api key")
  );
}

function isLocalDevelopmentHost(): boolean {
  if (typeof window === "undefined") {
    return false;
  }

  const host = window.location.hostname;
  return host === "localhost" || host === "127.0.0.1" || host === "::1";
}

function isLocalSocialFallbackEnabled(): boolean {
  const value = process.env.NEXT_PUBLIC_ENABLE_LOCAL_SOCIAL_FALLBACK ?? "false";
  return value.trim().toLowerCase() === "true";
}

function normalizeEmailHint(emailHint?: string): string | null {
  const value = emailHint?.trim().toLowerCase();
  if (!value || !isValidEmailAddress(value)) {
    return null;
  }

  return value;
}

function providerLabel(provider: SocialProvider): string {
  return PROVIDER_LABELS[provider] ?? provider;
}

function persistLocalSocialPending(pending: LocalSocialPending): void {
  if (typeof window === "undefined") {
    return;
  }

  window.sessionStorage.setItem(LOCAL_SOCIAL_PENDING_KEY, JSON.stringify(pending));
}

async function exchangeSsoToken(payload: SsoExchangePayload, nextPath: string): Promise<void> {
  const token = await apiFetch<AuthTokenResponse>("/auth/sso/exchange", {
    method: "POST",
    body: JSON.stringify(payload),
  });

  window.localStorage.setItem("onlooker_token", token.access_token);
  if (token.refresh_token) {
    window.localStorage.setItem("onlooker_refresh_token", token.refresh_token);
  }

  window.location.assign(nextPath);
}

function resolveLocalFallbackEmail(provider: SocialProvider, emailHint?: string): string {
  const fromHint = normalizeEmailHint(emailHint);
  if (fromHint) {
    window.localStorage.setItem(LOCAL_FALLBACK_EMAIL_STORAGE_KEY, fromHint);
    return fromHint;
  }

  const cached = normalizeEmailHint(window.localStorage.getItem(LOCAL_FALLBACK_EMAIL_STORAGE_KEY) ?? undefined);
  if (cached) {
    return cached;
  }

  const generated = `local-${provider}-${Date.now().toString(36)}@onlooker.local`;
  window.localStorage.setItem(LOCAL_FALLBACK_EMAIL_STORAGE_KEY, generated);
  return generated;
}

async function tryLocalProviderSsoExchange(provider: SocialProvider, nextPath: string, emailHint?: string): Promise<void> {
  const email = resolveLocalFallbackEmail(provider, emailHint);
  const externalSubject = `${provider}-local-${email}-${Date.now().toString(36)}`;

  try {
    await exchangeSsoToken(
      {
        provider,
        email,
        external_subject: externalSubject,
      },
      nextPath
    );
    return;
  } catch {
    // Fallback to redirect mode if direct browser exchange fails in this environment.
    persistLocalSocialPending({
      provider,
      email,
      externalSubject,
      nextPath,
      attempts: 0,
    });

    const fallbackUrl = new URL(`${resolveApiBase()}/auth/sso/local-fallback/start`);
    fallbackUrl.searchParams.set("provider", provider);
    fallbackUrl.searchParams.set("email", email);
    fallbackUrl.searchParams.set("external_subject", externalSubject);
    fallbackUrl.searchParams.set("return_to", buildFrontendOAuthCallback(nextPath));
    window.location.assign(fallbackUrl.toString());
  }
}

function resolveApiBase(): string {
  const configured = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";
  return configured.replace(/\/+$/, "");
}

function buildFrontendOAuthCallback(nextPath: string): string {
  const callbackUrl = new URL(`${window.location.origin}/auth/oauth/callback`);
  callbackUrl.searchParams.set("next", nextPath);
  return callbackUrl.toString();
}

function isNotFoundError(error: unknown): boolean {
  if (!error || typeof error !== "object") {
    return false;
  }

  const candidate = error as HttpLikeError;
  return candidate.status === 404 || candidate.status === 405;
}

function extractErrorText(raw: string): string {
  const value = raw.trim();
  if (!value) {
    return "";
  }

  try {
    const parsed = JSON.parse(value) as { detail?: unknown; message?: unknown };
    if (typeof parsed.detail === "string" && parsed.detail.trim()) {
      return parsed.detail.trim();
    }
    if (typeof parsed.message === "string" && parsed.message.trim()) {
      return parsed.message.trim();
    }
  } catch {
    // Ignore JSON parse failures and return raw text.
  }

  return value;
}

function extractHttpErrorMessage(error: unknown): string {
  if (!error || typeof error !== "object") {
    return "";
  }

  const candidate = error as HttpLikeError;
  if (typeof candidate.detail === "string" && candidate.detail.trim()) {
    return extractErrorText(candidate.detail);
  }

  if (typeof candidate.message === "string" && candidate.message.trim()) {
    return extractErrorText(candidate.message);
  }

  return "";
}

function isHostedOAuthProviderNotConfigured(error: unknown): boolean {
  if (!error || typeof error !== "object") {
    return false;
  }

  const candidate = error as HttpLikeError;
  const detail = extractHttpErrorMessage(error).toLowerCase();
  return candidate.status === 503 && detail.includes("oauth provider is not configured");
}

function deriveErrorMessage(error: unknown): string {
  if (isFirebaseUnauthorizedDomain(error)) {
    return "Social popup is blocked for this domain. Add this host in Firebase Console Authentication > Settings > Authorized domains.";
  }

  if (isFirebasePopupDismissed(error)) {
    return "Google sign-in was cancelled.";
  }

  if (getFirebaseErrorCode(error) === "auth/popup-blocked") {
    return "Your browser blocked the Google sign-in popup. Allow popups for this site and try again.";
  }

  if (isFirebaseConfigurationError(error)) {
    return "Google sign-in is not configured. Update Firebase credentials and enable the Google provider in Firebase Console.";
  }

  if (isHostedOAuthProviderNotConfigured(error)) {
    return "Hosted OAuth is not configured on this backend. Configure backend OAUTH provider credentials, or set NEXT_PUBLIC_ENABLE_LOCAL_SOCIAL_FALLBACK=true for local development.";
  }

  const httpMessage = extractHttpErrorMessage(error);
  if (httpMessage) {
    return httpMessage;
  }

  if (error instanceof Error && error.message.trim()) {
    return error.message;
  }

  if (error && typeof error === "object") {
    const candidate = error as HttpLikeError;
    if (typeof candidate.detail === "string" && candidate.detail.trim()) {
      return candidate.detail;
    }
    if (typeof candidate.message === "string" && candidate.message.trim()) {
      return candidate.message;
    }
  }

  return "Unable to start social sign-in";
}

function buildCallbackAndParams(options: SocialAuthOptions): { nextPath: string; params: URLSearchParams } {
  const nextPath = "/";
  const callbackUrl = new URL(`${window.location.origin}/auth/oauth/callback`);
  callbackUrl.searchParams.set("next", nextPath);

  const params = new URLSearchParams();
  params.set("return_to", callbackUrl.toString());

  const normalizedHint = options.emailHint?.trim();
  if (normalizedHint) {
    params.set("login_hint", normalizedHint);
  }

  return { nextPath, params };
}

async function tryGoogleSsoExchange(nextPath: string, emailHint?: string): Promise<void> {
  const { auth, googleProvider, signInWithPopup, isFirebaseAuthConfigured } =
    (await import("../components/outsource/local-simulated/firebase")) as GoogleFirebaseModule;

  if (typeof isFirebaseAuthConfigured === "function" && !isFirebaseAuthConfigured()) {
    const configError = new Error("Firebase Google Auth is not configured") as Error & { code?: string };
    configError.code = "auth/configuration-not-found";
    throw configError;
  }

  const trimmedHint = emailHint?.trim();
  if (trimmedHint) {
    googleProvider.setCustomParameters({ login_hint: trimmedHint, prompt: "select_account" });
  } else {
    googleProvider.setCustomParameters({ prompt: "select_account" });
  }

  const popupResult = await signInWithPopup(auth, googleProvider);
  const email = popupResult.user.email?.trim().toLowerCase();
  const externalSubject = popupResult.user.uid?.trim();

  if (!email || !externalSubject) {
    throw new Error("Google identity did not return required account details");
  }

  await exchangeSsoToken(
    {
      provider: "google",
      email,
      external_subject: externalSubject,
    },
    nextPath
  );
}

async function tryLocalProviderFallback(
  provider: SocialProvider,
  nextPath: string,
  emailHint?: string
): Promise<void> {
  try {
    await tryLocalProviderSsoExchange(provider, nextPath, emailHint);
  } catch (fallbackError) {
    const label = providerLabel(provider);
    throw new Error(`${label} local fallback failed: ${deriveErrorMessage(fallbackError)}`);
  }
}

export async function beginSocialAuth(provider: SocialProvider, options: SocialAuthOptions = {}): Promise<void> {
  if (typeof window === "undefined") {
    return;
  }

  const { nextPath, params } = buildCallbackAndParams(options);
  let startupError: unknown = null;
  const canUseLocalFallback = isLocalDevelopmentHost() && isLocalSocialFallbackEnabled();

  if (provider === "google") {
    try {
      await tryGoogleSsoExchange(nextPath, options.emailHint);
      return;
    } catch (error) {
      startupError = error;

      // User-cancelled and domain-auth issues should be surfaced directly.
      if (isFirebasePopupDismissed(error) || isFirebaseUnauthorizedDomain(error)) {
        throw new Error(deriveErrorMessage(error));
      }

      // For Firebase setup/runtime issues, continue to backend-hosted OAuth fallback.
      if (!isFirebaseConfigurationError(error)) {
        throw new Error(deriveErrorMessage(error));
      }
    }
  }

  try {
    const payload = await apiFetch<OAuthAuthorizePayload>(`/auth/oauth/${provider}/authorize?${params.toString()}`);
    if (!payload.authorization_url) {
      throw new Error("OAuth provider did not return an authorization URL");
    }
    window.location.assign(payload.authorization_url);
    return;
  } catch (error) {
    startupError = error;

    const shouldUseLocalFallback =
      canUseLocalFallback ||
      (isLocalDevelopmentHost() && isHostedOAuthProviderNotConfigured(error));

    if (!isNotFoundError(error)) {
      if (shouldUseLocalFallback) {
        await tryLocalProviderFallback(provider, nextPath, options.emailHint);
        return;
      }

      throw new Error(deriveErrorMessage(error));
    }
  }

  try {
    // Legacy fallback for deployments that only expose direct start redirect routes.
    const fallbackUrl = new URL(`${resolveApiBase()}/auth/oauth/${provider}/start`);
    fallbackUrl.search = params.toString();
    window.location.assign(fallbackUrl.toString());
  } catch {
    if (canUseLocalFallback) {
      await tryLocalProviderFallback(provider, nextPath, options.emailHint);
      return;
    }

    throw new Error(deriveErrorMessage(startupError));
  }
}