import { useCinematicQuality } from "../contexts/CinematicQualityContext";

const options: Array<{ label: string; value: "high" | "medium" | "low" }> = [
  { label: "High", value: "high" },
  { label: "Medium", value: "medium" },
  { label: "Low", value: "low" }
];

export function CinematicQualityControl() {
  const { quality, setQuality } = useCinematicQuality();

  return (
    <aside className="quality-console panel fixed bottom-4 right-4 z-40 w-[220px] p-3">
      <p className="hud-label text-[9px]">Render Quality</p>
      <p className="mt-1 text-xs text-softwhite/75">Scale post-processing for smooth performance.</p>
      <div className="mt-2 grid grid-cols-3 gap-1">
        {options.map((option) => {
          const active = quality === option.value;
          return (
            <button
              key={option.value}
              type="button"
              className={`rounded-md border px-2 py-1 text-xs transition ${
                active
                  ? "border-lagoon/70 bg-lagoon/20 text-softwhite shadow-neon"
                  : "border-softwhite/25 bg-black/30 text-softwhite/75 hover:border-lagoon/45"
              }`}
              onClick={() => setQuality(option.value)}
            >
              {option.label}
            </button>
          );
        })}
      </div>
    </aside>
  );
}
