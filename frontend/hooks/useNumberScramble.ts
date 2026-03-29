import { useState, useEffect } from "react";

/**
 * Cinematic hook to scramble a number value (like a sci-fi calculation UI).
 * It quickly flashes random characters before resolving to the actual value over a specified duration.
 */
export function useNumberScramble(
  value: number | string,
  durationMs: number = 800,
  chars: string = "0123456789!@#$%^&*()_+="
) {
  const [displayValue, setDisplayValue] = useState<string | number>(value);

  useEffect(() => {
    // If it's a very fast update or not string/number, just set it
    const targetString = String(value);
    
    let startTime: number | null = null;
    let lastTickTime: number = 0;
    let animationFrameId: number;

    const tick = (timestamp: number) => {
      if (!startTime) startTime = timestamp;
      const progress = timestamp - startTime;
      
      if (progress < durationMs) {
        if (timestamp - lastTickTime > 50) { // Throttle updates
          // Scramble
          let scrambled = "";
          for (let i = 0; i < targetString.length; i++) {
            if (targetString[i] === " " || targetString[i] === ".") {
              scrambled += targetString[i];
            } else {
              scrambled += chars[Math.floor(Math.random() * chars.length)];
            }
          }
          setDisplayValue(scrambled);
          lastTickTime = timestamp;
        }
        animationFrameId = requestAnimationFrame(tick);
      } else {
        // Complete
        setDisplayValue(targetString);
      }
    };

    animationFrameId = requestAnimationFrame(tick);

    return () => cancelAnimationFrame(animationFrameId);
  }, [value, durationMs, chars]);

  return displayValue;
}
