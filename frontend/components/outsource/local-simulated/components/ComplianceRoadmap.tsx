import React from 'react';
import { motion } from 'framer-motion';
import { CheckCircle2, Circle, ArrowRight, ShieldCheck, FileText, Scale, Gavel } from 'lucide-react';

interface Props {
  onBack: () => void;
}

const ComplianceRoadmap = ({ onBack }: Props) => {
  const steps = [
    {
      title: "Environmental Characterization",
      standard: "ISO 12944-2",
      description: "Classify the environment (C1 to CX) based on corrosivity. Measure chloride deposition and sulfur dioxide levels.",
      status: "completed"
    },
    {
      title: "Surface Preparation",
      standard: "ISO 8501-1",
      description: "Specify blast cleaning grades (Sa 2.5 or Sa 3). Ensure surface profile (roughness) meets coating manufacturer requirements.",
      status: "current"
    },
    {
      title: "Coating System Selection",
      standard: "ISO 12944-5",
      description: "Select a protective paint system based on durability requirements (Low, Medium, High, Very High).",
      status: "pending"
    },
    {
      title: "Cathodic Protection Design",
      standard: "NACE SP0169",
      description: "Design sacrificial anode or impressed current systems for submerged or buried sections.",
      status: "pending"
    },
    {
      title: "Inspection & Quality Control",
      standard: "ISO 12944-7",
      description: "Define DFT (Dry Film Thickness) measurement protocols and holiday detection tests.",
      status: "pending"
    }
  ];

  return (
    <div className="h-full flex flex-col space-y-8 overflow-y-auto custom-scrollbar pr-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-4xl font-display font-black text-white uppercase tracking-tighter">Compliance Roadmap</h2>
          <p className="text-xs text-white/40 uppercase tracking-widest">Regulatory alignment & certification path</p>
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2 px-4 py-2 bg-accent/10 border border-accent/20 rounded-full">
            <Scale className="w-4 h-4 text-accent" />
            <span className="text-[10px] font-mono font-bold text-accent uppercase tracking-widest">ISO 12944 Certified</span>
          </div>
          <button
            onClick={onBack}
            className="px-6 py-3 bg-white/5 border border-white/10 text-white font-display font-bold uppercase tracking-widest text-[10px] hover:bg-white/10 transition-all"
          >
            Back
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
        <div className="lg:col-span-8 space-y-4">
          {steps.map((step, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.1 }}
              className={`glass p-8 border ${step.status === 'current' ? 'border-accent shadow-2xl shadow-accent/20' : 'border-white/5'} relative overflow-hidden`}
            >
              {step.status === 'current' && (
                <div className="absolute top-0 right-0 w-32 h-32 bg-accent/5 blur-3xl -mr-16 -mt-16" />
              )}
              
              <div className="flex items-start gap-6">
                <div className="flex flex-col items-center gap-2">
                  {step.status === 'completed' ? (
                    <CheckCircle2 className="w-6 h-6 text-accent" />
                  ) : step.status === 'current' ? (
                    <div className="w-6 h-6 rounded-full border-2 border-accent flex items-center justify-center">
                      <div className="w-2 h-2 bg-accent rounded-full animate-pulse" />
                    </div>
                  ) : (
                    <Circle className="w-6 h-6 text-white/10" />
                  )}
                  {i < steps.length - 1 && (
                    <div className={`w-0.5 h-16 ${step.status === 'completed' ? 'bg-accent' : 'bg-white/5'}`} />
                  )}
                </div>
                
                <div className="flex-1 space-y-2">
                  <div className="flex items-center justify-between">
                    <h3 className={`text-lg font-display font-black uppercase tracking-tight ${step.status === 'pending' ? 'text-white/20' : 'text-white'}`}>
                      {step.title}
                    </h3>
                    <span className="text-[10px] font-mono font-bold text-accent px-2 py-1 bg-accent/10 border border-accent/20">
                      {step.standard}
                    </span>
                  </div>
                  <p className={`text-xs leading-relaxed ${step.status === 'pending' ? 'text-white/10' : 'text-white/40'}`}>
                    {step.description}
                  </p>
                  {step.status === 'current' && (
                    <button className="mt-4 flex items-center gap-2 text-accent text-[10px] font-mono font-bold uppercase tracking-widest hover:gap-4 transition-all">
                      <span>Execute Protocol</span>
                      <ArrowRight className="w-3 h-3" />
                    </button>
                  )}
                </div>
              </div>
            </motion.div>
          ))}
        </div>

        <div className="lg:col-span-4 space-y-8">
          <div className="glass p-8 border border-white/10 space-y-6">
            <div className="flex items-center gap-3 text-white">
              <Gavel className="w-5 h-5 text-accent" />
              <h3 className="text-lg font-display font-black uppercase tracking-tight">Regulatory Summary</h3>
            </div>
            <div className="space-y-4">
              <div className="p-4 bg-white/5 border border-white/10 rounded-xl space-y-2">
                <p className="text-[8px] font-mono font-bold text-white/20 uppercase tracking-widest">Primary Standard</p>
                <p className="text-sm font-display font-bold text-white">ISO 12944:2018</p>
              </div>
              <div className="p-4 bg-white/5 border border-white/10 rounded-xl space-y-2">
                <p className="text-[8px] font-mono font-bold text-white/20 uppercase tracking-widest">Secondary Standard</p>
                <p className="text-sm font-display font-bold text-white">NACE SP0169-2013</p>
              </div>
              <div className="p-4 bg-white/5 border border-white/10 rounded-xl space-y-2">
                <p className="text-[8px] font-mono font-bold text-white/20 uppercase tracking-widest">Environmental Class</p>
                <p className="text-sm font-display font-bold text-accent">C5-M (Very High Marine)</p>
              </div>
            </div>
          </div>

          <div className="glass p-8 border border-white/10 space-y-6">
            <div className="flex items-center gap-3 text-white">
              <FileText className="w-5 h-5 text-accent" />
              <h3 className="text-lg font-display font-black uppercase tracking-tight">Required Documentation</h3>
            </div>
            <ul className="space-y-3">
              {['Material Test Reports (MTR)', 'Surface Prep Log', 'DFT Inspection Records', 'Holiday Test Certificate'].map((doc) => (
                <li key={doc} className="flex items-center gap-3 text-[10px] font-mono font-bold text-white/40 uppercase tracking-widest">
                  <div className="w-1.5 h-1.5 bg-accent rounded-full" />
                  {doc}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ComplianceRoadmap;
