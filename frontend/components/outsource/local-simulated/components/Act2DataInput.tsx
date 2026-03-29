import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Settings, Droplets, Thermometer, Wind, Zap, Database, DollarSign, Clock, ShieldAlert, Info, X, ChevronRight, HelpCircle, BookOpen } from 'lucide-react';

import { toast } from 'sonner';

interface Props {
  onSimulate: (data: any) => void;
  initialData?: any;
}

const PARAMETER_GUIDES = {
  material: {
    title: "Material Intelligence",
    guide: "Select the primary structural alloy. Different alloys have unique electrochemical potentials. For custom alloys, specify the PREN (Pitting Resistance Equivalent Number) if known. Measurement: Refer to Mill Test Reports (MTR) or ASTM specifications.",
  },
  structure: {
    title: "Structural Context",
    guide: "The geometry and application of the asset. Pipelines face internal/external stress, while bridges face atmospheric chlorides. Measurement: Refer to engineering blueprints and site surveys.",
  },
  compliance: {
    title: "Compliance Standard",
    guide: "Select the regulatory framework. ISO 12944 covers protective paint systems, while NACE SP0169 focuses on external corrosion control for underground/submerged piping.",
  },
  criticality: {
    title: "Asset Criticality",
    guide: "Determines the safety factor in calculations. 'Mission Critical' implies zero-tolerance for failure (e.g., nuclear or high-pressure gas).",
  },
  assetValue: {
    title: "Asset Value",
    guide: "Total replacement cost of the asset in USD. This includes material, labor, and engineering costs for a full reconstruction.",
  },
  downtimeCost: {
    title: "Daily Downtime",
    guide: "Estimated revenue loss per 24 hours of operational stoppage. Include contractual penalties and lost production volume.",
  },
  temperature: {
    title: "Temperature Analysis",
    guide: "Corrosion rates typically double with every 10 C increase (Arrhenius equation). Measurement: Use calibrated thermocouples or SCADA historical averages.",
  },
  humidity: {
    title: "Relative Humidity",
    guide: "Critical for atmospheric corrosion. Above 80% RH, a thin electrolyte film forms on surfaces, accelerating oxidation. Measurement: Hygrometers or local meteorological data.",
  },
  salinity: {
    title: "Salinity (Chlorides)",
    guide: "Chloride ions penetrate protective oxide layers (pitting). Measurement: Conductometric titration or silver nitrate tests (ISO 9227).",
  },
  pH: {
    title: "pH Level",
    guide: "Acidity/Alkalinity. pH < 4 causes rapid acid attack; pH > 10 can cause caustic embrittlement in some steels. Measurement: pH probes or litmus analysis.",
  },
  uvIndex: {
    title: "UV Exposure",
    guide: "Critical for coating degradation. High UV index accelerates polymer breakdown in protective paints. Measurement: UV radiometers or local meteorological data.",
  },
  micActivity: {
    title: "MIC Activity",
    guide: "Microbiologically Influenced Corrosion. Sulfate-reducing bacteria (SRB) can cause localized pitting in anaerobic conditions. Measurement: Biological activity tests or coupon analysis.",
  },
  soilResistivity: {
    title: "Soil Resistivity",
    guide: "Determines the corrosivity of the soil for buried assets. Low resistivity (< 2000 Î©-cm) indicates high corrosivity. Measurement: Wenner four-pin method (ASTM G57).",
  },
  oxygenLevel: {
    title: "Oxygen Concentration",
    guide: "Primary cathodic reactant in aqueous corrosion. High oxygen levels accelerate oxidation in neutral/alkaline environments. Measurement: Dissolved oxygen (DO) probes.",
  }
};

