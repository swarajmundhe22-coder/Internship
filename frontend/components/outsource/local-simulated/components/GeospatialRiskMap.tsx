import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Globe, MapPin, ShieldAlert, Info, Layers, Navigation, Search } from 'lucide-react';

interface Props {
  onBack: () => void;
}

const GeospatialRiskMap = ({ onBack }: Props) => {
  const [activeLayer, setActiveLayer] = useState<'corrosivity' | 'salinity' | 'humidity'>('corrosivity');

  const hotspots = [
    { id: 1, x: '25%', y: '40%', name: 'North Sea Platform A', risk: 88, status: 'Critical' },
    { id: 2, x: '65%', y: '55%', name: 'Gulf Pipeline Segment 4', risk: 62, status: 'High' },
    { id: 3, x: '45%', y: '75%', name: 'Coastal Bridge B-12', risk: 45, status: 'Medium' },
    { id: 4, x: '80%', y: '30%', name: 'Arctic Storage Tank', risk: 12, status: 'Low' },
  ];

  return (
    <div className="h-full flex flex-col space-y-8 overflow-y-auto custom-scrollbar pr-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-4xl font-display font-black text-white uppercase tracking-tighter">Geospatial Risk Mapping</h2>
          <p className="text-xs text-white/40 uppercase tracking-widest">Global asset monitoring & environmental overlays</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex bg-white/5 border border-white/10 rounded-full p-1">
            {['corrosivity', 'salinity', 'humidity'].map((layer) => (
              <button
                key={layer}
                onClick={() => setActiveLayer(layer as any)}
                className={`px-4 py-1.5 rounded-full text-[8px] font-mono font-bold uppercase tracking-widest transition-all ${
                  activeLayer === layer ? 'bg-accent text-bg' : 'text-white/40 hover:text-white'
                }`}
              >
                {layer}
              </button>
            ))}
          </div>
          <button
            onClick={onBack}
            className="px-6 py-3 bg-white/5 border border-white/10 text-white font-display font-bold uppercase tracking-widest text-[10px] hover:bg-white/10 transition-all"
          >
            Back
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 flex-1 min-h-0">
        {/* Map View */}
        <div className="lg:col-span-9 glass border border-white/10 relative overflow-hidden bg-black/40 group">
          {/* Mock Map Background */}
          <div className="absolute inset-0 opacity-20 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] pointer-events-none" />
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <Globe className="w-96 h-96 text-white/5 animate-pulse" />
          </div>

          {/* Grid Overlay */}
          <div className="absolute inset-0 grid grid-cols-12 grid-rows-12 pointer-events-none">
            {Array.from({ length: 144 }).map((_, i) => (
              <div key={i} className="border-[0.5px] border-white/[0.02]" />
            ))}
          </div>

          {/* Hotspots */}
          {hotspots.map((spot) => (
            <motion.div
              key={spot.id}
              initial={{ scale: 0, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ delay: spot.id * 0.2 }}
              style={{ left: spot.x, top: spot.y }}
              className="absolute group/pin cursor-pointer"
            >
              <div className="relative">
                <div className={`w-4 h-4 rounded-full animate-ping absolute inset-0 ${
                  spot.status === 'Critical' ? 'bg-red-500' : spot.status === 'High' ? 'bg-orange-500' : 'bg-accent'
                }`} />
                <div className={`w-4 h-4 rounded-full relative z-10 border-2 border-white ${
                  spot.status === 'Critical' ? 'bg-red-500' : spot.status === 'High' ? 'bg-orange-500' : 'bg-accent'
                }`} />
                
                {/* Tooltip */}
                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-4 opacity-0 group-hover/pin:opacity-100 transition-all pointer-events-none z-50">
                  <div className="glass p-4 border border-white/10 w-48 space-y-2">
                    <div className="flex justify-between items-center">
                      <span className="text-[8px] font-mono font-bold text-white/40 uppercase tracking-widest">Asset ID: {spot.id}</span>
                      <span className={`text-[8px] font-mono font-bold uppercase tracking-widest ${
                        spot.status === 'Critical' ? 'text-red-500' : 'text-accent'
                      }`}>{spot.status}</span>
                    </div>
                    <p className="text-xs font-display font-bold text-white uppercase tracking-tight">{spot.name}</p>
                    <div className="flex items-center justify-between pt-2 border-t border-white/5">
                      <span className="text-[8px] font-mono font-bold text-white/20 uppercase tracking-widest">Risk Score</span>
                      <span className="text-xs font-display font-bold text-white">{spot.risk}%</span>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          ))}

          {/* Map Controls */}
          <div className="absolute bottom-8 left-8 flex flex-col gap-2 z-20">
            <button className="p-3 bg-black/60 border border-white/10 text-white hover:text-accent transition-colors">
              <Plus className="w-4 h-4" />
            </button>
            <button className="p-3 bg-black/60 border border-white/10 text-white hover:text-accent transition-colors">
              <Navigation className="w-4 h-4" />
            </button>
            <button className="p-3 bg-black/60 border border-white/10 text-white hover:text-accent transition-colors">
              <Layers className="w-4 h-4" />
            </button>
          </div>

          <div className="absolute top-8 right-8 z-20">
            <div className="glass px-4 py-2 border border-white/10 flex items-center gap-3">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-red-500" />
                <span className="text-[8px] font-mono font-bold text-white/40 uppercase tracking-widest">Critical</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-orange-500" />
                <span className="text-[8px] font-mono font-bold text-white/40 uppercase tracking-widest">High</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-accent" />
                <span className="text-[8px] font-mono font-bold text-white/40 uppercase tracking-widest">Nominal</span>
              </div>
            </div>
          </div>
        </div>

        {/* Sidebar: Regional Insights */}
        <div className="lg:col-span-3 space-y-6">
          <div className="glass p-8 border border-white/10 space-y-6">
            <div className="flex items-center gap-3 text-white">
              <ShieldAlert className="w-5 h-5 text-accent" />
              <h3 className="text-lg font-display font-black uppercase tracking-tight">Regional Alerts</h3>
            </div>
            <div className="space-y-4">
              {[
                { region: 'North Sea', alert: 'Storm Surge Expected', risk: '+12%' },
                { region: 'Gulf Coast', alert: 'High Salinity Ingress', risk: '+8%' },
                { region: 'Arctic', alert: 'Temperature Anomaly', risk: '-5%' },
              ].map((alert) => (
                <div key={alert.region} className="p-4 bg-white/5 border border-white/10 rounded-xl space-y-1">
                  <div className="flex justify-between items-center">
                    <p className="text-[8px] font-mono font-bold text-white/20 uppercase tracking-widest">{alert.region}</p>
                    <span className="text-[8px] font-mono font-bold text-accent">{alert.risk}</span>
                  </div>
                  <p className="text-xs font-display font-bold text-white">{alert.alert}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="glass p-8 border border-white/10 space-y-6">
            <div className="flex items-center gap-3 text-white">
              <Info className="w-5 h-5 text-accent" />
              <h3 className="text-lg font-display font-black uppercase tracking-tight">Data Sources</h3>
            </div>
            <ul className="space-y-3">
              {['NOAA Marine Data', 'Copernicus Sentinel-1', 'IoT Sensor Mesh', 'Historical Surveys'].map((source) => (
                <li key={source} className="flex items-center gap-3 text-[10px] font-mono font-bold text-white/40 uppercase tracking-widest">
                  <div className="w-1.5 h-1.5 bg-accent rounded-full" />
                  {source}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

const Plus = ({ className }: { className?: string }) => (
  <svg className={className} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
);

export default GeospatialRiskMap;
