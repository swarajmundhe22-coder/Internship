import React from 'react';
import { motion } from 'framer-motion';
import { BookOpen, ChevronRight, Target, Shield, DollarSign, Thermometer, Droplets, Zap, Info, ArrowLeft, FileText, Activity } from 'lucide-react';

interface Props {
  onBack: () => void;
}

const EngineeringManual = ({ onBack }: Props) => {
  const sections = [
    {
      id: 'compliance',
      title: 'Compliance Standards',
      icon: Shield,
      content: `
        ### Regulatory Framework Selection
        Accurate simulation requires alignment with industry-specific standards. 
        
        *   **ISO 12944:** The global benchmark for corrosion protection of steel structures by protective paint systems. Use this for atmospheric assets (bridges, offshore topsides).
        *   **NACE SP0169:** Standard for control of external corrosion on underground or submerged metallic piping systems. Focuses on Cathodic Protection (CP) criteria.
        *   **ASTM G1:** Standard practice for preparing, cleaning, and evaluating corrosion test specimens.
        
        **How to verify:** Check the asset's original design specification or the regional regulatory body (e.g., DOT for bridges, BSEE for offshore).
      `
    },
    {
      id: 'criticality',
      title: 'Asset Criticality (Risk Matrix)',
      icon: Target,
      content: `
        ### Calculating Criticality
        Criticality is defined as **Probability of Failure (PoF) Ã— Consequence of Failure (CoF)**.
        
        *   **Low:** Non-structural, redundant systems. Failure has minimal impact.
        *   **Medium:** Secondary structural elements. Failure requires repair but no immediate safety risk.
        *   **High:** Primary structural elements. Failure leads to significant operational stoppage.
        *   **Mission Critical:** Life-safety systems, nuclear containment, or high-pressure toxic gas lines. Zero-tolerance.
        
        **Calculation Tip:** Use the 5x5 Risk Matrix standard (ISO 31000) to assign numerical values to PoF and CoF.
      `
    },
    {
      id: 'financials',
      title: 'Financial Parameters',
      icon: DollarSign,
      content: `
        ### Asset Value & Downtime
        
        **Asset Value (Replacement Cost):**
        Do not use the book value. Use the **Current Replacement Value (CRV)**.
        *Formula:* CRV = (Material Cost + Fabrication + Logistics + Installation + Engineering + Permitting) at current market rates.
        
        **Daily Downtime Cost:**
        *Formula:* (Lost Revenue/Day) + (Fixed Operational Costs) + (Contractual Penalties) + (Emergency Mobilization Fees).
        
        **Accuracy Check:** Consult your Asset Management or Finance department for the most recent CRV and Business Interruption (BI) insurance values.
      `
    },
    {
      id: 'environmental',
      title: 'Environmental Data Collection',
      icon: Activity,
      content: `
        ### Precision Measurement Techniques
        
        **Temperature ( C):**
        Use the **Mean Annual Temperature** for long-term predictions. For high-accuracy, use the **Peak Surface Temperature**, as corrosion rates accelerate exponentially at higher temperatures (Arrhenius Equation).
        
        **Relative Humidity (%):**
        Calculate the **Time-of-Wetness (TOW)**. Corrosion only occurs when RH > 80% and temperature > 0 C.
        
        **Salinity (Chlorides):**
        Measured in g/L or mg/m2/day (deposition rate). 
        *Technique:* Use the "Wet Candle" method (ISO 9225) for atmospheric chlorides or conductometric titration for submerged environments.
        
        **pH Level:**
        Crucial for soil and fluid-handling assets. 
        *Tip:* pH < 4 (Acidic) causes rapid hydrogen evolution; pH > 10 (Alkaline) can lead to passivation in steel but embrittlement in other alloys.
      `
    }
  ];

  return (
    <div className="relative w-full h-screen bg-bg overflow-y-auto custom-scrollbar">
      {/* Background Elements */}
      <div className="fixed inset-0 z-0 opacity-5 pointer-events-none">
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#ffffff05_1px,transparent_1px),linear-gradient(to_bottom,#ffffff05_1px,transparent_1px)] bg-[size:100px_100px]" />
      </div>

      <div className="relative z-10 max-w-5xl mx-auto p-12 lg:p-24">
        {/* Header */}
        <div className="flex flex-col gap-8 mb-24">
          <button 
            onClick={onBack}
            className="flex items-center gap-2 text-white/40 hover:text-accent transition-colors group w-fit"
          >
            <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
            <span className="text-[10px] font-display font-bold uppercase tracking-widest">Return to Platform</span>
          </button>

          <div className="space-y-4">
            <div className="flex items-center gap-4">
              <div className="p-4 bg-accent/10 border border-accent/20">
                <BookOpen className="w-8 h-8 text-accent" />
              </div>
              <h1 className="text-6xl font-display font-black uppercase tracking-tighter text-white">Engineering Manual</h1>
            </div>
            <p className="text-lg text-white/40 font-serif italic max-w-2xl leading-relaxed">
              A comprehensive guide to high-fidelity data collection and parameter calculation for the corrosion digital twin.
            </p>
          </div>
        </div>

        {/* Content Sections */}
        <div className="space-y-32">
          {sections.map((section, i) => (
            <motion.section
              key={section.id}
              initial={{ opacity: 0, y: 40 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.8, delay: i * 0.1 }}
              className="grid grid-cols-1 lg:grid-cols-12 gap-12"
            >
              <div className="lg:col-span-4">
                <div className="sticky top-12 space-y-4">
                  <div className="flex items-center gap-3 text-accent">
                    <section.icon className="w-5 h-5" />
                    <span className="text-[10px] font-display font-bold uppercase tracking-widest">Section 0{i + 1}</span>
                  </div>
                  <h2 className="text-3xl font-display font-bold text-white uppercase tracking-tight leading-none">
                    {section.title}
                  </h2>
                  <div className="w-12 h-1 bg-accent/20" />
                </div>
              </div>

              <div className="lg:col-span-8">
                <div className="glass p-12 border border-white/5 space-y-8">
                  <div className="prose prose-invert prose-accent max-w-none">
                    {section.content.split('\n').map((line, idx) => {
                      if (line.trim().startsWith('###')) {
                        return <h3 key={idx} className="text-xl font-display font-bold text-white uppercase tracking-widest mb-6">{line.replace('###', '').trim()}</h3>;
                      }
                      if (line.trim().startsWith('*')) {
                        return <li key={idx} className="text-white/60 mb-2 list-none flex gap-3"><ChevronRight className="w-4 h-4 text-accent shrink-0 mt-1" /> {line.replace('*', '').trim()}</li>;
                      }
                      if (line.trim().startsWith('**')) {
                        const parts = line.split('**');
                        return <p key={idx} className="text-white/80 leading-relaxed mb-4"><span className="text-accent font-bold">{parts[1]}</span>{parts[2]}</p>;
                      }
                      return line.trim() ? <p key={idx} className="text-white/60 leading-relaxed mb-4">{line.trim()}</p> : null;
                    })}
                  </div>
                  
                  <div className="pt-8 border-t border-white/5 flex items-center gap-4">
                    <div className="p-2 bg-white/5 rounded-full">
                      <Info className="w-4 h-4 text-accent" />
                    </div>
                    <p className="text-[10px] font-mono text-white/20 uppercase tracking-widest">
                      Verified against ISO 9223 & NACE International Standards
                    </p>
                  </div>
                </div>
              </div>
            </motion.section>
          ))}
        </div>

        {/* Footer CTA */}
        <div className="mt-48 p-16 glass border border-accent/20 text-center space-y-8">
          <h3 className="text-4xl font-display font-black text-white uppercase tracking-tighter">Ready to Simulate?</h3>
          <p className="text-white/40 max-w-xl mx-auto">
            Apply these measurement techniques to ensure your digital twin provides the most accurate lifecycle predictions possible.
          </p>
          <button 
            onClick={onBack}
            className="px-12 py-6 bg-accent text-bg font-display font-black uppercase tracking-[0.4em] hover:brightness-110 transition-all shadow-2xl shadow-accent/20"
          >
            Launch Prediction Engine
          </button>
        </div>
      </div>
    </div>
  );
};

export default EngineeringManual;

