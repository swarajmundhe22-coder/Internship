import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/router";

import { CinematicScene } from "../../components/CinematicScene";
import { LayoutShell } from "../../components/LayoutShell";
import { useApi } from "../../hooks/useApi";
import { AuthTokenResponse, RegistrationOtpChallengeResponse } from "../../types/domain";

function strengthPercent(password: string): number {
  if (!password) {
    return 0;
  }

  let score = 0;
  if (password.length >= 8) score += 25;
  if (/[A-Z]/.test(password)) score += 20;
  if (/[0-9]/.test(password)) score += 20;
  if (/[^A-Za-z0-9]/.test(password)) score += 20;
  if (password.length >= 12) score += 15;
  return Math.min(score, 100);
}

export default function LoginPage() {
  const router = useRouter();
  const { run, loading, error } = useApi();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [otp, setOtp] = useState("");
  const [otpRequested, setOtpRequested] = useState(false);
  const [otpMessage, setOtpMessage] = useState<string | null>(null);
  const [devOtp, setDevOtp] = useState<string | null>(null);
  const passwordEnergy = strengthPercent(password);

  async function completeLogin(token: AuthTokenResponse): Promise<void> {
    if (typeof window !== "undefined") {
      window.localStorage.setItem("onlooker_token", token.access_token);
    }
    await router.push("/projects");
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

  return (
    <LayoutShell title="Sign In" subtitle="Authenticate to save projects and collaborate on corrosion scenarios.">
      <CinematicScene
        tone="opening"
        sceneLabel="Scene 1 / Opening Cutscene"
        narrative="Authenticate to enter the Command Grid. Your credentials unlock planetary foresight."
      >
        <section className="auth-shell mx-auto grid max-w-5xl gap-4 lg:grid-cols-[1.1fr_0.9fr]">
          <article className="auth-brief panel p-6 md:p-7" data-cinematic-reveal="true">
            <p className="hud-label text-[10px]">Access Layer</p>
            <h2 className="auth-hero-title mt-2 text-softwhite">Command Grid identity check with live OTP seal.</h2>
            <p className="auth-hero-copy mt-3 text-softwhite/78">
              Every sign-in now uses a timed verification pulse over email so cockpit access remains operator-bound and audit-ready.
            </p>
            <div className="auth-chip-row mt-4">
              <span className="auth-chip">2-Step Gate</span>
              <span className="auth-chip">Email OTP</span>
              <span className="auth-chip">Session Tokens</span>
            </div>

            <div className="auth-stage mt-5">
              <p className="hud-label text-[10px]">Sequence</p>
              <ol className="auth-sequence mt-2">
                <li><span>01</span><p>Submit email and password identity pair.</p></li>
                <li><span>02</span><p>Receive 6-digit timed code in mailbox.</p></li>
                <li><span>03</span><p>Verify OTP to enter mission workspace.</p></li>
              </ol>
            </div>
          </article>

          <article className="auth-form panel p-6 md:p-7" data-cinematic-reveal="true">
            <form className="grid gap-3" onSubmit={(event) => void submit(event)}>
              <label className="grid gap-1 text-sm text-softwhite/85">
                Email
                <input
                  className="glass-input rounded-md p-2"
                  type="email"
                  value={email}
                  onChange={(event) => setEmail(event.target.value)}
                  required
                />
              </label>
              <label className="grid gap-1 text-sm text-softwhite/85">
                Password
                <input
                  className="glass-input rounded-md p-2"
                  type="password"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  minLength={8}
                  required
                />
              </label>

              <div className="grid gap-1">
                <p className="hud-label text-[10px] text-softwhite/80">Credential Energy</p>
                <div className="energy-meter">
                  <span style={{ width: `${passwordEnergy}%` }} />
                </div>
                <p className="text-xs text-softwhite/65">Plasma integrity: {passwordEnergy}%</p>
              </div>

              {otpRequested ? (
                <label className="grid gap-1 text-sm text-softwhite/85">
                  OTP (6 digits)
                  <input
                    className="glass-input rounded-md p-2"
                    type="text"
                    inputMode="numeric"
                    pattern="[0-9]{6}"
                    maxLength={6}
                    value={otp}
                    onChange={(event) => setOtp(event.target.value.replace(/\D/g, "").slice(0, 6))}
                    required
                  />
                </label>
              ) : null}

              <button className="holo-btn portal-btn rounded-md px-3 py-2 text-sm" type="submit" disabled={loading}>
                {loading ? "Opening portal..." : otpRequested ? "Verify OTP & Sign In" : "Send Sign-In OTP"}
              </button>

              {otpRequested ? (
                <button
                  className="rounded-md border border-softwhite/30 bg-softwhite/5 px-3 py-2 text-sm text-softwhite/86 transition hover:border-softwhite/55"
                  type="button"
                  onClick={() => void requestOtp()}
                  disabled={loading}
                >
                  Resend OTP
                </button>
              ) : null}
            </form>
            {error && <p className="mt-3 text-sm text-red-300">{error}</p>}
            {otpMessage ? <p className="mt-3 text-sm text-lagoon/90">{otpMessage}</p> : null}
            {devOtp ? <p className="mt-2 text-xs text-softwhite/65">Dev fallback OTP: {devOtp}</p> : null}
            <p className="mt-4 text-sm text-softwhite/80">
              Need an account? <Link className="text-lagoon underline" href="/auth/register">Register</Link>
            </p>
          </article>
        </section>
      </CinematicScene>
    </LayoutShell>
  );
}
