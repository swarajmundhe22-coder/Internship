import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area, BarChart, Bar, ReferenceArea, ReferenceLine } from 'recharts';
import { Clock, ShieldAlert, TrendingDown, Activity, DollarSign, AlertTriangle, Info, Zap, Layers, Target, Download } from 'lucide-react';

interface Props {
  result: any;
  narrative: string;
  onNext: () => void;
}

const ACCENT_HEX = '#c9ff57';
const MAX_DISPLAY_LIFESPAN = 200;

function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}

function triggerCsvDownload(fileName: string, rows: Array<Record<string, string | number>>) {
  if (typeof window === 'undefined' || rows.length === 0) {
    return;
  }

  const headers = Object.keys(rows[0]);
  const csvLines = [
    headers.join(','),
    ...rows.map((row) => headers.map((header) => row[header]).join(',')),
  ];
  const csvContent = csvLines.join('\n');

  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = fileName;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  URL.revokeObjectURL(url);
}

const Act4Timeline = ({ result, narrative, onNext }: Props) => {
  const [year, setYear] = useState(0);
  const [viewMode, setViewMode] = useState<'integrity' | 'financial' | 'probability'>('integrity');

  const degradationTimeline = useMemo(() => {
    if (Array.isArray(result?.degradationTimeline) && result.degradationTimeline.length > 0) {
      return result.degradationTimeline;
    }

    return [
      { year: 0, thickness: 100 },
      { year: 5, thickness: 94 },
      { year: 10, thickness: 88 },
      { year: 15, thickness: 82 },
      { year: 20, thickness: 76 },
    ];
  }, [result?.degradationTimeline]);

  const uncertaintyBands = result?.uncertaintyBands;
  const designRateBand = uncertaintyBands?.designCorrosionRate ?? uncertaintyBands?.corrosionRate;
  const confidencePercent = Math.round(
    clamp(Number(designRateBand?.confidenceLevel ?? uncertaintyBands?.riskScore?.confidenceLevel ?? 0.9) * 100, 1, 99)
  );

  const timelineWithUncertainty = useMemo(() => {
    const initialThicknessMm = Number(result?.initialThicknessMm ?? 12);
    if (!Number.isFinite(initialThicknessMm) || initialThicknessMm <= 0 || !designRateBand) {
      return degradationTimeline.map((d: any) => {
        const thickness = clamp(Number(d.thickness ?? 100), 0, 100);
        return {
          ...d,
          thickness,
          thicknessLow: thickness,
          thicknessHigh: thickness,
        };
      });
    }

    const lowerRate = clamp(Number(designRateBand.lower), 0, 10);
    const upperRate = clamp(Number(designRateBand.upper), lowerRate, 10);

    return degradationTimeline.map((d: any) => {
      const year = Number(d.year ?? 0);
      const thickness = clamp(Number(d.thickness ?? 100), 0, 100);
      const highRemainingMm = Math.max(initialThicknessMm - lowerRate * year, 0);
      const lowRemainingMm = Math.max(initialThicknessMm - upperRate * year, 0);
      const thicknessHigh = clamp((highRemainingMm / initialThicknessMm) * 100, 0, 100);
      const thicknessLow = clamp((lowRemainingMm / initialThicknessMm) * 100, 0, 100);

      return {
        ...d,
        thickness,
        thicknessLow: Number(thicknessLow.toFixed(2)),
        thicknessHigh: Number(thicknessHigh.toFixed(2)),
      };
    });
  }, [degradationTimeline, result?.initialThicknessMm, designRateBand]);

  const currentData = timelineWithUncertainty.find((d: any) => d.year === year) || timelineWithUncertainty[0];
  
  const assetValue = Number(result?.inputData?.assetValue ?? 50000000);
  const downtimeCost = Number(result?.inputData?.downtimeCost ?? 250000);
  
  const financialTimeline = useMemo(() => timelineWithUncertainty.map((d: any) => {
    const thickness = clamp(Number(d.thickness ?? 100), 0, 100);
    const degradationFactor = clamp((100 - thickness) / 100, 0, 1);
    const riskValue = assetValue * Math.pow(degradationFactor, 2);
    // Sigmoid-like probability curve
    const probabilityOfFailure = 1 / (1 + Math.exp(-10 * (degradationFactor - 0.5)));
    const expectedLoss = riskValue + (probabilityOfFailure * downtimeCost * 30);
    
    return {
      ...d,
      thickness,
      thicknessLow: d.thicknessLow,
      thicknessHigh: d.thicknessHigh,
      expectedLoss: Math.round(expectedLoss),
      riskLevel: clamp(degradationFactor * 100, 0, 100),
      pof: probabilityOfFailure * 100,
    };
  }), [timelineWithUncertainty, assetValue, downtimeCost]);

  const currentFinancial = financialTimeline.find((d: any) => d.year === year) || financialTimeline[0];
  const predictedLifespan = Number.isFinite(result?.predictedLifespan) ? Number(result.predictedLifespan) : 0;
  const displayedCorrosionRate = Number(result?.designCorrosionRate ?? result?.corrosionRate ?? 0);
  const riskScoreBand = uncertaintyBands?.riskScore;
  const lifespanBand = uncertaintyBands?.predictedLifespan;
  const riskScoreCenter = clamp(Number(result?.riskScore ?? currentFinancial.riskLevel ?? 0), 0, 100);
  const riskBandHalfWidth = riskScoreBand
    ? clamp((Number(riskScoreBand.upper) - Number(riskScoreBand.lower)) / 2, 0, 50)
    : 0;
  const displayFailureYear =
    predictedLifespan > MAX_DISPLAY_LIFESPAN
      ? `${MAX_DISPLAY_LIFESPAN}+`
      : `${Math.max(1, Math.round(predictedLifespan))}`;

  const chartYearMin = Math.min(...financialTimeline.map((d: any) => Number(d.year ?? 0)));
  const chartYearMax = Math.max(...financialTimeline.map((d: any) => Number(d.year ?? 0)));
  const lifespanWindow = lifespanBand
    ? {
        start: clamp(Number(lifespanBand.lower), chartYearMin, chartYearMax),
        end: clamp(Number(lifespanBand.upper), chartYearMin, chartYearMax),
      }
    : null;

  const timelineForChart = useMemo(() => {
    const lifespanLower = Number(lifespanBand?.lower ?? predictedLifespan);
    const lifespanUpper = Number(lifespanBand?.upper ?? predictedLifespan);

    return financialTimeline.map((d: any) => {
      const temporalFactor = clamp((Number(d.year ?? 0) + 2) / 22, 0.08, 1);
      const riskCenter = clamp(riskScoreCenter * temporalFactor, 0, 100);
      const riskCiLower = clamp(riskCenter - riskBandHalfWidth, 0, 100);
      const riskCiUpper = clamp(riskCenter + riskBandHalfWidth, riskCiLower, 100);

      const year = Number(d.year ?? 0);
      const remainingLifespan = clamp(predictedLifespan - year, 0, MAX_DISPLAY_LIFESPAN);
      const lifespanCiLower = clamp(lifespanLower - year, 0, MAX_DISPLAY_LIFESPAN);
      const lifespanCiUpper = clamp(lifespanUpper - year, lifespanCiLower, MAX_DISPLAY_LIFESPAN);

      return {
        ...d,
        riskCiLower: Number(riskCiLower.toFixed(2)),
        riskCiUpper: Number(riskCiUpper.toFixed(2)),
        remainingLifespan: Number(remainingLifespan.toFixed(2)),
        lifespanCiLower: Number(lifespanCiLower.toFixed(2)),
        lifespanCiUpper: Number(lifespanCiUpper.toFixed(2)),
      };
    });
  }, [financialTimeline, lifespanBand?.lower, lifespanBand?.upper, predictedLifespan, riskBandHalfWidth, riskScoreCenter]);

  const downloadRiskCiOverlay = () => {
    const rows = timelineForChart.map((d: any) => ({
      year: Number(d.year ?? 0),
      risk_score_ci_lower: Number(d.riskCiLower ?? 0),
      risk_score_ci_upper: Number(d.riskCiUpper ?? 0),
      pof_percent: Number(d.pof ?? 0).toFixed(2),
      confidence_level: Number(riskScoreBand?.confidenceLevel ?? designRateBand?.confidenceLevel ?? 0.9).toFixed(3),
    }));
    triggerCsvDownload(`risk_ci_overlay_${Date.now()}.csv`, rows);
  };

  const downloadLifespanCiOverlay = () => {
    const rows = timelineForChart.map((d: any) => ({
      year: Number(d.year ?? 0),
      remaining_lifespan_center_years: Number(d.remainingLifespan ?? 0),
      remaining_lifespan_ci_lower_years: Number(d.lifespanCiLower ?? 0),
      remaining_lifespan_ci_upper_years: Number(d.lifespanCiUpper ?? 0),
      confidence_level: Number(lifespanBand?.confidenceLevel ?? 0.9).toFixed(3),
    }));
    triggerCsvDownload(`lifespan_ci_overlay_${Date.now()}.csv`, rows);
  };

  const integrityMin = Math.max(0, Math.min(...financialTimeline.map((d: any) => d.thickness)) - 5);
  const integrityMax = Math.min(100, Math.max(...financialTimeline.map((d: any) => d.thickness)) + 2);
  const integrityDomain: [number, number] =
    integrityMax - integrityMin < 8 ? [Math.max(0, integrityMax - 8), 100] : [integrityMin, integrityMax];

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
              {result?.modelVersion ? (
                <p className="text-[9px] font-mono uppercase tracking-widest text-white/40">
                  Model: {result.modelVersion}
                </p>
              ) : null}
              {result?.assetProfile ? (
                <p className="text-[9px] font-mono uppercase tracking-widest text-white/40">
                  Asset Profile: {result.assetProfile}
                </p>
              ) : null}
              {result?.regionName || result?.regionKey ? (
                <p className="text-[9px] font-mono uppercase tracking-widest text-white/40">
                  Region Pack: {result.regionName || result.regionKey}
                </p>
              ) : null}
              {typeof result?.initialThicknessMm === 'number' && typeof result?.minimumSafeThicknessMm === 'number' ? (
                <p className="text-[9px] font-mono uppercase tracking-widest text-white/40">
                  Thickness Thresholds: {result.initialThicknessMm.toFixed(1)}mm init / {result.minimumSafeThicknessMm.toFixed(1)}mm safe
                </p>
              ) : null}
              {designRateBand ? (
                <p className="text-[9px] font-mono uppercase tracking-widest text-white/40">
                  Design Rate CI ({confidencePercent}%): {Number(designRateBand.lower).toFixed(3)}-{Number(designRateBand.upper).toFixed(3)} mm/y
                </p>
              ) : null}
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
                    <p className="text-3xl font-display font-black text-white">Yr {displayFailureYear}</p>
                  </div>
                  <div className="p-4 bg-white/5 border border-white/5 rounded-none">
                    <p className="text-[8px] uppercase tracking-widest text-white/30 mb-1">Design Corrosion Rate</p>
                    <p className="text-3xl font-display font-black text-white">{displayedCorrosionRate.toFixed(3)} mm/y</p>
                  </div>
                  {riskScoreBand ? (
                    <div className="p-4 bg-white/5 border border-white/5 rounded-none">
                      <p className="text-[8px] uppercase tracking-widest text-white/30 mb-1">Risk Score CI</p>
                      <p className="text-3xl font-display font-black text-white">
                        {Number(riskScoreBand.lower).toFixed(1)}-{Number(riskScoreBand.upper).toFixed(1)}
                      </p>
                    </div>
                  ) : null}
                  {lifespanBand ? (
                    <div className="p-4 bg-white/5 border border-white/5 rounded-none">
                      <p className="text-[8px] uppercase tracking-widest text-white/30 mb-1">Lifespan CI</p>
                      <p className="text-3xl font-display font-black text-white">
                        {Number(lifespanBand.lower).toFixed(1)}-{Number(lifespanBand.upper).toFixed(1)} yr
                      </p>
                    </div>
                  ) : null}
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
                  <AreaChart data={timelineForChart} margin={{ top: 40, right: 20, left: 0, bottom: 0 }}>
                    <defs>
                      <linearGradient id="colorIntegrity" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor={ACCENT_HEX} stopOpacity={0.35}/>
                        <stop offset="95%" stopColor={ACCENT_HEX} stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" vertical={false} />
                    <XAxis dataKey="year" stroke="#ffffff55" fontSize={10} tickFormatter={(v) => `Yr ${v}`} />
                    <YAxis stroke="#ffffff55" fontSize={10} domain={integrityDomain} tickFormatter={(v) => `${v}%`} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#0a0a0a', border: '1px solid #ffffff10', borderRadius: '0px', fontSize: '10px' }}
                      itemStyle={{ color: ACCENT_HEX }}
                    />
                    <Area
                      type="monotone"
                      dataKey="thickness"
                      stroke={ACCENT_HEX}
                      strokeWidth={3}
                      fillOpacity={1}
                      fill="url(#colorIntegrity)"
                    />
                    {designRateBand ? (
                      <>
                        <Area
                          type="monotone"
                          dataKey="thicknessHigh"
                          stroke="#f3f4f6"
                          strokeWidth={1.25}
                          strokeDasharray="4 4"
                          fillOpacity={0}
                        />
                        <Area
                          type="monotone"
                          dataKey="thicknessLow"
                          stroke="#9ca3af"
                          strokeWidth={1.25}
                          strokeDasharray="4 4"
                          fillOpacity={0}
                        />
                      </>
                    ) : null}
                    {lifespanWindow ? (
                      <ReferenceArea
                        x1={lifespanWindow.start}
                        x2={lifespanWindow.end}
                        stroke="#38bdf8"
                        fill="#38bdf8"
                        fillOpacity={0.08}
                      />
                    ) : null}
                    {lifespanBand ? (
                      <ReferenceLine
                        x={clamp(Number(predictedLifespan), chartYearMin, chartYearMax)}
                        stroke="#38bdf8"
                        strokeDasharray="5 5"
                      />
                    ) : null}
                  </AreaChart>
                ) : viewMode === 'financial' ? (
                  <BarChart data={timelineForChart} margin={{ top: 40, right: 20, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" vertical={false} />
                    <XAxis dataKey="year" stroke="#ffffff55" fontSize={10} tickFormatter={(v) => `Yr ${v}`} />
                    <YAxis stroke="#ffffff55" fontSize={10} tickFormatter={(v) => `$${(v / 1000000).toFixed(1)}M`} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#0a0a0a', border: '1px solid #ffffff10', borderRadius: '0px', fontSize: '10px' }}
                      itemStyle={{ color: '#ef4444' }}
                      formatter={(v: any) => [`$${v.toLocaleString()}`, 'Expected Loss']}
                    />
                    <Bar dataKey="expectedLoss" fill="#ef4444" opacity={0.6} />
                    {lifespanWindow ? (
                      <ReferenceArea
                        x1={lifespanWindow.start}
                        x2={lifespanWindow.end}
                        stroke="#38bdf8"
                        fill="#38bdf8"
                        fillOpacity={0.08}
                      />
                    ) : null}
                  </BarChart>
                ) : (
                  <LineChart data={timelineForChart} margin={{ top: 40, right: 20, left: 0, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" vertical={false} />
                    <XAxis dataKey="year" stroke="#ffffff55" fontSize={10} tickFormatter={(v) => `Yr ${v}`} />
                    <YAxis stroke="#ffffff55" fontSize={10} domain={[0, 100]} tickFormatter={(v) => `${v}%`} />
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
                    {riskScoreBand ? (
                      <>
                        <Line
                          type="monotone"
                          dataKey="riskCiUpper"
                          stroke="#fde047"
                          strokeWidth={1.25}
                          strokeDasharray="4 4"
                          dot={false}
                        />
                        <Line
                          type="monotone"
                          dataKey="riskCiLower"
                          stroke="#facc15"
                          strokeWidth={1.25}
                          strokeDasharray="4 4"
                          dot={false}
                        />
                      </>
                    ) : null}
                    {lifespanWindow ? (
                      <ReferenceArea
                        x1={lifespanWindow.start}
                        x2={lifespanWindow.end}
                        stroke="#38bdf8"
                        fill="#38bdf8"
                        fillOpacity={0.08}
                      />
                    ) : null}
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
                          width: `${Math.max(d.riskLevel, 6)}%`,
                          backgroundColor: d.riskLevel > 50 ? '#ef4444' : ACCENT_HEX,
                          opacity: Math.max(d.riskLevel / 100, 0.22)
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

            <div className="glass p-4 rounded-none border border-white/5 space-y-3">
              <h3 className="text-[9px] font-display font-bold uppercase tracking-widest text-white/40">Download CI Overlays</h3>
              <button
                onClick={downloadRiskCiOverlay}
                className="w-full py-3 px-4 border border-yellow-300/30 text-yellow-200 text-[10px] font-display font-bold uppercase tracking-widest hover:bg-yellow-300/10 transition-all flex items-center justify-center gap-2"
              >
                <Download className="w-3 h-3" /> Risk CI CSV
              </button>
              <button
                onClick={downloadLifespanCiOverlay}
                className="w-full py-3 px-4 border border-sky-300/30 text-sky-200 text-[10px] font-display font-bold uppercase tracking-widest hover:bg-sky-300/10 transition-all flex items-center justify-center gap-2"
              >
                <Download className="w-3 h-3" /> Lifespan CI CSV
              </button>
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

