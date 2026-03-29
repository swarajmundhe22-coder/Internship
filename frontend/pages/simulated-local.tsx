import dynamic from "next/dynamic";

const LocalSimulatedApp = dynamic(() => import("../components/outsource/local-simulated/App"), {
  ssr: false,
  loading: () => (
    <div className="min-h-screen bg-black text-white flex items-center justify-center">
      <div className="w-10 h-10 border-4 border-accent border-t-transparent rounded-full animate-spin" />
    </div>
  )
});

export default function SimulatedLocalPage() {
  return <LocalSimulatedApp />;
}
