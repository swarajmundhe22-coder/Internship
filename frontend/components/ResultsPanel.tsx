import { SimulationPrediction } from "../types/domain";

type ResultsPanelProps = {
  result: SimulationPrediction | null;
};

export function ResultsPanel({ result }: ResultsPanelProps) {
  if (!result) {
    return <section className="panel p-6 text-sm text-slate-500">Run a simulation to view corrosion risk intelligence.</section>;
  }

  return (
    <section className="panel grid gap-4 p-6">
      <h3 className="text-lg font-semibold">Predicted Results</h3>
      <p className="text-sm text-slate-600">Risk Class: <span className="font-bold uppercase">{result.risk_classification}</span></p>
      <p className="text-sm text-slate-600">Environmental Score: <span className="font-semibold">{result.environment_risk.risk_score.toFixed(2)}</span></p>
      <p className="text-sm text-slate-600">Corrosion Rate: <span className="font-semibold">{result.corrosion_rate_mm_per_year.toFixed(4)} mm/year</span></p>
      <p className="text-sm text-slate-600">Estimated Lifespan: <span className="font-semibold">{result.estimated_lifespan_years.toFixed(1)} years</span></p>
      <p className="rounded-lg bg-slatewash p-3 text-sm text-slate-700">{result.recommendation_summary}</p>
    </section>
  );
}
