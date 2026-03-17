import { useEffect, useState } from "react";

type SocialProvider = "google" | "apple";

type SocialSignInPanelProps = {
  email?: string;
  redirectTo?: string;
  onSuccess?: (provider: SocialProvider) => void;
};

export default function SocialSignInPanel({ email, redirectTo, onSuccess }: SocialSignInPanelProps) {
  const [socialEmail, setSocialEmail] = useState(email ?? "");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setSocialEmail(email ?? "");
  }, [email]);

  async function signInWith(provider: SocialProvider): Promise<void> {
    setLoading(true);
    setError(null);
    onSuccess?.(provider);

    if (typeof window === "undefined") {
      setLoading(false);
      return;
    }

    const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";
    const callbackUrl = new URL(`${window.location.origin}/auth/oauth/callback`);
    if (redirectTo) {
      callbackUrl.searchParams.set("next", redirectTo);
    }

    const authorizeUrl = new URL(`${apiBase}/auth/oauth/${provider}/start`);
    authorizeUrl.searchParams.set("return_to", callbackUrl.toString());
    if (socialEmail.trim()) {
      authorizeUrl.searchParams.set("login_hint", socialEmail.trim());
    }

    window.location.assign(authorizeUrl.toString());
  }

  return (
    <div className="mt-4 rounded-md border border-white/15 bg-white/5 p-3">
      <p className="section-number">Social Sign In</p>
      <p className="mt-1 text-xs text-white/70">Use hosted Google or Apple sign-in, then return with an authenticated session.</p>

      <label className="mt-3 grid gap-1 text-sm text-white/85">
        Work email hint (optional)
        <input
          className="glass-input rounded-md p-2"
          type="email"
          value={socialEmail}
          onChange={(event) => setSocialEmail(event.target.value)}
          placeholder="name@company.com"
        />
      </label>

      <div className="mt-3 flex flex-wrap gap-2">
        <button
          type="button"
          className="btn-outline text-xs"
          disabled={loading}
          onClick={() => void signInWith("google")}
        >
          Continue with Google
        </button>
        <button
          type="button"
          className="btn-outline text-xs"
          disabled={loading}
          onClick={() => void signInWith("apple")}
        >
          Continue with Apple ID
        </button>
      </div>

      {error ? <p className="mt-2 text-xs text-red-300">{error}</p> : null}
    </div>
  );
}
