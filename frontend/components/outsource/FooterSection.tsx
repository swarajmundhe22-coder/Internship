/* ============================================================
   FooterSection — Lusion.co-style footer
   Large CTA + contact info + newsletter
   ============================================================ */
import { useState } from "react";
import { motion, useInView } from "framer-motion";
import { useRef } from "react";
import { toast } from "sonner";

const bigWords = ["Is", "Your", "Infrastructure", "Ready", "to", "be", "Protected?"];

export default function FooterSection() {
  const [email, setEmail] = useState("");
  const titleRef = useRef(null);
  const titleInView = useInView(titleRef, { once: true });

  const handleSubscribe = (e: React.FormEvent) => {
    e.preventDefault();
    if (email) {
      toast.success("Subscribed! We'll keep you updated on GIFIP developments.");
      setEmail("");
    }
  };

  return (
    <footer id="contact" style={{ background: "#050508" }}>
      {/* Big CTA section */}
      <div className="relative overflow-hidden py-32 border-t border-white/5">
        <div className="absolute inset-0 pointer-events-none" style={{
          background: "radial-gradient(ellipse 50% 60% at 50% 100%, rgba(77,255,210,0.04) 0%, transparent 70%)"
        }} />

        <div className="container">
          <div ref={titleRef} className="text-center mb-16">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={titleInView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.6 }}
              className="section-number mb-8 text-center"
            >
              Let's work together
            </motion.div>

            <div className="flex flex-wrap justify-center gap-x-4 gap-y-0">
              {bigWords.map((word, i) => (
                <motion.span
                  key={`${word}-${i}`}
                  initial={{ y: 60, opacity: 0 }}
                  animate={titleInView ? { y: 0, opacity: 1 } : {}}
                  transition={{ duration: 0.8, delay: 0.2 + i * 0.08, type: "tween" }}
                  className="text-5xl md:text-7xl lg:text-8xl font-bold leading-none"
                  style={{
                    fontFamily: "'Space Grotesk', sans-serif",
                    letterSpacing: "-0.03em",
                    color: i === 2 || i === 6 ? "#4DFFD2" : "white",
                  }}
                >
                  {word}
                </motion.span>
              ))}
            </div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={titleInView ? { opacity: 1, y: 0 } : {}}
              transition={{ duration: 0.7, delay: 0.9 }}
              className="mt-12 flex flex-col sm:flex-row items-center justify-center gap-4"
            >
              <a href="mailto:hello@gifip.io" className="btn-primary text-sm">
                Request a Demo
              </a>
              <a href="#platform" className="btn-outline text-sm">
                Explore Platform
              </a>
            </motion.div>
          </div>
        </div>
      </div>

      {/* Footer info */}
      <div className="border-t border-white/5 py-16">
        <div className="container">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-12">
            {/* Brand */}
            <div>
              <div className="flex items-center gap-3 mb-6">
                <div className="relative w-8 h-8">
                  <div className="absolute inset-0 border border-teal-400/40" />
                  <div className="absolute inset-1.5 bg-teal-400/60" />
                </div>
              <span className="font-bold text-sm tracking-widest uppercase text-white"
                style={{ fontFamily: "'Space Grotesk', sans-serif", letterSpacing: "0.15em" }}>
                The On Lookers
              </span>
              </div>
              <p className="text-sm text-white/30 leading-relaxed"
                style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 300 }}>
                The On Lookers — Advanced infrastructure monitoring and corrosion prediction platform.
              </p>
            </div>

            {/* Platform */}
            <div>
              <div className="section-number mb-4">Platform</div>
              <div className="space-y-2">
                {["Corrosion Engine", "Material Database", "3D Visualization", "Engineering Tools", "Report Generator"].map((item) => (
                  <a key={item} href="#platform"
                    className="block text-sm text-white/30 hover:text-white/70 transition-colors duration-300 animated-underline"
                    style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
                    {item}
                  </a>
                ))}
              </div>
            </div>

            {/* Industries */}
            <div>
              <div className="section-number mb-4">Industries</div>
              <div className="space-y-2">
                {["Oil & Gas", "Bridge Engineering", "Marine", "Energy", "Chemical Processing"].map((item) => (
                  <a key={item} href="#industries"
                    className="block text-sm text-white/30 hover:text-white/70 transition-colors duration-300 animated-underline"
                    style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
                    {item}
                  </a>
                ))}
              </div>
            </div>

            {/* Newsletter */}
            <div>
              <div className="section-number mb-4">Stay Updated</div>
              <p className="text-sm text-white/30 mb-4"
                style={{ fontFamily: "'Space Grotesk', sans-serif", fontWeight: 300 }}>
                Subscribe to receive platform updates and corrosion intelligence insights.
              </p>
              <form onSubmit={handleSubscribe} className="flex gap-2">
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="Your email"
                  className="flex-1 bg-transparent border border-white/10 px-3 py-2 text-sm text-white placeholder-white/20 focus:outline-none focus:border-teal-400/40 transition-colors duration-300"
                  style={{ fontFamily: "'DM Mono', monospace" }}
                />
                <button type="submit" className="px-4 py-2 border border-teal-400/30 text-teal-400 text-xs hover:bg-teal-400/10 transition-colors duration-300"
                  style={{ fontFamily: "'DM Mono', monospace" }}>
                  →
                </button>
              </form>
            </div>
          </div>

          {/* Bottom bar */}
          <div className="mt-16 pt-8 border-t border-white/5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
            <div className="text-xs text-white/20" style={{ fontFamily: "'DM Mono', monospace" }}>
              ©2025 The On Lookers — Infrastructure Intelligence Platform
            </div>
            <div className="flex items-center gap-6">
              {["Privacy Policy", "Terms of Use", "API Docs"].map((link) => (
                <a key={link} href="#"
                  className="text-xs text-white/20 hover:text-white/50 transition-colors duration-300"
                  style={{ fontFamily: "'DM Mono', monospace" }}>
                  {link}
                </a>
              ))}
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}
