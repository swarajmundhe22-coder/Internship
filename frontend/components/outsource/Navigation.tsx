/* ============================================================
   Navigation — Lusion.co-style header
   Minimal top bar with logo, sound toggle, CTA, and menu
   ============================================================ */
import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/router";
import { motion, AnimatePresence } from "framer-motion";
import { X, Menu, Volume2, VolumeX } from "lucide-react";
import { normalizeDemoBookingUrl } from "../../utils/demoBookingUrl";

const navLinks = [
  { label: "Platform", href: "#platform" },
  { label: "Architecture", href: "#architecture" },
  { label: "Features", href: "#features" },
  { label: "Simulation", href: "#simulation" },
  { label: "Industries", href: "#industries" },
  { label: "Roadmap", href: "#roadmap" },
];

const menuItems = [
  { label: "Platform Overview", sub: "Predictive Intelligence" },
  { label: "Corrosion Engine", sub: "Core Computation" },
  { label: "3D Visualization", sub: "Simulation Tools" },
  { label: "Material Database", sub: "100+ Materials" },
  { label: "Industries", sub: "9 Sectors" },
  { label: "Roadmap", sub: "4 Phases" },
];

type NavigationProps = {
  onRequestDemo?: () => void;
};

const DEMO_BOOKING_URL = normalizeDemoBookingUrl(process.env.NEXT_PUBLIC_DEMO_BOOKING_URL ?? "https://calendly.com");

