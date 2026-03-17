import Link from "next/link";
import { useRouter } from "next/router";
import { motion } from "framer-motion";
import { ReactNode, useEffect, useState } from "react";

type LayoutShellProps = {
  title: string;
  subtitle: string;
  children: ReactNode;
};

export function LayoutShell({ title, subtitle, children }: LayoutShellProps) {
  const router = useRouter();
  const [hasToken, setHasToken] = useState(false);
  const isAuthRoute = router.pathname.startsWith("/auth");

  const navItems = [
    { href: "/", label: "Identity" },
    { href: "/expertise", label: "Expertise" },
    { href: "/credibility", label: "Credibility" },
    { href: "/dashboard", label: "Dashboard" },
    { href: "/simulations", label: "Simulations" },
    { href: "/reports", label: "Reports" },
    { href: "/projects", label: "Projects" },
    { href: "/about", label: "About" }
  ];

  const moduleRailItems = [
    { href: "/", label: "Identity Scene" },
    { href: "/expertise", label: "Expertise Scene" },
    { href: "/credibility", label: "Credibility Scene" },
    { href: "/about", label: "About The On Lookers" },
    { href: "/dashboard", label: "Live Dashboard" },
    { href: "/materials", label: "Materials Registry" },
    { href: "/environments", label: "Environment Profiles" },
    { href: "/simulations", label: "Simulation Ops" },
    { href: "/simulations/compare", label: "Scenario Compare" },
    { href: "/reports", label: "Report Dossiers" },
    { href: "/visualization/mission-control", label: "Mission Control" },
    { href: "/visualization/global-risk-atlas", label: "Risk Atlas" },
    { href: "/projects", label: "Projects Workspace" },
    { href: "/admin/governance", label: "Governance" },
    { href: "/admin/audit-logs", label: "Audit Logs" },
    { href: "/admin/integrations", label: "Integrations" }
  ];

  useEffect(() => {
    if (typeof window !== "undefined") {
      setHasToken(Boolean(window.localStorage.getItem("onlooker_token")));
    }
  }, []);

  function logout() {
    if (typeof window !== "undefined") {
      window.localStorage.removeItem("onlooker_token");
    }
    setHasToken(false);
    void router.push("/auth/login");
  }

  return (
    <main className="layout-shell relative mx-auto w-full max-w-7xl p-6 md:p-10">
      <div className="shell-progress-rail">
        <div className="shell-progress-bar" />
      </div>

      <div className="pointer-events-none absolute inset-0 -z-10 opacity-70">
        <div data-scroll-parallax="slow" className="absolute -left-24 top-0 h-72 w-72 rounded-full bg-lagoon/20 blur-3xl" />
        <div data-scroll-parallax="medium" className="absolute -right-10 top-20 h-80 w-80 rounded-full bg-neoviolet/25 blur-3xl" />
        <div data-scroll-parallax="fast" className="absolute bottom-10 left-1/3 h-56 w-56 rounded-full bg-signal/10 blur-3xl" />
      </div>

      <motion.header
        className={`mb-8 panel ${isAuthRoute ? "auth-shell-header" : "panel-density-normal"}`}
        data-cinematic-reveal="true"
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.45, ease: [0.16, 1, 0.3, 1] }}
      >
        <div className={`flex flex-col gap-5 ${isAuthRoute ? "md:gap-3" : "md:flex-row md:items-end md:justify-between"}`}>
          <div className="rhythm-stack">
            <p className="type-kicker hud-label">The On Lookers</p>
            <h1 className="type-title text-softwhite md:text-[2.15rem]">{title}</h1>
            <p className={`type-body text-softwhite/72 ${isAuthRoute ? "max-w-xl" : "max-w-3xl"}`}>{subtitle}</p>
          </div>
          {!isAuthRoute ? (
            <nav className="flex max-w-3xl flex-wrap items-center gap-2 text-xs md:text-sm">
              {navItems.map((item) => {
                const isActive = router.pathname === item.href || router.pathname.startsWith(`${item.href}/`);
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`rounded-full px-4 py-2 font-hud tracking-wide transition ${
                      isActive
                        ? "animate-hud-pulse border border-lagoon/70 bg-lagoon/15 text-softwhite"
                        : "border border-softwhite/20 bg-slatewash/35 text-softwhite/90 hover:border-lagoon/60 hover:text-softwhite"
                    }`}
                  >
                    {item.label}
                  </Link>
                );
              })}

              {hasToken ? (
                <button
                  type="button"
                  className="rounded-full border border-signal/70 bg-signal/15 px-4 py-2 font-hud text-softwhite transition hover:bg-signal/25"
                  onClick={logout}
                >
                  Logout
                </button>
              ) : (
                <Link
                  href="/auth/login"
                  className="rounded-full border border-neoviolet/60 bg-neoviolet/10 px-4 py-2 font-hud text-softwhite transition hover:bg-neoviolet/20"
                >
                  Login
                </Link>
              )}
            </nav>
          ) : null}
        </div>

        {!isAuthRoute ? (
          <div className="module-rail mt-4" data-cinematic-reveal="true">
            {moduleRailItems.map((item) => {
              const isActive = router.pathname === item.href || router.pathname.startsWith(`${item.href}/`);
              return (
                <Link key={item.href} href={item.href} className={`module-pill ${isActive ? "module-pill-active" : ""}`}>
                  {item.label}
                </Link>
              );
            })}
          </div>
        ) : null}
      </motion.header>
      {children}
    </main>
  );
}