const Act2DataInput = ({ onSimulate, initialData }: Props) => {
  const [formData, setFormData] = useState(initialData || {
    material: 'Carbon Steel',
    customMaterial: '',
    temperature: 25,
    tempRange: [0, 100],
    isCustomTemp: false,
    humidity: 80,
    pH: 7,
    salinity: 35,
    oxygenLevel: 6,
    uvIndex: 5,
    micActivity: 'Low',
    soilResistivity: 5000,
    structure: 'Pipeline',
    customStructure: '',
    assetValue: 50000000,
    downtimeCost: 250000,
    compliance: 'ISO 12944',
    criticality: 'High',
  });

  const [activeGuide, setActiveGuide] = useState<keyof typeof PARAMETER_GUIDES | null>(null);

  const materials = [
    'Carbon Steel (A36/A516)', 
    'Stainless Steel 304', 
    'Stainless Steel 316L', 
    'Duplex Stainless Steel 2205',
    'Aluminum 6061-T6', 
    'Aluminum 5083',
    'Copper-Nickel (90/10)', 
    'Nickel Alloy (Inconel 625)',
    'Titanium Grade 2',
    'Galvanized Steel',
    'Weathering Steel (Corten)',
    'Cast Iron (Ductile)',
    'Custom'
  ];

  const structures = [
    'Pipeline (Submerged)', 
    'Pipeline (Atmospheric)',
    'Bridge (Suspension)', 
    'Bridge (Beam)',
    'Marine Vessel (Hull)', 
    'Storage Tank (AST)', 
    'Offshore Platform (Fixed)',
    'Offshore Platform (FPSO)',
    'Cooling Tower',
    'Reinforced Concrete',
    'Wind Turbine Tower',
    'Custom'
  ];
  const complianceStandards = ['ISO 12944', 'NACE SP0169', 'ASTM G1', 'NORSOK M-501', 'Custom'];
  const criticalityLevels = ['Low', 'Medium', 'High', 'Mission Critical'];

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target as HTMLInputElement;
    const isStringField = ['material', 'structure', 'compliance', 'criticality', 'customMaterial', 'customStructure'].includes(name);
    const isBooleanField = type === 'checkbox';
    
    setFormData((prev: any) => ({ 
      ...prev, 
      [name]: isBooleanField ? (e.target as HTMLInputElement).checked : (isStringField ? value : parseFloat(value)) 
    }));
  };

  const GuidePanel = () => (
    <AnimatePresence>
      {activeGuide && (
        <motion.div
          initial={{ opacity: 0, x: 100, y: 0 }}
          animate={{ opacity: 1, x: 0, y: 0 }}
          exit={{ opacity: 0, x: 100, y: 0 }}
          className="fixed right-0 top-0 h-full w-full md:w-80 lg:w-96 glass border-l border-white/10 z-[70] p-6 md:p-8 flex flex-col gap-6 shadow-2xl overflow-y-auto"
        >
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-display font-bold text-accent uppercase tracking-tighter">Engineering Guide</h3>
            <button onClick={() => setActiveGuide(null)} className="p-2 hover:bg-white/5 rounded-full transition-colors">
              <X className="w-5 h-5 text-white" />
            </button>
          </div>
          
          <div className="space-y-4">
            <h4 className="text-sm font-display font-bold text-white uppercase tracking-widest">{PARAMETER_GUIDES[activeGuide].title}</h4>
            <p className="text-xs text-white/60 leading-relaxed font-serif italic">
              {PARAMETER_GUIDES[activeGuide].guide}
            </p>
          </div>

          <div className="mt-auto space-y-4">
            <div className="p-4 bg-accent/5 border border-accent/10 rounded-xl">
              <p className="text-[10px] text-accent font-bold uppercase tracking-widest mb-2">Pro Tip</p>
              <p className="text-[10px] text-white/40 leading-relaxed">
                Always cross-reference field measurements with at least two independent sensors for high-reliability modeling.
              </p>
            </div>
            
            <button 
              onClick={() => onSimulate({ ...formData, goToManual: true })}
              className="w-full py-4 border border-accent/20 text-accent text-[10px] font-display font-black uppercase tracking-widest hover:bg-accent hover:text-bg transition-all flex items-center justify-center gap-2"
            >
              <BookOpen className="w-3 h-3" /> View Full Engineering Manual
            </button>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );

  const [errors, setErrors] = useState<Record<string, string>>({});

  const validate = () => {
    const newErrors: Record<string, string> = {};
    if (formData.material === 'Custom' && !formData.customMaterial) newErrors.material = 'Specify material grade';
    if (formData.structure === 'Custom' && !formData.customStructure) newErrors.structure = 'Specify structure type';
    if (formData.assetValue <= 0) newErrors.assetValue = 'Value must be positive';
    if (formData.downtimeCost < 0) newErrors.downtimeCost = 'Cost cannot be negative';
    if (formData.humidity < 0 || formData.humidity > 100) newErrors.humidity = 'Invalid humidity range';
    if (formData.pH < 0 || formData.pH > 14) newErrors.pH = 'pH must be between 0-14';
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSimulate = () => {
    if (validate()) {
      onSimulate(formData);
    } else {
      toast.error("Please correct the validation errors before proceeding.");
    }
  };

  return (
    <div className="relative w-full min-h-screen bg-bg flex items-center justify-center overflow-y-auto custom-scrollbar p-4 md:p-6">
      <GuidePanel />
      {/* Dynamic Background */}
      <div className="absolute inset-0 z-0 opacity-20 pointer-events-none">
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,var(--color-accent),transparent_50%)]" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_bottom_left,#4a90e2,transparent_50%)]" />
        <div className="absolute inset-0 backdrop-blur-3xl" />
      </div>

      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 1, ease: "easeOut" }}
        className="relative z-10 w-full max-w-5xl glass p-6 md:p-12 rounded-2xl shadow-2xl my-12"
      >
        <div className="flex flex-col gap-2 mb-8 md:mb-12">
          <div className="flex items-center gap-3">
            <Settings className="w-5 h-5 md:w-6 md:h-6 text-accent animate-spin-slow" />
            <h2 className="text-2xl md:text-4xl font-display font-bold uppercase tracking-tighter text-white">Setting the Scene</h2>
          </div>
          <p className="text-[8px] md:text-[10px] font-sans uppercase tracking-[0.3em] md:tracking-[0.5em] text-white/40">Environmental & Material Parameter Configuration</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 md:gap-12">
          {/* Material & Structure */}
          <div className="space-y-8">
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <label className="text-[10px] font-display font-bold uppercase tracking-widest text-white/40 flex items-center gap-2">
                  <Database className="w-3 h-3 text-accent" /> Material Intelligence
                </label>
                <button onClick={() => setActiveGuide('material')} className="text-white/20 hover:text-accent transition-colors">
                  <HelpCircle className="w-3 h-3" />
                </button>
              </div>
              <select
                name="material"
                value={formData.material}
                onChange={handleChange}
                className="w-full p-4 bg-white/5 border border-white/10 rounded-xl text-white font-display font-bold focus:outline-none focus:border-accent transition-all appearance-none cursor-pointer"
              >
                {materials.map((m) => (
                  <option key={m} value={m} className="bg-bg">{m}</option>
                ))}
              </select>
              <AnimatePresence>
                {formData.material === 'Custom' && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="space-y-2"
                  >
                    <input
                      type="text"
                      name="customMaterial"
                      placeholder="Specify Alloy Grade..."
                      value={formData.customMaterial}
                      onChange={handleChange}
                      className={`w-full p-4 bg-white/5 border ${errors.material ? 'border-red-500' : 'border-white/10'} rounded-xl text-white font-display font-bold focus:outline-none focus:border-accent transition-all mt-2`}
                    />
                    {errors.material && <p className="text-[8px] text-red-500 uppercase font-bold">{errors.material}</p>}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <label className="text-[10px] font-display font-bold uppercase tracking-widest text-white/40 flex items-center gap-2">
                  <Wind className="w-3 h-3 text-accent" /> Structural Context
                </label>
                <button onClick={() => setActiveGuide('structure')} className="text-white/20 hover:text-accent transition-colors">
                  <HelpCircle className="w-3 h-3" />
                </button>
              </div>
              <select
                name="structure"
                value={formData.structure}
                onChange={handleChange}
                className="w-full p-4 bg-white/5 border border-white/10 rounded-xl text-white font-display font-bold focus:outline-none focus:border-accent transition-all appearance-none cursor-pointer"
              >
                {structures.map((s) => (
                  <option key={s} value={s} className="bg-bg">{s}</option>
                ))}
              </select>
              <AnimatePresence>
                {formData.structure === 'Custom' && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="space-y-2"
                  >
                    <input
                      type="text"
                      name="customStructure"
                      placeholder="Specify Asset Type..."
                      value={formData.customStructure}
                      onChange={handleChange}
                      className={`w-full p-4 bg-white/5 border ${errors.structure ? 'border-red-500' : 'border-white/10'} rounded-xl text-white font-display font-bold focus:outline-none focus:border-accent transition-all mt-2`}
                    />
                    {errors.structure && <p className="text-[8px] text-red-500 uppercase font-bold">{errors.structure}</p>}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>

          {/* Financial & Environmental Parameters */}
          <div className="space-y-8">
            <div className="grid grid-cols-2 gap-6">
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <label className="text-[10px] font-display font-bold uppercase tracking-widest text-white/40 flex items-center gap-2">
                    <ShieldAlert className="w-3 h-3 text-accent" /> Compliance Standard
                  </label>
                  <button onClick={() => setActiveGuide('compliance')} className="text-white/20 hover:text-accent transition-colors">
                    <HelpCircle className="w-3 h-3" />
                  </button>
                </div>
                <select
                  name="compliance"
                  value={formData.compliance}
                  onChange={handleChange}
                  className="w-full p-4 bg-white/5 border border-white/10 rounded-xl text-white font-display font-bold focus:outline-none focus:border-accent transition-all appearance-none cursor-pointer"
                >
                  {complianceStandards.map((c) => (
                    <option key={c} value={c} className="bg-bg">{c}</option>
                  ))}
                </select>
              </div>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <label className="text-[10px] font-display font-bold uppercase tracking-widest text-white/40 flex items-center gap-2">
                    <Zap className="w-3 h-3 text-accent" /> Asset Criticality
                  </label>
                  <button onClick={() => setActiveGuide('criticality')} className="text-white/20 hover:text-accent transition-colors">
                    <HelpCircle className="w-3 h-3" />
                  </button>
                </div>
                <select
                  name="criticality"
                  value={formData.criticality}
                  onChange={handleChange}
                  className="w-full p-4 bg-white/5 border border-white/10 rounded-xl text-white font-display font-bold focus:outline-none focus:border-accent transition-all appearance-none cursor-pointer"
                >
                  {criticalityLevels.map((l) => (
                    <option key={l} value={l} className="bg-bg">{l}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-6">
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <label className="text-[10px] font-display font-bold uppercase tracking-widest text-white/40 flex items-center gap-2">
                    <DollarSign className="w-3 h-3 text-accent" /> Asset Value ($)
                  </label>
                  <button onClick={() => setActiveGuide('assetValue')} className="text-white/20 hover:text-accent transition-colors">
                    <HelpCircle className="w-3 h-3" />
                  </button>
                </div>
                <input
                  type="number"
                  name="assetValue"
                  value={formData.assetValue}
                  onChange={handleChange}
                  className={`w-full p-4 bg-white/5 border ${errors.assetValue ? 'border-red-500' : 'border-white/10'} rounded-xl text-white font-display font-bold focus:outline-none focus:border-accent transition-all`}
                />
                {errors.assetValue && <p className="text-[8px] text-red-500 uppercase font-bold">{errors.assetValue}</p>}
              </div>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <label className="text-[10px] font-display font-bold uppercase tracking-widest text-white/40 flex items-center gap-2">
                    <Clock className="w-3 h-3 text-accent" /> Daily Downtime ($)
                  </label>
                  <button onClick={() => setActiveGuide('downtimeCost')} className="text-white/20 hover:text-accent transition-colors">
                    <HelpCircle className="w-3 h-3" />
                  </button>
                </div>
                <input
                  type="number"
                  name="downtimeCost"
                  value={formData.downtimeCost}
                  onChange={handleChange}
                  className={`w-full p-4 bg-white/5 border ${errors.downtimeCost ? 'border-red-500' : 'border-white/10'} rounded-xl text-white font-display font-bold focus:outline-none focus:border-accent transition-all`}
                />
                {errors.downtimeCost && <p className="text-[8px] text-red-500 uppercase font-bold">{errors.downtimeCost}</p>}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-6">
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <label className="text-[10px] font-display font-bold uppercase tracking-widest text-white/40 flex items-center gap-2">
                    <Thermometer className="w-3 h-3 text-accent" /> Temp ( C)
                  </label>
                  <div className="flex items-center gap-2">
                    <label className="text-[8px] text-white/20 uppercase">Custom Range</label>
                    <input 
                      type="checkbox" 
                      name="isCustomTemp" 
                      checked={formData.isCustomTemp} 
                      onChange={handleChange}
                      className="accent-accent"
                    />
                    <button onClick={() => setActiveGuide('temperature')} className="text-white/20 hover:text-accent transition-colors">
                      <HelpCircle className="w-3 h-3" />
                    </button>
                  </div>
                </div>
                {formData.isCustomTemp ? (
                  <div className="flex gap-2">
                    <input
                      type="number"
                      placeholder="Min"
                      name="tempMin"
                      onChange={(e) => setFormData((p: any) => ({ ...p, tempRange: [parseFloat(e.target.value), p.tempRange[1]] }))}
                      className="w-1/2 p-4 bg-white/5 border border-white/10 rounded-xl text-white font-display font-bold focus:outline-none focus:border-accent transition-all"
                    />
                    <input
                      type="number"
                      placeholder="Max"
                      name="tempMax"
                      onChange={(e) => setFormData((p: any) => ({ ...p, tempRange: [p.tempRange[0], parseFloat(e.target.value)] }))}
                      className="w-1/2 p-4 bg-white/5 border border-white/10 rounded-xl text-white font-display font-bold focus:outline-none focus:border-accent transition-all"
                    />
                  </div>
                ) : (
                  <input
                    type="number"
                    name="temperature"
                    value={formData.temperature}
                    onChange={handleChange}
                    className="w-full p-4 bg-white/5 border border-white/10 rounded-xl text-white font-display font-bold focus:outline-none focus:border-accent transition-all"
                  />
                )}
              </div>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <label className="text-[10px] font-display font-bold uppercase tracking-widest text-white/40 flex items-center gap-2">
                    <Droplets className="w-3 h-3 text-accent" /> Humidity (%)
                  </label>
                  <button onClick={() => setActiveGuide('humidity')} className="text-white/20 hover:text-accent transition-colors">
                    <HelpCircle className="w-3 h-3" />
                  </button>
                </div>
                <input
                  type="number"
                  name="humidity"
                  value={formData.humidity}
                  onChange={handleChange}
                  className={`w-full p-4 bg-white/5 border ${errors.humidity ? 'border-red-500' : 'border-white/10'} rounded-xl text-white font-display font-bold focus:outline-none focus:border-accent transition-all`}
                />
                {errors.humidity && <p className="text-[8px] text-red-500 uppercase font-bold">{errors.humidity}</p>}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-6">
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <label className="text-[10px] font-display font-bold uppercase tracking-widest text-white/40 flex items-center gap-2">
                    <Zap className="w-3 h-3 text-accent" /> Salinity (g/L)
                  </label>
                  <button onClick={() => setActiveGuide('salinity')} className="text-white/20 hover:text-accent transition-colors">
                    <HelpCircle className="w-3 h-3" />
                  </button>
                </div>
                <input
                  type="number"
                  name="salinity"
                  value={formData.salinity}
                  onChange={handleChange}
                  className="w-full p-4 bg-white/5 border border-white/10 rounded-xl text-white font-display font-bold focus:outline-none focus:border-accent transition-all"
                />
              </div>
              <div className="space-y-3">
                <div className="flex justify-between items-center">
                  <label className="text-[10px] font-display font-bold uppercase tracking-widest text-white/40 flex items-center gap-2">
                    <Droplets className="w-3 h-3 text-accent" /> pH Level
                  </label>
                  <button onClick={() => setActiveGuide('pH')} className="text-white/20 hover:text-accent transition-colors">
                    <HelpCircle className="w-3 h-3" />
                  </button>
                </div>
                <input
                  type="number"
                  step="0.1"
                  name="pH"
                  value={formData.pH}
                  onChange={handleChange}
                  className={`w-full p-4 bg-white/5 border ${errors.pH ? 'border-red-500' : 'border-white/10'} rounded-xl text-white font-display font-bold focus:outline-none focus:border-accent transition-all`}
                />
                {errors.pH && <p className="text-[8px] text-red-500 uppercase font-bold">{errors.pH}</p>}
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-[10px] font-mono font-bold text-white/40 uppercase tracking-widest">UV Exposure (Index)</label>
                  <input
                    type="number"
                    value={formData.uvIndex}
                    onChange={(e) => setFormData({ ...formData, uvIndex: parseFloat(e.target.value) })}
                    className="w-full p-4 bg-white/5 border border-white/10 rounded-xl text-white font-display font-bold focus:outline-none focus:border-accent transition-all"
                    placeholder="0-11+"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-[10px] font-mono font-bold text-white/40 uppercase tracking-widest">MIC Activity</label>
                  <select
                    value={formData.micActivity}
                    onChange={(e) => setFormData({ ...formData, micActivity: e.target.value as any })}
                    className="w-full p-4 bg-white/5 border border-white/10 rounded-xl text-white font-display font-bold focus:outline-none focus:border-accent transition-all appearance-none"
                  >
                    <option value="Low">Low</option>
                    <option value="Medium">Medium</option>
                    <option value="High">High</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-[10px] font-mono font-bold text-white/40 uppercase tracking-widest">Soil Resistivity (Î©-cm)</label>
                  <input
                    type="number"
                    value={formData.soilResistivity}
                    onChange={(e) => setFormData({ ...formData, soilResistivity: parseFloat(e.target.value) })}
                    className="w-full p-4 bg-white/5 border border-white/10 rounded-xl text-white font-display font-bold focus:outline-none focus:border-accent transition-all"
                    placeholder="e.g., 5000"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-[10px] font-mono font-bold text-white/40 uppercase tracking-widest">Oxygen (mg/L)</label>
                  <input
                    type="number"
                    value={formData.oxygenLevel}
                    onChange={(e) => setFormData({ ...formData, oxygenLevel: parseFloat(e.target.value) })}
                    className="w-full p-4 bg-white/5 border border-white/10 rounded-xl text-white font-display font-bold focus:outline-none focus:border-accent transition-all"
                    placeholder="e.g., 8"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={handleSimulate}
          className="w-full mt-12 py-5 bg-accent text-bg font-display font-black uppercase tracking-[0.4em] rounded-xl hover:brightness-110 transition-all shadow-2xl shadow-accent/20"
        >
          Initiate Prediction Engine
        </motion.button>
      </motion.div>
    </div>
  );
};

export default Act2DataInput;

