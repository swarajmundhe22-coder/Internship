import Link from "next/link";
import { FormEvent, useMemo, useState } from "react";
import { Toaster } from "sonner";

import Navigation from "../components/outsource/Navigation";
import SocialSignInPanel from "../components/SocialSignInPanel";
import { useApi } from "../hooks/useApi";
import { DemoRequestResponse } from "../types/domain";
import { normalizeDemoBookingUrl } from "../utils/demoBookingUrl";

const FALLBACK_BOOKING_URL = "https://calendly.com";

export default function DemoPage() {
  const { run, loading, error } = useApi();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [company, setCompany] = useState("");
  const [role, setRole] = useState("");
  const [useCase, setUseCase] = useState("");
  const [preferredAuthProvider, setPreferredAuthProvider] = useState<"email" | "google" | "apple">("email");
  const [submitted, setSubmitted] = useState<DemoRequestResponse | null>(null);

  const bookingUrl = useMemo(
    () => normalizeDemoBookingUrl(submitted?.booking_url ?? process.env.NEXT_PUBLIC_DEMO_BOOKING_URL ?? FALLBACK_BOOKING_URL),
    [submitted]
  );

  async function submit(event: FormEvent<HTMLFormElement>): Promise<void> {
    event.preventDefault();
    const response = await run<DemoRequestResponse>("/demo/request", {
      method: "POST",
      body: JSON.stringify({ full_name: fullName, email, company, role, use_case: useCase, preferred_auth_provider: preferredAuthProvider })
    });
    setSubmitted(response);
  }

  return (
    <div className="outsource-home min-h-screen" style={{ background: "#050508", color: "#f0f0f5" }}>
      <Toaster richColors position="top-right" />
      <div className="noise-overlay" />
      <div className="scan-line" />
      <Navigation />

      <main className="container mx-auto px-6 pb-16 pt-28">
        <p className="section-number">Demo Center</p>
        <h1 className="mt-2 text-4xl font-semibold text-white md:text-5xl">Book your guided product demo</h1>
        <p className="mt-3 max-w-3xl text-sm text-white/70 md:text-base">
          Choose email registration, Google sign-in, or Apple ID sign-in, submit your demo brief to backend,
          and then lock your meeting slot through calendar booking.
        </p>

        <section className="mt-8 grid gap-5 lg:grid-cols-[1.2fr_0.8fr]">
          <article className="rounded-xl border border-white/15 bg-white/5 p-5 md:p-6">
            <form className="grid gap-3" onSubmit={(event) => void submit(event)}>
              <div className="grid gap-3 md:grid-cols-2">
                <label className="grid gap-1 text-sm text-white/85">
                  Full name
                  <input className="glass-input rounded-md p-2" value={fullName} onChange={(event) => setFullName(event.target.value)} required />
                </label>
                <label className="grid gap-1 text-sm text-white/85">
                  Work email
                  <input className="glass-input rounded-md p-2" type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
                </label>
                <label className="grid gap-1 text-sm text-white/85">
                  Company
                  <input className="glass-input rounded-md p-2" value={company} onChange={(event) => setCompany(event.target.value)} required />
                </label>
                <label className="grid gap-1 text-sm text-white/85">
                  Role
                  <input className="glass-input rounded-md p-2" value={role} onChange={(event) => setRole(event.target.value)} required />
                </label>
              </div>

              <label className="grid gap-1 text-sm text-white/85">
                What do you want us to cover in the demo?
                <textarea className="glass-input min-h-28 rounded-md p-2" value={useCase} onChange={(event) => setUseCase(event.target.value)} minLength={10} required />
              </label>

              <div className="rounded-md border border-white/15 bg-white/5 p-3">
                <p className="section-number">Preferred Sign-in Path</p>
                <div className="mt-2 flex flex-wrap gap-2">
                  <button type="button" className={preferredAuthProvider === "email" ? "btn-primary text-xs" : "btn-outline text-xs"} onClick={() => setPreferredAuthProvider("email")}>Register via Email</button>
                  <button type="button" className={preferredAuthProvider === "google" ? "btn-primary text-xs" : "btn-outline text-xs"} onClick={() => setPreferredAuthProvider("google")}>Google Sign In</button>
                  <button type="button" className={preferredAuthProvider === "apple" ? "btn-primary text-xs" : "btn-outline text-xs"} onClick={() => setPreferredAuthProvider("apple")}>Apple ID Sign In</button>
                </div>
              </div>

              <button className="btn-primary text-xs" type="submit" disabled={loading}>{loading ? "Submitting..." : "Submit to backend"}</button>
              {error ? <p className="text-sm text-red-300">{error}</p> : null}
            </form>

            {submitted ? (
              <div className="mt-4 rounded-md border border-teal-300/35 bg-teal-200/10 p-4 text-sm text-white/90">
                <p>{submitted.message}</p>
                <p className="mt-1 text-xs text-white/70">Reference: {submitted.request_id}</p>
              </div>
            ) : null}
          </article>

          <article className="rounded-xl border border-white/15 bg-white/5 p-5 md:p-6">
            <p className="section-number">Quick Actions</p>
            <div className="mt-3 grid gap-3">
              <a className="btn-primary text-xs" href={bookingUrl} target="_blank" rel="noreferrer">Book with Calendly / Calendar</a>
              <Link className="btn-outline text-xs" href="/">Back to landing page</Link>
            </div>

            <SocialSignInPanel email={email} onSuccess={(provider) => setPreferredAuthProvider(provider)} />

            <p className="mt-3 text-xs text-white/65">
              If your account is already provisioned with Google or Apple, use social sign-in above and then continue booking.
            </p>
          </article>
        </section>
      </main>
    </div>
  );
}
