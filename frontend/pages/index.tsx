import dynamic from 'next/dynamic';

const SimulatedLocalApp = dynamic(
  () => import('../components/outsource/local-simulated/App'),
  {
    ssr: false,
    loading: () => (
      <div className="min-h-screen bg-black flex items-center justify-center text-white text-xs uppercase tracking-[0.4em] font-mono">
        Initializing Mission Control
      </div>
    ),
  }
);

export default function HomePage() {
  return <SimulatedLocalApp />;
}
