import React from 'react';
import { motion } from 'framer-motion';
import { ArrowLeft, BarChart3, TrendingDown, Clock, ShieldCheck, AlertTriangle } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

interface Props {
  scenarios: any[];
  onBack: () => void;
}

const ComparisonView = ({ scenarios, onBack }: Props) => {
  if (!scenarios || scenarios.length === 0) {
    return (
      <div className="h-full flex flex-col items-center justify-center space-y-6">
        <div className="w-24 h-24 rounded-full bg-white/5 flex items-center justify-center border border-white/10">
          <BarChart3 className="w-10 h-10 text-white/20" />
        </div>
        <div className="text-center space-y-2">
          <h3 className="text-2xl font-display font-black text-white uppercase tracking-tighter">No Scenarios Found</h3>
          <p className="text-xs text-white/40 uppercase tracking-widest">Save simulations to compare them side-by-side</p>
        </div>
        <button
          onClick={onBack}
          className="px-8 py-4 bg-accent text-bg font-display font-black uppercase tracking-widest text-xs"
        >
          Back to Dashboard
        </button>
      </div>
    );
  }

  const comparisonData = scenarios.map(s => ({
    name: s.name,
    risk: s.result.riskScore,
    lifespan: s.result.predictedLifespan,
    rate: s.result.corrosionRate * 100, // Scale for visibility
    roi: s.result.projectedROI || 0,
  }));

  return (
    <div className="h-full flex flex-col space-y-8 overflow-y-auto custom-scrollbar pr-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={onBack}
            className="p-3 rounded-full bg-white/5 border border-white/10 text-white/60 hover:text-accent transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h2 className="text-4xl font-display font-black text-white uppercase tracking-tighter">Scenario Comparison</h2>
            <p className="text-xs text-white/40 uppercase tracking-widest">Multi-variable performance analysis</p>
          </div>
        </div>
        <div className="flex items-center gap-2 px-4 py-2 bg-accent/10 border border-accent/20 rounded-full">
          <div className="w-2 h-2 rounded-full bg-accent animate-pulse" />
          <span className="text-[10px] font-mono font-bold text-accent uppercase tracking-widest">
            {scenarios.length} Scenarios Loaded
          </span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Risk & Lifespan Chart */}
        <div className="glass p-8 border border-white/10 space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-display font-black text-white uppercase tracking-tight">Risk vs. Lifespan</h3>
            <ShieldCheck className="w-5 h-5 text-accent" />
          </div>
          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={comparisonData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                <XAxis 
                  dataKey="name" 
                  stroke="rgba(255,255,255,0.4)" 
                  fontSize={10} 
                  tickLine={false}
                  axisLine={false}
                />
                <YAxis stroke="rgba(255,255,255,0.4)" fontSize={10} tickLine={false} axisLine={false} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#0A0A0A', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                  itemStyle={{ fontSize: '12px', fontWeight: 'bold' }}
                />
                <Legend iconType="circle" wrapperStyle={{ fontSize: '10px', textTransform: 'uppercase', letterSpacing: '1px', paddingTop: '20px' }} />
                <Bar dataKey="risk" name="Risk Score" fill="#FF6321" radius={[4, 4, 0, 0]} />
                <Bar dataKey="lifespan" name="Lifespan (Yrs)" fill="#FFFFFF" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Corrosion Rate & ROI Chart */}
        <div className="glass p-8 border border-white/10 space-y-6">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-display font-black text-white uppercase tracking-tight">Degradation & Financials</h3>
            <TrendingDown className="w-5 h-5 text-accent" />
          </div>
          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={comparisonData}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                <XAxis 
                  dataKey="name" 
                  stroke="rgba(255,255,255,0.4)" 
                  fontSize={10} 
                  tickLine={false}
                  axisLine={false}
                />
                <YAxis stroke="rgba(255,255,255,0.4)" fontSize={10} tickLine={false} axisLine={false} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#0A0A0A', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                  itemStyle={{ fontSize: '12px', fontWeight: 'bold' }}
                />
                <Legend iconType="circle" wrapperStyle={{ fontSize: '10px', textTransform: 'uppercase', letterSpacing: '1px', paddingTop: '20px' }} />
                <Bar dataKey="rate" name="Corrosion Rate (x100)" fill="#FF6321" radius={[4, 4, 0, 0]} />
                <Bar dataKey="roi" name="Projected ROI (%)" fill="#FFFFFF" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Detailed Table */}
      <div className="glass border border-white/10 overflow-hidden">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-white/5 border-bottom border-white/10">
              <th className="p-6 text-[10px] font-mono font-bold text-white/40 uppercase tracking-widest">Scenario</th>
              <th className="p-6 text-[10px] font-mono font-bold text-white/40 uppercase tracking-widest">Material</th>
              <th className="p-6 text-[10px] font-mono font-bold text-white/40 uppercase tracking-widest">Risk</th>
              <th className="p-6 text-[10px] font-mono font-bold text-white/40 uppercase tracking-widest">Lifespan</th>
              <th className="p-6 text-[10px] font-mono font-bold text-white/40 uppercase tracking-widest">Rate</th>
              <th className="p-6 text-[10px] font-mono font-bold text-white/40 uppercase tracking-widest">ROI</th>
            </tr>
          </thead>
          <tbody>
            {scenarios.map((s, idx) => (
              <tr key={s.id} className="border-b border-white/5 hover:bg-white/[0.02] transition-colors">
                <td className="p-6">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded bg-accent/20 flex items-center justify-center text-accent font-mono text-xs font-bold">
                      {idx + 1}
                    </div>
                    <span className="font-display font-bold text-white">{s.name}</span>
                  </div>
                </td>
                <td className="p-6 text-xs text-white/60 uppercase tracking-widest font-bold">{s.data.material}</td>
                <td className="p-6">
                  <div className="flex items-center gap-2">
                    <div className={`w-2 h-2 rounded-full ${s.result.riskScore > 70 ? 'bg-red-500' : s.result.riskScore > 40 ? 'bg-yellow-500' : 'bg-green-500'}`} />
                    <span className="font-mono font-bold text-white">{s.result.riskScore}%</span>
                  </div>
                </td>
                <td className="p-6 font-mono font-bold text-white">{s.result.predictedLifespan} Yrs</td>
                <td className="p-6 font-mono font-bold text-white">{s.result.corrosionRate.toFixed(3)} mm/y</td>
                <td className="p-6 font-mono font-bold text-accent">+{s.result.projectedROI}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default ComparisonView;
