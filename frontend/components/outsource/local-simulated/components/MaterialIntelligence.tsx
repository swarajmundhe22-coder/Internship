import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, Database, ShieldCheck, TrendingDown, Info, X, Zap, Thermometer, Droplets } from 'lucide-react';

const MATERIAL_DATABASE = [
  {
    name: 'Carbon Steel (A36)',
    type: 'Ferrous',
    pren: 0,
    potential: -0.65,
    resistance: 20,
    description: 'Standard structural steel. Highly susceptible to atmospheric and aqueous corrosion without protection.',
    properties: { strength: 'High', weldability: 'Excellent', cost: 'Low' }
  },
  {
    name: 'Stainless Steel 316L',
    type: 'Austenitic',
    pren: 25,
    potential: -0.15,
    resistance: 85,
    description: 'Molybdenum-bearing grade. Excellent resistance to chloride pitting and crevice corrosion.',
    properties: { strength: 'Medium', weldability: 'Good', cost: 'High' }
  },
  {
    name: 'Duplex 2205',
    type: 'Duplex',
    pren: 35,
    potential: -0.10,
    resistance: 95,
    description: 'Two-phase microstructure. Combines high strength with exceptional resistance to stress corrosion cracking.',
    properties: { strength: 'Very High', weldability: 'Good', cost: 'Very High' }
  },
  {
    name: 'Inconel 625',
    type: 'Nickel Alloy',
    pren: 50,
    potential: +0.10,
    resistance: 99,
    description: 'Nickel-chromium-molybdenum alloy. Virtually immune to chloride-induced stress corrosion cracking.',
    properties: { strength: 'High', weldability: 'Excellent', cost: 'Extreme' }
  },
  {
    name: 'Titanium Grade 2',
    type: 'Reactive',
    pren: 100,
    potential: +0.20,
    resistance: 100,
    description: 'Commercially pure titanium. Exceptional resistance to seawater and oxidising environments.',
    properties: { strength: 'Medium', weldability: 'Good', cost: 'Extreme' }
  },
  {
    name: 'Aluminum 5083',
    type: 'Non-Ferrous',
    pren: 0,
    potential: -0.90,
    resistance: 75,
    description: 'Magnesium-aluminum alloy. Excellent performance in marine environments and cryogenic applications.',
    properties: { strength: 'Medium', weldability: 'Excellent', cost: 'Medium' }
  }
];

interface Props {
  onBack: () => void;
}

