import { FormEvent, useState } from "react";

type SimulationControlPanelProps = {
  onRun: (payload: { exposed_area_m2: number; exposure_time_hours: number }) => Promise<void>;
};

export function SimulationControlPanel({ onRun }: SimulationControlPanelProps) {
  const [area, setArea] = useState(12);
  const [duration, setDuration] = useState(720);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await onRun({ exposed_area_m2: area, exposure_time_hours: duration });
  }

  return (
    <form onSubmit={submit} className="panel grid gap-4 p-6">
      <h3 className="text-lg font-semibold">Simulation Control</h3>
      <label className="grid gap-1 text-sm">
        Exposed Area (m2)
        <input className="rounded-md border border-slate-300 p-2" type="number" min={0.1} step={0.1} value={area} onChange={(e) => setArea(Number(e.target.value))} />
      </label>
      <label className="grid gap-1 text-sm">
        Exposure Time (hours)
        <input className="rounded-md border border-slate-300 p-2" type="number" min={1} step={1} value={duration} onChange={(e) => setDuration(Number(e.target.value))} />
      </label>
      <button className="rounded-lg bg-lagoon px-4 py-2 font-medium text-white" type="submit">Run Predictive Model</button>
    </form>
  );
}
