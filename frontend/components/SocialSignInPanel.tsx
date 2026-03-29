import { useEffect, useState } from "react";
import { beginSocialAuth, type SocialProvider } from "../utils/socialAuth";

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

    try {
      await beginSocialAuth(provider, {
        nextPath: redirectTo ?? "/",
        emailHint: socialEmail,
      });
    } catch (socialStartError) {
      console.error("Unable to start social sign-in", socialStartError);
      const socialMessage =
        socialStartError instanceof Error && socialStartError.message
          ? socialStartError.message
          : "Social sign-in is unavailable right now. Please use OTP sign-in or try again later.";
      setError(socialMessage);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mt-4 rounded-lg border border-neoviolet/25 bg-slatewash/35 p-4">
      <p className="hud-label text-[10px]">Social Sign In</p>
      <p className="mt-1 text-xs text-softwhite/72">Use hosted Google or Apple sign-in, then return with an authenticated session.</p>

      <label className="mt-3 grid gap-1 text-sm text-softwhite/85">
        Email hint (optional)
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
          className="tactical-btn hud-tone-support text-xs"
          disabled={loading}
          onClick={() => void signInWith("google")}
        >
          Continue with Google
        </button>
        <button
          type="button"
          className="tactical-btn hud-tone-primary text-xs"
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
