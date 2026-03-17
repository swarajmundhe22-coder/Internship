import Link from "next/link";
import { FormEvent, useEffect, useRef, useState } from "react";
import { useRouter } from "next/router";
import { motion } from "framer-motion";

import { CinematicScene } from "../../components/CinematicScene";
import { LayoutShell } from "../../components/LayoutShell";
import Navigation from "../../components/outsource/Navigation";
import ParticleCanvas from "../../components/outsource/ParticleCanvas";
import SocialSignInPanel from "../../components/SocialSignInPanel";
import { useApi } from "../../hooks/useApi";
import { AuthTokenResponse, RegistrationOtpChallengeResponse } from "../../types/domain";

const AUTH_HERO_IMAGE = "https://d2xsxph8kpxj0f.cloudfront.net/310519663448417147/bRTxyCJq9mgt5p2skQtMAx/gifip-hero-bg-A6fYWkbGeyrzV2VMo2dA8h.webp";

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
  const [loaded, setLoaded] = useState(false);
  const [counter, setCounter] = useState(0);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [otp, setOtp] = useState("");
  const [otpRequested, setOtpRequested] = useState(false);
  const [otpMessage, setOtpMessage] = useState<string | null>(null);
  const [devOtp, setDevOtp] = useState<string | null>(null);
  const counterRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const passwordEnergy = strengthPercent(password);
  const stageProgress = otpRequested ? 100 : 52;

  useEffect(() => {
    counterRef.current = setInterval(() => {
      setCounter((prev) => {
        if (prev >= 100) {
          if (counterRef.current) clearInterval(counterRef.current);
          setLoaded(true);
          return 100;
        }
        return prev + Math.floor(Math.random() * 4) + 1;
      });
    }, 25);

    return () => {
      if (counterRef.current) clearInterval(counterRef.current);
    };
  }, []);

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
    <div className="outsource-home min-h-screen" style={{ background: "#050508", color: "#f0f0f5" }}>
      {!loaded && (
        <motion.div
          className="fixed inset-0 z-[120] flex flex-col items-center justify-center"
          style={{ background: "#050508" }}
          animate={{ opacity: counter >= 100 ? 0 : 1 }}
          transition={{ duration: 0.6, delay: 0.2 }}
        >
          <div className="section-number mb-4">Initializing Identity Gate</div>
          <div className="text-7xl font-bold text-white" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
            {counter.toString().padStart(3, "0")}
          </div>
          <div className="relative mt-4 h-px w-48 overflow-hidden bg-white/10">
            <motion.div className="absolute inset-y-0 left-0 bg-teal-400" style={{ width: `${counter}%` }} />
          </div>
        </motion.div>
      )}
      <div className="noise-overlay" />
      <div className="scan-line" />
      <Navigation />
      <div className="relative overflow-hidden pt-20">
        <div className="pointer-events-none absolute inset-0 z-0">
          <img
            src={AUTH_HERO_IMAGE}
            alt=""
            className="h-full w-full object-cover opacity-20"
            style={{ filter: "saturate(1.15) brightness(0.55)" }}
          />
          <div
            className="absolute inset-0"
            style={{
              background:
                "radial-gradient(ellipse 70% 58% at 50% 30%, rgba(77,255,210,0.12) 0%, transparent 70%), linear-gradient(to bottom, rgba(5,5,8,0.52) 0%, rgba(5,5,8,0.86) 70%, #050508 100%)"
            }}
          />
        </div>

        <div className="pointer-events-none absolute inset-0 z-[1] opacity-80">
          <ParticleCanvas className="h-full w-full" />
        </div>

        <div className="relative z-10">
        <LayoutShell title="Sign In" subtitle="Authenticate to save projects and collaborate on corrosion scenarios.">
          <CinematicScene
            tone="opening"
            sceneLabel="Scene 1 / Opening Cutscene"
            narrative="Authenticate to enter the Command Grid. Your credentials unlock planetary foresight."
          >
            <motion.section
              className="mb-4 grid gap-3 rounded-xl border border-lagoon/35 bg-slatewash/30 p-4 md:grid-cols-[1fr_auto] md:items-center"
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.45, ease: [0.16, 1, 0.3, 1] }}
            >
              <div>
                <p className="hud-label text-[10px]">Authentication Command Layer</p>
                <h3 className="mt-2 text-xl font-semibold text-softwhite md:text-2xl">
                  Identity Gate Is <span className="gradient-text">Live And Monitored</span>
                </h3>
                <p className="mt-2 text-sm text-softwhite/74">
                  Multi-step verification with OTP timing, session controls, and audit visibility built into every sign-in sequence.
                </p>
              </div>
              <div className="grid grid-cols-3 gap-2 text-center">
                <div className="rounded-lg border border-lagoon/40 bg-lagoon/10 px-3 py-2">
                  <p className="text-base font-semibold text-softwhite">2</p>
                  <p className="text-[10px] uppercase tracking-wide text-softwhite/70">Steps</p>
                </div>
                <div className="rounded-lg border border-neoviolet/40 bg-neoviolet/10 px-3 py-2">
                  <p className="text-base font-semibold text-softwhite">6</p>
                  <p className="text-[10px] uppercase tracking-wide text-softwhite/70">OTP Digits</p>
                </div>
                <div className="rounded-lg border border-signal/45 bg-signal/10 px-3 py-2">
                  <p className="text-base font-semibold text-softwhite">24/7</p>
                  <p className="text-[10px] uppercase tracking-wide text-softwhite/70">Monitoring</p>
                </div>
              </div>
            </motion.section>

            <section className="auth-shell mx-auto grid max-w-5xl gap-4 lg:grid-cols-[1.1fr_0.9fr]">
          <motion.article
            className="auth-brief panel p-6 md:p-7"
            data-cinematic-reveal="true"
            initial={{ opacity: 0, y: 24, scale: 0.985 }}
            whileInView={{ opacity: 1, y: 0, scale: 1 }}
            viewport={{ once: true, amount: 0.4 }}
            transition={{ duration: 0.55, ease: [0.16, 1, 0.3, 1] }}
          >
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
          </motion.article>

          <motion.article
            className="auth-form panel p-6 md:p-7"
            data-cinematic-reveal="true"
            initial={{ opacity: 0, y: 24, scale: 0.985 }}
            whileInView={{ opacity: 1, y: 0, scale: 1 }}
            viewport={{ once: true, amount: 0.4 }}
            transition={{ duration: 0.6, delay: 0.04, ease: [0.16, 1, 0.3, 1] }}
          >
            <div className="mb-3 rounded-md border border-softwhite/20 bg-softwhite/5 p-3">
              <div className="mb-1 flex items-center justify-between text-xs text-softwhite/75">
                <span>Access Stage</span>
                <span>{otpRequested ? "OTP Verification" : "Identity Validation"}</span>
              </div>
              <div className="h-1.5 overflow-hidden rounded-full bg-softwhite/15">
                <motion.div
                  className="h-full bg-gradient-to-r from-lagoon via-neoviolet to-signal"
                  initial={{ width: 0 }}
                  animate={{ width: `${stageProgress}%` }}
                  transition={{ duration: 0.4, ease: "easeOut" }}
                />
              </div>
            </div>

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

            <SocialSignInPanel email={email} redirectTo="/projects" />

            <p className="mt-4 text-sm text-softwhite/80">
              Need an account? <Link className="text-lagoon underline" href="/auth/register">Register</Link>
            </p>
          </motion.article>
            </section>
          </CinematicScene>
        </LayoutShell>
        </div>

        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 0.18 }}
          className="relative z-10 overflow-hidden border-t border-white/5 py-3"
        >
          <motion.div
            animate={{ x: [0, -860] }}
            transition={{ duration: 22, repeat: Infinity, ease: "linear" }}
            className="flex w-max items-center gap-6 whitespace-nowrap"
          >
            {Array(4).fill(["SECURE", "VERIFIED", "AUDIT-READY", "MISSION ACCESS"]).flat().map((tag, i) => (
              <span key={`${tag}-${i}`} className="section-number px-3">{tag}</span>
            ))}
          </motion.div>
        </motion.div>
      </div>
    </div>
  );
}
