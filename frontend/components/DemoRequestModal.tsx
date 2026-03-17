import Link from "next/link";
import { FormEvent, useMemo, useState } from "react";

import { useApi } from "../hooks/useApi";
import { DemoRequestResponse } from "../types/domain";
import { normalizeDemoBookingUrl } from "../utils/demoBookingUrl";
import SocialSignInPanel from "./SocialSignInPanel";

type DemoRequestModalProps = {
  open: boolean;
  onClose: () => void;
};

const FALLBACK_BOOKING_URL = "https://calendly.com";

export default function DemoRequestModal({ open, onClose }: DemoRequestModalProps) {
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

  if (!open) {
    return null;
  }

  return (
    <div className="fixed inset-0 z-[130] flex items-center justify-center bg-black/75 px-4 py-10 backdrop-blur-sm" onClick={onClose}>
      <div className="w-full max-w-2xl rounded-xl border border-white/20 bg-[#0a0a10] p-5 md:p-7" onClick={(event) => event.stopPropagation()}>
        <div className="mb-4 flex items-center justify-between">
          <div>
            <p className="section-number">Demo Access</p>
            <h2 className="mt-1 text-2xl font-semibold text-white">Request your live walkthrough</h2>
          </div>
          <button type="button" className="btn-outline text-xs" onClick={onClose}>Close</button>
        </div>

        {submitted ? (
          <div className="rounded-md border border-teal-300/35 bg-teal-200/10 p-4 text-sm text-white/90">
            <p>{submitted.message}</p>
            <p className="mt-1 text-xs text-white/65">Reference ID: {submitted.request_id}</p>
            <div className="mt-4 flex flex-wrap gap-2">
              <a className="btn-primary text-xs" href={bookingUrl} target="_blank" rel="noreferrer">Book calendar slot</a>
              <Link href="/demo" className="btn-outline text-xs">Open full demo page</Link>
            </div>
          </div>
        ) : (
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
              Demo goals / use case
              <textarea className="glass-input min-h-24 rounded-md p-2" value={useCase} onChange={(event) => setUseCase(event.target.value)} minLength={10} required />
            </label>

            <div className="rounded-md border border-white/15 bg-white/5 p-3">
              <p className="section-number">Preferred Sign-in</p>
              <div className="mt-2 flex flex-wrap gap-2 text-xs">
                <button type="button" className={preferredAuthProvider === "email" ? "btn-primary text-xs" : "btn-outline text-xs"} onClick={() => setPreferredAuthProvider("email")}>Email registration</button>
                <button type="button" className={preferredAuthProvider === "google" ? "btn-primary text-xs" : "btn-outline text-xs"} onClick={() => setPreferredAuthProvider("google")}>Google sign-in</button>
                <button type="button" className={preferredAuthProvider === "apple" ? "btn-primary text-xs" : "btn-outline text-xs"} onClick={() => setPreferredAuthProvider("apple")}>Apple ID sign-in</button>
              </div>
            </div>

            <button className="btn-primary text-xs" type="submit" disabled={loading}>{loading ? "Sending..." : "Submit demo request"}</button>
            {error ? <p className="text-sm text-red-300">{error}</p> : null}
          </form>
        )}

        <SocialSignInPanel email={email} onSuccess={(provider) => setPreferredAuthProvider(provider)} />

        <div className="mt-4 flex flex-wrap gap-2">
          <a className="btn-outline text-xs" href={bookingUrl} target="_blank" rel="noreferrer">Book directly on calendar</a>
          <Link href="/demo" className="btn-outline text-xs">Open dedicated /demo page</Link>
        </div>
      </div>
    </div>
  );
}