export default function Navigation({ onRequestDemo }: NavigationProps) {
  const router = useRouter();
  const isAuthRoute = router.pathname.startsWith("/auth");
  const [menuOpen, setMenuOpen] = useState(false);
  const [muted, setMuted] = useState(true);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 50);
    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  useEffect(() => {
    document.body.style.overflow = menuOpen ? "hidden" : "";
    return () => { document.body.style.overflow = ""; };
  }, [menuOpen]);

  return (
    <>
      <motion.header
        initial={{ y: -80, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
        className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-6 md:px-10 py-5"
        style={{
          background: scrolled ? "rgba(5,5,8,0.85)" : "transparent",
          backdropFilter: scrolled ? "blur(20px)" : "none",
          borderBottom: scrolled ? "1px solid rgba(77,255,210,0.06)" : "none",
          transition: "background 0.4s ease, backdrop-filter 0.4s ease",
        }}
      >
        {/* Logo */}
        <a href="/" className="flex items-center gap-3 group" aria-label="GIFIP Home">
          <div className="relative w-8 h-8">
            <div className="absolute inset-0 rounded-sm bg-teal-400/20 border border-teal-400/40 group-hover:bg-teal-400/30 transition-all duration-300" />
            <div className="absolute inset-1.5 rounded-sm bg-teal-400/60 group-hover:bg-teal-400 transition-all duration-300" />
          </div>
          <span className="font-display font-700 text-sm tracking-widest uppercase text-white/90 group-hover:text-teal-300 transition-colors duration-300"
            style={{ fontFamily: "'Space Grotesk', sans-serif", letterSpacing: "0.15em" }}>
            The On Lookers
          </span>
        </a>

        {/* Center nav links — desktop */}
        {!isAuthRoute ? (
          <nav className="hidden lg:flex items-center gap-8">
            {navLinks.map((link) => (
              <a key={link.label} href={link.href} className="nav-link animated-underline">
                {link.label}
              </a>
            ))}
          </nav>
        ) : (
          <div className="hidden lg:block section-number">Authentication</div>
        )}

        {/* Right controls */}
        <div className="flex items-center gap-4">
          <button
            onClick={() => setMuted(!muted)}
            className="nav-link flex items-center gap-2 hover:text-teal-300 transition-colors"
            aria-label="Toggle sound"
          >
            {muted ? <VolumeX size={14} /> : <Volume2 size={14} />}
            <span className="hidden sm:inline text-xs tracking-widest uppercase">{muted ? "Sound Off" : "Sound On"}</span>
          </button>

          {onRequestDemo ? (
            <button type="button" onClick={onRequestDemo} className="btn-primary hidden sm:block text-xs">
              Request Demo
            </button>
          ) : (
            <Link href="/demo" className="btn-primary hidden sm:inline-flex text-xs">
              Request Demo
            </Link>
          )}

          <Link href="/auth/login" className="btn-outline hidden md:inline-flex text-xs">
            Login
          </Link>

          <Link href="/auth/register" className="btn-outline hidden md:inline-flex text-xs">
            Register
          </Link>

          <button
            onClick={() => setMenuOpen(!menuOpen)}
            className="flex items-center gap-2 nav-link hover:text-white"
            aria-label="Toggle menu"
          >
            {menuOpen ? <X size={16} /> : <Menu size={16} />}
            <span className="text-xs tracking-widest uppercase">{menuOpen ? "Close" : "Menu"}</span>
          </button>
        </div>
      </motion.header>

      {/* Full-screen menu overlay */}
      <AnimatePresence>
        {menuOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.4 }}
            className="fixed inset-0 z-40 flex"
            style={{ background: "rgba(5,5,8,0.97)", backdropFilter: "blur(30px)" }}
          >
            {/* Left side — menu items */}
            <div className="flex-1 flex flex-col justify-center px-10 md:px-20">
              <div className="section-number mb-8">Navigation</div>
              <nav className="space-y-1">
                <motion.div
                  initial={{ x: -40, opacity: 0 }}
                  animate={{ x: 0, opacity: 1 }}
                  exit={{ x: -40, opacity: 0 }}
                  transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
                  className="flex gap-2 pb-4"
                >
                  <Link
                    href="/auth/login"
                    onClick={() => setMenuOpen(false)}
                    className="btn-outline text-xs"
                  >
                    Login
                  </Link>
                  <Link
                    href="/auth/register"
                    onClick={() => setMenuOpen(false)}
                    className="btn-outline text-xs"
                  >
                    Register
                  </Link>
                </motion.div>
                {menuItems.map((item, i) => (
                  <motion.a
                    key={item.label}
                    href={`#${item.label.toLowerCase().replace(/\s+/g, "-")}`}
                    initial={{ x: -40, opacity: 0 }}
                    animate={{ x: 0, opacity: 1 }}
                    exit={{ x: -40, opacity: 0 }}
                    transition={{ duration: 0.4, delay: i * 0.06, ease: [0.22, 1, 0.36, 1] }}
                    onClick={() => setMenuOpen(false)}
                    className="group flex items-baseline gap-6 py-3 border-b border-white/5 hover:border-teal-400/20 transition-all duration-300"
                  >
                    <span className="section-number w-8">{String(i + 1).padStart(2, "0")}</span>
                    <div>
                      <div className="text-3xl md:text-4xl font-bold text-white/80 group-hover:text-white transition-colors duration-300"
                        style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
                        {item.label}
                      </div>
                      <div className="text-xs text-white/30 mt-0.5" style={{ fontFamily: "'DM Mono', monospace" }}>
                        {item.sub}
                      </div>
                    </div>
                    <span className="ml-auto text-teal-400 opacity-0 group-hover:opacity-100 transition-opacity duration-300">→</span>
                  </motion.a>
                ))}
              </nav>
            </div>

            {/* Right side — info panel */}
            <motion.div
              initial={{ x: 60, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: 60, opacity: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="hidden lg:flex w-80 flex-col justify-between p-10 border-l border-white/5"
            >
              <div>
                <div className="section-number mb-4">Platform Status</div>
                <div className="flex items-center gap-2 mb-6">
                  <div className="w-2 h-2 rounded-full bg-teal-400 pulse-ring" />
                  <span className="text-xs text-teal-400" style={{ fontFamily: "'DM Mono', monospace" }}>
                    System Operational
                  </span>
                </div>
                <div className="space-y-3">
                  {[
                    { label: "Corrosion Engine", val: "v2.4.1" },
                    { label: "Material DB", val: "12,400+ entries" },
                    { label: "Active Simulations", val: "247" },
                    { label: "Predictions Today", val: "1,892" },
                  ].map((stat) => (
                    <div key={stat.label} className="flex justify-between items-center py-2 border-b border-white/5">
                      <span className="text-xs text-white/40" style={{ fontFamily: "'DM Mono', monospace" }}>{stat.label}</span>
                      <span className="text-xs text-teal-400" style={{ fontFamily: "'DM Mono', monospace" }}>{stat.val}</span>
                    </div>
                  ))}
                </div>
              </div>
              <div>
                <div className="section-number mb-3">Contact</div>
                <a href={DEMO_BOOKING_URL} target="_blank" rel="noreferrer" className="text-sm text-white/60 hover:text-teal-400 transition-colors">
                  Book via Calendar
                </a>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
