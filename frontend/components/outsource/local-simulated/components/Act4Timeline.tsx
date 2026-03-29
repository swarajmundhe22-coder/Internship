import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area, BarChart, Bar } from 'recharts';
import { Clock, ShieldAlert, TrendingDown, Activity, DollarSign, AlertTriangle, Info, Zap, Layers, Target } from 'lucide-react';

interface Props {
  result: any;
  narrative: string;
  onNext: () => void;
}

const Act4Timeline = ({ result, narrative, onNext }: Props) => {
  const [year, setYear] = useState(0);
  const [viewMode, setViewMode] = useState<'integrity' | 'financial' | 'probability'>('integrity');

  const currentData = result.degradationTimeline.find((d: any) => d.year === year) || result.degradationTimeline[0];
  
  const assetValue = result.inputData?.assetValue || 50000000;
  const downtimeCost = result.inputData?.downtimeCost || 250000;
  
  const financialTimeline = useMemo(() => result.degradationTimeline.map((d: any) => {
    const degradationFactor = (100 - d.thickness) / 100;
    const riskValue = assetValue * Math.pow(degradationFactor, 2);
    // Sigmoid-like probability curve
    const probabilityOfFailure = 1 / (1 + Math.exp(-10 * (degradationFactor - 0.5)));
    const expectedLoss = riskValue + (probabilityOfFailure * downtimeCost * 30);
    
    return {
      ...d,
      expectedLoss: Math.round(expectedLoss),
      riskLevel: degradationFactor * 100,
      pof: probabilityOfFailure * 100,
    };
  }), [result, assetValue, downtimeCost]);

  const currentFinancial = financialTimeline.find((d: any) => d.year === year) || financialTimeline[0];

  return (
    <div className="relative w-full h-screen bg-bg flex flex-col items-center justify-center overflow-hidden p-4 md:p-12">
      {/* Dynamic Background */}
      <div className="absolute inset-0 z-0 opacity-10 pointer-events-none">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,var(--color-accent),transparent_70%)]" />
        <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 mix-blend-overlay" />
      </div>

      <div className="relative z-10 w-full max-w-7xl h-full flex flex-col gap-6 md:gap-8 overflow-y-auto custom-scrollbar">
        {/* Header */}
        <div className="flex flex-col lg:flex-row justify-between items-start lg:items-end gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-3">
              <Clock className="w-5 h-5 md:w-6 md:h-6 text-accent animate-pulse" />
              <h2 className="text-3xl md:text-5xl font-display font-black uppercase tracking-tighter text-white">Temporal Analysis</h2>
            </div>
            <p className="text-[8px] md:text-[10px] font-sans uppercase tracking-[0.3em] md:tracking-[0.5em] text-white/40">Predictive Degradation Lifecycle v4.0</p>
          </div>
          <div className="flex flex-wrap gap-2 md:gap-4 w-full lg:w-auto">
            <button 
              onClick={() => setViewMode('integrity')}
              className={`flex-1 lg:flex-none px-4 md:px-6 py-2 text-[8px] md:text-[10px] font-display font-bold uppercase tracking-widest border transition-all ${viewMode === 'integrity' ? 'bg-accent text-bg border-accent' : 'text-white/40 border-white/10 hover:border-white/20'}`}
            >
              Integrity View
            </button>
            <button 
              onClick={() => setViewMode('financial')}
              className={`flex-1 lg:flex-none px-4 md:px-6 py-2 text-[8px] md:text-[10px] font-display font-bold uppercase tracking-widest border transition-all ${viewMode === 'financial' ? 'bg-red-500 text-white border-red-500' : 'text-white/40 border-white/10 hover:border-white/20'}`}
            >
              Financial Risk
            </button>
            <button 
              onClick={() => setViewMode('probability')}
              className={`flex-1 lg:flex-none px-4 md:px-6 py-2 text-[8px] md:text-[10px] font-display font-bold uppercase tracking-widest border transition-all ${viewMode === 'probability' ? 'bg-orange-500 text-white border-orange-500' : 'text-white/40 border-white/10 hover:border-white/20'}`}
            >
              Probability (PoF)
            </button>
          </div>
        </div>

        <div className="flex-1 grid grid-cols-1 lg:grid-cols-4 gap-6 md:gap-8 min-h-0">
          {/* Left Column: AI & Metrics */}
          <div className="lg:col-span-1 flex flex-col gap-6 max-h-[400px] lg:max-h-none">
            <div className="glass p-6 rounded-none border-l-2 border-accent space-y-4">
              <div className="flex items-center gap-2 text-accent">
                <Zap className="w-4 h-4" />
                <span className="text-[10px] font-display font-bold uppercase tracking-widest">AI Strategic Briefing</span>
              </div>
              <p className="text-xs text-white/70 leading-relaxed font-serif italic">
                {narrative || "Synthesizing temporal data points for executive summary..."}
              </p>
            </div>

            <div className="flex-1 glass p-6 rounded-none border border-white/5 space-y-8 overflow-y-auto custom-scrollbar">
              <div className="space-y-4">
                <h3 className="text-[9px] font-display font-bold uppercase tracking-widest text-white/40">Critical Metrics</h3>
                <div className="space-y-4">
                  <div className="p-4 bg-white/5 border border-white/5 rounded-none">
                    <p className="text-[8px] uppercase tracking-widest text-white/30 mb-1">Current Integrity</p>
                    <p className="text-3xl font-display font-black text-white">{currentData.thickness}%</p>
                    <div className="w-full h-1 bg-white/5 mt-2">
                      <motion.div 
                        initial={{ width: 0 }}
                        animate={{ width: `${currentData.thickness}%` }}
                        className={`h-full ${currentData.thickness < 50 ? 'bg-red-500' : 'bg-accent'}`}
                      />
                    </div>
                  </div>
                  <div className="p-4 bg-white/5 border border-white/5 rounded-none">
                    <p className="text-[8px] uppercase tracking-widest text-white/30 mb-1">Financial Exposure</p>
                    <p className="text-3xl font-display font-black text-red-500">${(currentFinancial.expectedLoss / 1000000).toFixed(2)}M</p>
                  </div>
                  <div className="p-4 bg-white/5 border border-white/5 rounded-none">
                    <p className="text-[8px] uppercase tracking-widest text-white/30 mb-1">Est. Failure Year</p>
                    <p className="text-3xl font-display font-black text-white">Yr {Math.round(result.predictedLifespan)}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Middle Column: Main Visualization */}
          <div className="lg:col-span-2 flex flex-col gap-6 min-h-[300px] md:min-h-[400px] lg:min-h-0">
            <div className="flex-1 glass p-4 md:p-8 rounded-none border border-white/5 relative overflow-hidden">
              <div className="absolute top-4 left-4 md:top-8 md:left-8 flex items-center gap-2 z-10">
                <Target className="w-3 h-3 md:w-4 md:h-4 text-accent" />
                <span className="text-[8px] md:text-[10px] font-display font-bold uppercase tracking-widest text-white/40">
                  {viewMode === 'integrity' ? 'Degradation Curve' : 'Risk Accumulation'}
                </span>
              </div>
              
              <ResponsiveContainer width="100%" height="100%">
                {viewMode === 'integrity' ? (
                  <AreaChart data={financialTimeline} margin={{ top: 40, right: 20, left: 0, bottom: 0 }}>
                    <defs>
                      <linearGradient id="colorIntegrity" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="var(--color-accent)" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="var(--color-accent)" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#ffffff05" vertical={false} />
                    <XAxis dataKey="year" stroke="#ffffff20" fontSize={10} tickFormatter={(v) => `Yr ${v}`} />
                    <YAxis stroke="#ffffff20" fontSize={10} domain={[0, 100]} tickFormatter={(v) => `${v}%`} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#0a0a0a', border: '1px solid #ffffff10', borderRadius: '0px', fontSize: '10px' }}
                      itemStyle={{ color: 'var(--color-accent)' }}
                    />
                    <Area
                      type="monotone"
                      dataKey="thickness"
                      stroke="var(--color-accent)"
                      strokeWidth={3}
                      fillOpacity={1}
                      fill="url(#colorIntegrity)"
                    />
                  </AreaChart>
                ) : viewMode === 'financial' ? (
                  <BarChart data={financialTimeline} margin={{ top: 40, right: 20, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#ffffff05" vertical={false} />
                    <XAxis dataKey="year" stroke="#ffffff20" fontSize={10} tickFormatter={(v) => `Yr ${v}`} />
                    <YAxis stroke="#ffffff20" fontSize={10} tickFormatter={(v) => `$${(v / 1000000).toFixed(1)}M`} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#0a0a0a', border: '1px solid #ffffff10', borderRadius: '0px', fontSize: '10px' }}
                      itemStyle={{ color: '#ef4444' }}
                      formatter={(v: any) => [`$${v.toLocaleString()}`, 'Expected Loss']}
                    />
                    <Bar dataKey="expectedLoss" fill="#ef4444" opacity={0.6} />
                  </BarChart>
                ) : (
                  <LineChart data={financialTimeline} margin={{ top: 40, right: 20, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#ffffff05" vertical={false} />
                    <XAxis dataKey="year" stroke="#ffffff20" fontSize={10} tickFormatter={(v) => `Yr ${v}`} />
                    <YAxis stroke="#ffffff20" fontSize={10} domain={[0, 100]} tickFormatter={(v) => `${v}%`} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#0a0a0a', border: '1px solid #ffffff10', borderRadius: '0px', fontSize: '10px' }}
                      itemStyle={{ color: '#f97316' }}
                      formatter={(v: any) => [`${v.toFixed(2)}%`, 'PoF']}
                    />
                    <Line
                      type="monotone"
                      dataKey="pof"
                      stroke="#f97316"
                      strokeWidth={3}
                      dot={{ fill: '#f97316', r: 4 }}
                    />
                  </LineChart>
                )}
              </ResponsiveContainer>
            </div>

            <div className="glass p-8 rounded-none border border-white/5 space-y-6">
              <div className="flex justify-between items-center">
                <div className="flex items-center gap-4">
                  <span className="text-[10px] font-display font-bold uppercase tracking-widest text-white/40">Simulation Scrub</span>
                  <div className="px-3 py-1 bg-accent/10 border border-accent/20 text-accent text-[10px] font-mono font-bold">
                    YEAR {year.toString().padStart(2, '0')}
                  </div>
                </div>
                <div className="flex gap-2">
                  {[0, 5, 10, 15, 20].map(y => (
                    <button 
                      key={y}
                      onClick={() => setYear(y)}
                      className={`w-8 h-8 flex items-center justify-center text-[10px] font-mono border transition-all ${year === y ? 'bg-accent text-bg border-accent' : 'text-white/40 border-white/10 hover:border-white/20'}`}
                    >
                      {y}
                    </button>
                  ))}
                </div>
              </div>
              <input
                type="range"
                min="0"
                max="20"
                step="5"
                value={year}
                onChange={(e) => setYear(parseInt(e.target.value))}
                className="w-full h-1 bg-white/5 rounded-none appearance-none cursor-pointer accent-accent"
              />
            </div>
          </div>

          {/* Right Column: Risk Heatmap & Actions */}
          <div className="lg:col-span-1 flex flex-col gap-6">
            <div className="flex-1 glass p-6 rounded-none border border-white/5 space-y-6">
              <h3 className="text-[9px] font-display font-bold uppercase tracking-widest text-white/40 flex items-center gap-2">
                <Layers className="w-3 h-3" /> Risk Heatmap
              </h3>
              <div className="grid grid-cols-1 gap-1">
                {financialTimeline.map((d: any) => (
                  <div key={d.year} className="flex items-center gap-4 group cursor-pointer" onClick={() => setYear(d.year)}>
                    <span className="text-[8px] font-mono text-white/20 w-8">YR {d.year}</span>
                    <div className="flex-1 h-8 bg-white/5 relative overflow-hidden border border-white/5 group-hover:border-white/20 transition-all">
                      <div 
                        className="absolute inset-0 transition-all duration-500"
                        style={{ 
                          width: `${d.riskLevel}%`,
                          backgroundColor: d.riskLevel > 50 ? '#ef4444' : 'var(--color-accent)',
                          opacity: d.riskLevel / 100
                        }}
                      />
                      <div className="absolute inset-0 flex items-center justify-center">
                        <span className="text-[8px] font-mono font-bold text-white opacity-0 group-hover:opacity-100 transition-opacity">
                          {d.riskLevel.toFixed(1)}% RISK
                        </span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <motion.button
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              onClick={onNext}
              className="w-full py-6 bg-accent text-bg font-display font-black uppercase tracking-[0.4em] text-xs rounded-none hover:brightness-110 transition-all shadow-2xl shadow-accent/20 flex items-center justify-center gap-3"
            >
              <FileTextIcon className="w-4 h-4" /> Finalize Blueprint
            </motion.button>
          </div>
        </div>
      </div>

      {/* Scanning Line */}
      <motion.div 
        animate={{ top: ['0%', '100%', '0%'] }}
        transition={{ duration: 15, repeat: Infinity, ease: "linear" }}
        className="absolute left-0 w-full h-[1px] bg-accent/10 z-20 pointer-events-none"
      />
    </div>
  );
};

const FileTextIcon = ({ className }: { className?: string }) => (
  <svg className={className} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><line x1="10" y1="9" x2="8" y2="9"/></svg>
);

export default Act4Timeline;

