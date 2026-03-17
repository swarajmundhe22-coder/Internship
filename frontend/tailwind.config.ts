import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./pages/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "IBM Plex Sans", "system-ui", "sans-serif"],
        hud: ["Orbitron", "Rajdhani", "Inter", "sans-serif"],
        mono: ["IBM Plex Mono", "ui-monospace", "SFMono-Regular", "monospace"]
      },
      colors: {
        graphite: "#1A1D22",
        slatewash: "#111723",
        signal: "#FFB84D",
        lagoon: "#00E5FF",
        neoviolet: "#9A4DFF",
        inkdark: "#0A0A0C",
        softwhite: "#E6F1FF"
      },
      boxShadow: {
        panel: "0 22px 48px rgba(0, 0, 0, 0.45)",
        neon: "0 0 0 1px rgba(0, 229, 255, 0.45), 0 0 20px rgba(0, 229, 255, 0.35)",
        violet: "0 0 0 1px rgba(154, 77, 255, 0.5), 0 0 20px rgba(154, 77, 255, 0.28)"
      },
      backgroundImage: {
        holo: "radial-gradient(circle at 20% 0%, rgba(0,229,255,0.22), transparent 32%), radial-gradient(circle at 80% 0%, rgba(154,77,255,0.18), transparent 35%), linear-gradient(180deg, rgba(10,10,12,0.9), rgba(10,10,12,0.97))"
      },
      keyframes: {
        "hud-pulse": {
          "0%, 100%": { boxShadow: "0 0 0 1px rgba(0,229,255,0.35), 0 0 14px rgba(0,229,255,0.18)" },
          "50%": { boxShadow: "0 0 0 1px rgba(0,229,255,0.6), 0 0 24px rgba(0,229,255,0.35)" }
        },
        "row-sheen": {
          "0%": { transform: "translateX(-120%)" },
          "100%": { transform: "translateX(120%)" }
        }
      },
      animation: {
        "hud-pulse": "hud-pulse 2.8s ease-in-out infinite",
        "row-sheen": "row-sheen 1.6s ease"
      }
    }
  },
  plugins: []
};

export default config;
