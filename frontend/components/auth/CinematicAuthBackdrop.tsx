import { motion } from "framer-motion";

type BackdropTone = "purple" | "blue";

type CinematicAuthBackdropProps = {
  tone: BackdropTone;
};

const DATA_STREAMS = [
  { left: "4%", delay: 0.2, duration: 14.5, text: "1011010010" },
  { left: "11%", delay: 1.1, duration: 16.4, text: "0110011101" },
  { left: "18%", delay: 2.3, duration: 15.2, text: "1100101001" },
  { left: "26%", delay: 0.8, duration: 17.1, text: "0011010110" },
  { left: "34%", delay: 1.6, duration: 15.8, text: "1110100101" },
  { left: "43%", delay: 2.2, duration: 16.8, text: "0100110011" },
  { left: "53%", delay: 0.5, duration: 14.9, text: "1010101110" },
  { left: "62%", delay: 1.4, duration: 16.1, text: "0110100110" },
  { left: "71%", delay: 2.5, duration: 17.7, text: "1101010001" },
  { left: "80%", delay: 0.9, duration: 15.6, text: "0010111010" },
  { left: "89%", delay: 1.9, duration: 16.5, text: "1001101011" },
  { left: "96%", delay: 2.8, duration: 18.2, text: "0111010010" }
] as const;

export function CinematicAuthBackdrop({ tone }: CinematicAuthBackdropProps) {
  const primary = tone === "purple" ? "rgba(168, 85, 247, 0.36)" : "rgba(59, 130, 246, 0.36)";
  const secondary = tone === "purple" ? "rgba(236, 72, 153, 0.24)" : "rgba(34, 211, 238, 0.24)";
  const tertiary = tone === "purple" ? "rgba(99, 102, 241, 0.18)" : "rgba(96, 165, 250, 0.18)";

  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden="true">
      <div className="absolute inset-0 bg-black" />

      <motion.div
        className="absolute -inset-[16%]"
        style={{
          background: `
            radial-gradient(circle at 16% 14%, ${primary}, transparent 40%),
            radial-gradient(circle at 84% 20%, ${secondary}, transparent 46%),
            radial-gradient(circle at 52% 86%, ${tertiary}, transparent 44%),
            linear-gradient(145deg, rgba(2, 6, 16, 0.98) 0%, rgba(5, 10, 22, 0.96) 54%, rgba(1, 4, 10, 1) 100%)
          `
        }}
        animate={{ scale: [1, 1.05, 1], rotate: [0, 1.6, 0], opacity: [0.75, 0.94, 0.75] }}
        transition={{ duration: 22, repeat: Infinity, ease: "easeInOut" }}
      />

      <div
        className="absolute inset-0 opacity-[0.08]"
        style={{
          backgroundImage:
            "linear-gradient(rgba(255,255,255,0.3) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.28) 1px, transparent 1px)",
          backgroundSize: "40px 40px"
        }}
      />

      <motion.div
        className="absolute inset-0 opacity-[0.06]"
        style={{
          backgroundImage:
            "repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(255,255,255,0.75) 2px, rgba(255,255,255,0.75) 3px)"
        }}
        animate={{ y: [0, 8] }}
        transition={{ duration: 0.14, repeat: Infinity, ease: "linear" }}
      />

      <div className="absolute inset-0 overflow-hidden opacity-35">
        {DATA_STREAMS.map((stream, index) => (
          <motion.span
            key={`${stream.left}-${index}`}
            className={`absolute top-0 font-mono text-[9px] tracking-[0.16em] ${tone === "purple" ? "text-violet-300/55" : "text-cyan-200/55"}`}
            style={{ left: stream.left, writingMode: "vertical-rl", textOrientation: "upright" }}
            initial={{ y: "-120%" }}
            animate={{ y: ["-120%", "120vh"] }}
            transition={{ duration: stream.duration, delay: stream.delay, repeat: Infinity, ease: "linear" }}
          >
            {stream.text}
          </motion.span>
        ))}
      </div>

      <motion.div
        className="absolute -left-40 -top-32 h-96 w-96 rounded-full blur-3xl"
        style={{ background: tone === "purple" ? "rgba(168, 85, 247, 0.28)" : "rgba(56, 189, 248, 0.28)" }}
        animate={{ x: [0, 36, 0], y: [0, -24, 0], scale: [1, 1.2, 1] }}
        transition={{ duration: 12, repeat: Infinity, ease: "easeInOut" }}
      />

      <motion.div
        className="absolute -bottom-28 -right-40 h-[420px] w-[420px] rounded-full blur-3xl"
        style={{ background: tone === "purple" ? "rgba(236, 72, 153, 0.24)" : "rgba(59, 130, 246, 0.24)" }}
        animate={{ x: [0, -34, 0], y: [0, 28, 0], scale: [1, 1.15, 1] }}
        transition={{ duration: 14, repeat: Infinity, ease: "easeInOut" }}
      />

      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,transparent_0%,rgba(0,0,0,0.68)_100%)]" />
    </div>
  );
}