const MaterialIntelligence = ({ onBack }: Props) => {
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState<any>(null);

  const filtered = MATERIAL_DATABASE.filter(m => 
    m.name.toLowerCase().includes(search.toLowerCase()) || 
    m.type.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="h-full flex flex-col space-y-8 overflow-y-auto custom-scrollbar pr-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-4xl font-display font-black text-white uppercase tracking-tighter">Material Intelligence</h2>
          <p className="text-xs text-white/40 uppercase tracking-widest">Advanced alloy database & electrochemical profiles</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-white/20" />
            <input
              type="text"
              placeholder="Search alloys (e.g., Duplex)..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-12 pr-6 py-3 bg-white/5 border border-white/10 rounded-full text-xs text-white focus:outline-none focus:border-accent transition-all w-64"
            />
          </div>
          <button
            onClick={onBack}
            className="px-6 py-3 bg-white/5 border border-white/10 text-white font-display font-bold uppercase tracking-widest text-[10px] hover:bg-white/10 transition-all"
          >
            Back
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 grid grid-cols-1 md:grid-cols-2 gap-4">
          {filtered.map((m, i) => (
            <motion.div
              key={m.name}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              onClick={() => setSelected(m)}
              className={`glass p-6 border ${selected?.name === m.name ? 'border-accent' : 'border-white/5'} hover:border-accent/40 transition-all cursor-pointer group relative overflow-hidden`}
            >
              <div className="flex justify-between items-start mb-4">
                <div className="p-3 bg-white/5 rounded-none group-hover:bg-accent/10 transition-colors">
                  <Database className="w-5 h-5 text-accent" />
                </div>
                <div className="flex flex-col items-end">
                  <span className="text-[8px] font-mono font-bold text-white/20 uppercase tracking-widest">PREN</span>
                  <span className="text-sm font-display font-black text-white">{m.pren}</span>
                </div>
              </div>
              <h3 className="text-lg font-display font-black text-white uppercase tracking-tight mb-1">{m.name}</h3>
              <p className="text-[10px] font-mono font-bold text-accent uppercase tracking-widest mb-4">{m.type}</p>
              
              <div className="grid grid-cols-2 gap-4 pt-4 border-t border-white/5">
                <div className="space-y-1">
                  <p className="text-[8px] font-mono font-bold text-white/20 uppercase tracking-widest">Potential (V)</p>
                  <p className="text-xs font-display font-bold text-white">{m.potential > 0 ? '+' : ''}{m.potential}</p>
                </div>
                <div className="space-y-1">
                  <p className="text-[8px] font-mono font-bold text-white/20 uppercase tracking-widest">Resistance</p>
                  <p className="text-xs font-display font-bold text-accent">{m.resistance}%</p>
                </div>
              </div>
            </motion.div>
          ))}
        </div>

        <div className="lg:col-span-1">
          <AnimatePresence mode="wait">
            {selected ? (
              <motion.div
                key={selected.name}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                className="glass p-8 border border-accent/40 space-y-8 sticky top-0"
              >
                <div className="space-y-2">
                  <h3 className="text-3xl font-display font-black text-white uppercase tracking-tighter leading-none">{selected.name}</h3>
                  <p className="text-xs font-mono font-bold text-accent uppercase tracking-widest">{selected.type} Profile</p>
                </div>

                <p className="text-xs text-white/40 leading-relaxed italic">
                  "{selected.description}"
                </p>

                <div className="space-y-6">
                  <div className="space-y-4">
                    <h4 className="text-[10px] font-mono font-bold text-white/20 uppercase tracking-widest">Performance Metrics</h4>
                    <div className="space-y-4">
                      {Object.entries(selected.properties).map(([key, val]) => (
                        <div key={key} className="flex items-center justify-between">
                          <span className="text-[10px] font-mono font-bold text-white/40 uppercase tracking-widest">{key}</span>
                          <span className="text-xs font-display font-bold text-white uppercase tracking-widest">{val as string}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="pt-8 border-t border-white/5 space-y-4">
                    <div className="flex items-center gap-3">
                      <Zap className="w-4 h-4 text-accent" />
                      <span className="text-[10px] font-mono font-bold text-white/40 uppercase tracking-widest">Electrochemical Signature</span>
                    </div>
                    <div className="p-4 bg-white/5 border border-white/10 rounded-xl space-y-4">
                      <div className="flex justify-between items-center">
                        <span className="text-[10px] font-mono font-bold text-white/20 uppercase tracking-widest">Galvanic Potential</span>
                        <span className="text-xs font-display font-bold text-white">{selected.potential}V vs SCE</span>
                      </div>
                      <div className="w-full h-1 bg-white/5 rounded-full overflow-hidden">
                        <motion.div 
                          initial={{ width: 0 }}
                          animate={{ width: `${Math.abs(selected.potential * 100)}%` }}
                          className="h-full bg-accent"
                        />
                      </div>
                    </div>
                  </div>
                </div>

                <button className="w-full py-4 bg-accent text-bg font-display font-black uppercase tracking-widest text-xs shadow-2xl shadow-accent/20">
                  Apply to Simulation
                </button>
              </motion.div>
            ) : (
              <div className="h-full flex flex-col items-center justify-center space-y-6 opacity-20">
                <Database className="w-16 h-16" />
                <p className="text-xs font-mono font-bold uppercase tracking-widest">Select an alloy to view profile</p>
              </div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
};

export default MaterialIntelligence;
