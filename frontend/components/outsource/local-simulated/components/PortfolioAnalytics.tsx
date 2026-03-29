import React from 'react';
import { motion } from 'framer-motion';
import { BarChart3, TrendingUp, ShieldAlert, Database, Globe, ArrowUpRight, ArrowDownRight, Zap } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

interface Props {
  projects: any[];
  onBack: () => void;
}

const PortfolioAnalytics = ({ projects, onBack }: Props) => {
  const totalValue = projects.reduce((acc, p) => acc + (p.parameters?.assetValue || 0), 0);
  const avgRisk = projects.reduce((acc, p) => acc + (p.scenarios?.[0]?.result?.riskScore || 0), 0) / (projects.length || 1);
  const totalDowntime = projects.reduce((acc, p) => acc + (p.parameters?.downtimeCost || 0), 0);

  const riskData = [
    { name: 'Critical', value: projects.filter(p => (p.scenarios?.[0]?.result?.riskScore || 0) > 70).length, color: '#FF6321' },
    { name: 'High', value: projects.filter(p => (p.scenarios?.[0]?.result?.riskScore || 0) > 40 && (p.scenarios?.[0]?.result?.riskScore || 0) <= 70).length, color: '#FFD700' },
    { name: 'Low', value: projects.filter(p => (p.scenarios?.[0]?.result?.riskScore || 0) <= 40).length, color: '#00FF00' },
  ].filter(d => d.value > 0);

  const timelineData = [
    { month: 'Jan', value: 45 },
    { month: 'Feb', value: 52 },
    { month: 'Mar', value: 48 },
    { month: 'Apr', value: 61 },
    { month: 'May', value: 55 },
    { month: 'Jun', value: 67 },
  ];

  return (
    <div className="h-full flex flex-col space-y-8 overflow-y-auto custom-scrollbar pr-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-4xl font-display font-black text-white uppercase tracking-tighter">Portfolio Analytics</h2>
          <p className="text-xs text-white/40 uppercase tracking-widest">Aggregated asset risk & financial exposure</p>
        </div>
        <button
          onClick={onBack}
          className="px-6 py-3 bg-white/5 border border-white/10 text-white font-display font-bold uppercase tracking-widest text-[10px] hover:bg-white/10 transition-all"
        >
          Back
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[
          { label: 'Total Asset Value', value: `$${(totalValue / 1000000000).toFixed(2)}B`, trend: '+12.4%', icon: Database },
          { label: 'Avg Portfolio Risk', value: `${avgRisk.toFixed(1)}%`, trend: '-2.1%', icon: ShieldAlert },
          { label: 'Daily Downtime Risk', value: `$${(totalDowntime / 1000000).toFixed(1)}M`, trend: '+5.8%', icon: Zap },
          { label: 'Assets Monitored', value: projects.length, trend: '+3', icon: Globe },
        ].map((stat, i) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className="glass p-8 border border-white/5 space-y-4"
          >
            <div className="flex items-center justify-between">
              <stat.icon className="w-5 h-5 text-accent" />
              <div className={`flex items-center gap-1 text-[10px] font-mono font-bold uppercase tracking-widest ${stat.trend.startsWith('+') ? 'text-green-500' : 'text-red-500'}`}>
                {stat.trend.startsWith('+') ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
                {stat.trend}
              </div>
            </div>
            <div className="space-y-1">
              <p className="text-[10px] font-mono font-bold text-white/40 uppercase tracking-widest">{stat.label}</p>
              <p className="text-3xl font-display font-black text-white">{stat.value}</p>
            </div>
          </motion.div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Risk Distribution */}
        <div className="lg:col-span-4 glass p-8 border border-white/10 space-y-8">
          <h3 className="text-xl font-display font-black text-white uppercase tracking-tighter">Risk Distribution</h3>
          <div className="h-[300px] w-full relative">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={riskData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {riskData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ backgroundColor: '#0A0A0A', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
                  itemStyle={{ fontSize: '12px', fontWeight: 'bold' }}
                />
              </PieChart>
            </ResponsiveContainer>
            <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
              <p className="text-2xl font-display font-black text-white">{projects.length}</p>
              <p className="text-[8px] font-mono font-bold text-white/40 uppercase tracking-widest">Assets</p>
            </div>
          </div>
          <div className="space-y-4">
            {riskData.map((d) => (
              <div key={d.name} className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 rounded-full" style={{ backgroundColor: d.color }} />
                  <span className="text-[10px] font-mono font-bold text-white/40 uppercase tracking-widest">{d.name}</span>
                </div>
                <span className="text-xs font-display font-bold text-white">{d.value}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Portfolio Value at Risk */}
        <div className="lg:col-span-8 glass p-8 border border-white/10 space-y-8">
          <div className="flex items-center justify-between">
            <h3 className="text-xl font-display font-black text-white uppercase tracking-tighter">Portfolio Value at Risk (VaR)</h3>
            <div className="flex gap-2">
              {['1M', '3M', '6M', '1Y'].map((t) => (
                <button key={t} className={`px-3 py-1 text-[8px] font-mono font-bold uppercase tracking-widest border ${t === '6M' ? 'border-accent text-accent' : 'border-white/10 text-white/40'}`}>
                  {t}
                </button>
              ))}
            </div>
          </div>
          <div className="h-[300px] w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={timelineData}>
                <defs>
                  <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#FF6321" stopOpacity={0.3}/>
                    <stop offset="95%" stopColor="#FF6321" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" vertical={false} />
                <XAxis 
                  dataKey="month" 
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
                <Area type="monotone" dataKey="value" stroke="#FF6321" fillOpacity={1} fill="url(#colorValue)" strokeWidth={3} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PortfolioAnalytics;
