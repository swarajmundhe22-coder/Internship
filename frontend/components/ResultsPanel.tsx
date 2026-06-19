import { SimulationPrediction } from "../types/domain";

type ResultsPanelProps = {
  result: SimulationPrediction | null;
};

export function ResultsPanel({ result }: ResultsPanelProps) {
  if (!result) {
    return <section className="panel p-6 text-sm text-slate-500">Run a simulation to view corrosion risk intelligence.</section>;
  }

  const operatorGuidance = result.operator_guidance ?? [];

  return (
    <section className="panel grid gap-4 p-6">
      <h3 className="text-lg font-semibold">Predicted Results</h3>
      <p className="text-sm text-slate-600">Risk Class: <span className="font-bold uppercase">{result.risk_classification}</span></p>
      <p className="text-sm text-slate-600">Environmental Score: <span className="font-semibold">{result.environment_risk.risk_score.toFixed(2)}</span></p>
      <p className="text-sm text-slate-600">Corrosion Rate: <span className="font-semibold">{result.corrosion_rate_mm_per_year.toFixed(4)} mm/year</span></p>
      <p className="text-sm text-slate-600">Estimated Lifespan: <span className="font-semibold">{result.estimated_lifespan_years.toFixed(1)} years</span></p>
      {typeof result.service_age_years === "number" ? (
        <p className="text-sm text-slate-600">Service Age: <span className="font-semibold">{result.service_age_years.toFixed(2)} years</span></p>
      ) : null}
      {typeof result.service_utilization === "number" ? (
        <p className="text-sm text-slate-600">Service Utilization: <span className="font-semibold">{(result.service_utilization * 100).toFixed(0)}%</span></p>
      ) : null}
      {operatorGuidance.length > 0 ? (
        <div className="grid gap-2 rounded-lg border border-slate-200 bg-white/70 p-3 text-sm text-slate-700">
          <p className="font-semibold text-slate-900">Operator Guidance</p>
          <ul className="grid gap-2">
            {operatorGuidance.map((step) => (
              <li key={step} className="leading-relaxed">{step}</li>
            ))}
          </ul>
        </div>
      ) : null}
      {result.fallback_applied ? (
        <p className="rounded-lg border border-amber-300 bg-amber-50 p-3 text-sm text-amber-900">
          Conservative fallback is active. Treat this output as a planning signal until recalibration completes.
        </p>
      ) : null}
      <p className="rounded-lg bg-slatewash p-3 text-sm text-slate-700">{result.recommendation_summary}</p>
    </section>
  );
}
