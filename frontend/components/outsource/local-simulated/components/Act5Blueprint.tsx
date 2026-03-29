import React, { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ShieldCheck, Zap, Droplets, Hammer, FileText, Download, Share2, RefreshCw, TrendingUp, PieChart, Globe, ClipboardCheck, Box, CheckCircle2, AlertCircle, Database, FileDown } from 'lucide-react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Float, PerspectiveCamera, MeshDistortMaterial, OrbitControls, Stage } from '@react-three/drei';
import * as THREE from 'three';
import { toast } from 'sonner';
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';

const InterventionModel = () => {
  const meshRef = useRef<THREE.Mesh>(null!);
  const groupRef = useRef<THREE.Group>(null!);
  
  useFrame((state) => {
    const t = state.clock.getElapsedTime();
    const { x, y } = state.mouse;
    
    meshRef.current.rotation.y = t * 0.2;
    
    // Parallax
    groupRef.current.rotation.x = THREE.MathUtils.lerp(groupRef.current.rotation.x, y * 0.1, 0.05);
    groupRef.current.rotation.y = THREE.MathUtils.lerp(groupRef.current.rotation.y, x * 0.1, 0.05);
  });

  return (
    <group ref={groupRef}>
      <mesh ref={meshRef}>
        <cylinderGeometry args={[1, 1, 4, 64]} />
        <meshStandardMaterial 
          color="#c9ff57" 
          metalness={0.8} 
          roughness={0.2} 
          emissive="#c9ff57"
          emissiveIntensity={0.2}
        />
      </mesh>
      {/* Protective Layer */}
      <mesh scale={[1.1, 1.05, 1.1]}>
        <cylinderGeometry args={[1, 1, 4, 64]} />
        <meshStandardMaterial 
          color="#ffffff" 
          transparent 
          opacity={0.1} 
          wireframe 
        />
      </mesh>
    </group>
  );
};

interface Props {
  result: any;
  onReset: () => void;
  onSaveScenario?: (name: string) => void;
}

const Act5Blueprint = ({ result, onReset, onSaveScenario }: Props) => {
  const reportRef = useRef<HTMLDivElement>(null);
  const [scenarioName, setScenarioName] = useState('');
  const [showSaveModal, setShowSaveModal] = useState(false);

  const handleSave = () => {
    if (!scenarioName) {
      toast.error("Please enter a scenario name");
      return;
    }
    onSaveScenario?.(scenarioName);
    setShowSaveModal(false);
    setScenarioName('');
  };

  const exportPDF = async () => {
    if (!reportRef.current) return;
    
    const toastId = toast.loading("Generating Engineering Report...");
    
    try {
      const canvas = await html2canvas(reportRef.current, {
        scale: 2,
        useCORS: true,
        backgroundColor: '#050505'
      });
      
      const imgData = canvas.toDataURL('image/png');
      const pdf = new jsPDF('l', 'mm', 'a4');
      const imgProps = pdf.getImageProperties(imgData);
      const pdfWidth = pdf.internal.pageSize.getWidth();
      const pdfHeight = (imgProps.height * pdfWidth) / imgProps.width;
      
      pdf.addImage(imgData, 'PNG', 0, 0, pdfWidth, pdfHeight);
      pdf.save(`Onlooker_Report_${result?.id || Date.now()}.pdf`);
      
      toast.success("Report downloaded successfully", { id: toastId });
    } catch (error) {
      console.error(error);
      toast.error("Failed to generate report", { id: toastId });
    }
  };
  const interventions = result?.interventions || [
    {
      title: 'Protective Coatings',
      description: 'Apply high-performance epoxy-polyamide coating system with zinc-rich primer.',
      icon: ShieldCheck,
      status: 'Recommended',
    },
    {
      title: 'Cathodic Protection',
      description: 'Install sacrificial anode system (Al-Zn-In) to suppress electrochemical potential.',
      icon: Zap,
      status: 'Critical',
    },
    {
      title: 'Corrosion Inhibitors',
      description: 'Inject organic film-forming inhibitors into the fluid stream to reduce surface reactivity.',
      icon: Droplets,
      status: 'Optional',
    },
    {
      title: 'Maintenance Schedule',
      description: 'Bi-annual ultrasonic thickness measurements and visual inspection at critical nodes.',
      icon: Hammer,
      status: 'Mandatory',
    },
  ];

  // Map icon types if they are strings from AI, but here we just use the index to keep it simple or use defaults
  const getIcon = (index: number) => {
    const icons = [ShieldCheck, Zap, Droplets, Hammer];
    return icons[index % icons.length];
  };

  const capex = result?.capexRequirement || 1240000;
  const roi = result?.projectedROI || 15.4;
  const extension = result?.lifecycleExtension || 12.5;
  const esg = result?.esgCompliance || 92;

  return (
    <div className="relative w-full h-screen bg-bg flex flex-col items-center justify-center overflow-hidden">
      {/* Background Grid */}
      <div className="absolute inset-0 z-0 opacity-10 pointer-events-none">
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#ffffff05_1px,transparent_1px),linear-gradient(to_bottom,#ffffff05_1px,transparent_1px)] bg-[size:40px_40px]" />
      </div>

      <div ref={reportRef} className="relative z-10 w-full max-w-7xl h-full flex flex-col p-6 md:p-12 gap-8 bg-bg overflow-y-auto custom-scrollbar">
        {/* Header */}
        <div className="flex flex-col lg:flex-row justify-between items-start lg:items-end gap-8">
          <div className="space-y-2">
            <div className="flex items-center gap-3">
              <ShieldCheck className="w-6 h-6 md:w-8 md:h-8 text-accent animate-pulse" />
              <h2 className="text-3xl md:text-5xl font-display font-black uppercase tracking-tighter text-white">The Blueprint</h2>
            </div>
            <p className="text-[8px] md:text-[10px] font-sans uppercase tracking-[0.3em] md:tracking-[0.5em] text-white/40">Engineering & Capital Preservation Strategy</p>
          </div>
          <div className="flex flex-wrap gap-3 md:gap-4 pointer-events-auto w-full lg:w-auto">
            <div className="flex gap-2">
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={exportPDF}
                className="p-3 md:p-4 glass border border-white/10 text-accent hover:border-accent/40 transition-all"
                title="Download PDF Report"
              >
                <FileDown className="w-4 h-4" />
              </motion.button>
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => {
                  navigator.clipboard.writeText(window.location.href);
                  toast.success("Simulation link copied to clipboard");
                }}
                className="p-3 md:p-4 glass border border-white/10 text-white hover:border-accent/40 transition-all"
              >
                <Share2 className="w-4 h-4" />
              </motion.button>
            </div>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setShowSaveModal(true)}
              className="flex-1 lg:flex-none px-4 md:px-8 py-3 md:py-4 border border-accent/20 text-accent font-display font-black uppercase tracking-widest text-[10px] md:text-xs shadow-2xl shadow-accent/20 hover:bg-accent hover:text-bg transition-all"
            >
              Save Scenario
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={onReset}
              className="flex-1 lg:flex-none px-4 md:px-8 py-3 md:py-4 bg-accent text-bg font-display font-black uppercase tracking-widest text-[10px] md:text-xs shadow-2xl shadow-accent/20"
            >
              New Simulation
            </motion.button>
          </div>
        </div>

        <AnimatePresence>
          {showSaveModal && (
            <div className="fixed inset-0 z-[100] flex items-center justify-center p-6">
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                onClick={() => setShowSaveModal(false)}
                className="absolute inset-0 bg-black/80 backdrop-blur-sm"
              />
              <motion.div
                initial={{ opacity: 0, scale: 0.9, y: 20 }}
                animate={{ opacity: 1, scale: 1, y: 0 }}
                exit={{ opacity: 0, scale: 0.9, y: 20 }}
                className="relative w-full max-w-md glass p-12 border border-white/10 space-y-8"
              >
                <div className="space-y-2">
                  <h3 className="text-3xl font-display font-black text-white uppercase tracking-tighter">Save Scenario</h3>
                  <p className="text-xs text-white/40 uppercase tracking-widest">Archive this simulation for comparison</p>
                </div>
                <div className="space-y-4">
                  <input
                    type="text"
                    placeholder="Scenario Name (e.g., High Salinity Test)..."
                    value={scenarioName}
                    onChange={(e) => setScenarioName(e.target.value)}
                    className="w-full p-4 bg-white/5 border border-white/10 rounded-xl text-white font-display font-bold focus:outline-none focus:border-accent transition-all"
                  />
                  <button
                    onClick={handleSave}
                    className="w-full py-4 bg-accent text-bg font-display font-black uppercase tracking-widest rounded-xl"
                  >
                    Confirm Save
                  </button>
                </div>
              </motion.div>
            </div>
          )}
        </AnimatePresence>

        <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-8 min-h-0">
          {/* Left: Interventions List */}
          <div className="lg:col-span-4 flex flex-col gap-4 overflow-y-auto custom-scrollbar pr-0 lg:pr-2 max-h-[400px] lg:max-h-none">
            {interventions.map((item: any, i: number) => {
              const Icon = item.icon || getIcon(i);
              return (
                <motion.div
                  key={i}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: i * 0.1 }}
                  className="glass p-6 rounded-none border border-white/5 hover:border-accent/40 transition-all group cursor-pointer"
                >
                  <div className="flex justify-between items-start mb-4">
                    <div className="p-3 bg-white/5 rounded-none group-hover:bg-accent/10 transition-colors">
                      <Icon className="w-5 h-5 text-accent" />
                    </div>
                    <span className={`text-[8px] font-display font-bold uppercase tracking-widest px-2 py-1 border ${
                      item.status === 'Critical' ? 'border-red-500 text-red-500' : 
                      item.status === 'Mandatory' ? 'border-accent text-accent' : 'border-white/20 text-white/40'
                    }`}>
                      {item.status}
                    </span>
                  </div>
                  <h3 className="text-sm font-display font-bold text-white uppercase tracking-widest mb-2">{item.title}</h3>
                  <p className="text-[10px] text-white/40 leading-relaxed">{item.description}</p>
                </motion.div>
              );
            })}
          </div>

          {/* Middle: 3D Visualization */}
          <div className="lg:col-span-5 glass p-0 rounded-none border border-white/5 relative overflow-hidden bg-black/20 min-h-[300px] md:min-h-[400px] lg:min-h-0">
            <div className="absolute top-4 left-4 md:top-8 md:left-8 z-20 flex items-center gap-2">
              <Box className="w-4 h-4 text-accent" />
              <span className="text-[8px] md:text-[10px] font-display font-bold uppercase tracking-widest text-white/40">Structural Digital Twin</span>
            </div>
            
            <Canvas shadows className="cursor-grab active:cursor-grabbing">
              <PerspectiveCamera makeDefault position={[0, 0, 10]} fov={35} />
              <ambientLight intensity={0.5} />
              <pointLight position={[10, 10, 10]} intensity={1} />
              <pointLight position={[-10, -10, -10]} intensity={0.5} color="#4a90e2" />
              
              <Stage environment="city" intensity={0.5}>
                <InterventionModel />
              </Stage>
              
              <OrbitControls enableZoom={false} autoRotate autoRotateSpeed={0.5} />
            </Canvas>

            <div className="absolute bottom-4 left-4 right-4 md:bottom-8 md:left-8 md:right-8 z-20 flex justify-between items-center">
              <div className="flex gap-2">
                <div className="px-2 md:px-3 py-1 bg-accent/10 border border-accent/20 text-accent text-[6px] md:text-[8px] font-mono font-bold">LOD: 400</div>
                <div className="px-2 md:px-3 py-1 bg-white/5 border border-white/10 text-white/40 text-[6px] md:text-[8px] font-mono font-bold">MESH: OPTIMIZED</div>
              </div>
              <div className="text-[7px] md:text-[9px] font-mono text-white/20 uppercase tracking-widest">Interactive 3D Preview</div>
            </div>
          </div>

          {/* Right: Investment & ESG */}
          <div className="lg:col-span-3 flex flex-col gap-6">
            <div className="glass p-8 rounded-none border border-white/5 space-y-8">
              <div className="flex items-center gap-3 text-accent">
                <TrendingUp className="w-5 h-5" />
                <span className="text-[10px] font-display font-bold uppercase tracking-widest">Investment Analysis</span>
              </div>
              
              <div className="space-y-6">
                <div className="space-y-1">
                  <p className="text-[9px] font-display font-bold uppercase tracking-widest text-white/40">CAPEX Requirement</p>
                  <p className="text-4xl font-display font-black text-white">${(capex / 1000000).toFixed(2)}M</p>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <p className="text-[8px] font-display font-bold uppercase tracking-widest text-white/40">NPV (10Y)</p>
                    <p className="text-lg font-display font-black text-white">$14.2M</p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-[8px] font-display font-bold uppercase tracking-widest text-white/40">IRR</p>
                    <p className="text-lg font-display font-black text-accent">24.8%</p>
                  </div>
                </div>
                <div className="space-y-1">
                  <p className="text-[9px] font-display font-bold uppercase tracking-widest text-white/40">Projected ROI</p>
                  <p className="text-4xl font-display font-black text-accent">{roi}x</p>
                </div>
              </div>

              <div className="pt-8 border-t border-white/5 space-y-6">
                <div className="flex items-center justify-between">
                  <span className="text-[9px] font-display font-bold uppercase tracking-widest text-white/40">ESG Compliance</span>
                  <span className="text-xs font-display font-bold text-accent">{esg}%</span>
                </div>
                <div className="space-y-4">
                  <div className="space-y-2">
                    <div className="flex justify-between text-[8px] font-mono font-bold uppercase tracking-widest text-white/20">
                      <span>Carbon Reduction</span>
                      <span>-12.4t</span>
                    </div>
                    <div className="w-full h-1 bg-white/5">
                      <motion.div 
                        initial={{ width: 0 }}
                        animate={{ width: `${esg}%` }}
                        className="h-full bg-accent"
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="flex justify-between text-[8px] font-mono font-bold uppercase tracking-widest text-white/20">
                      <span>Sustainability Score</span>
                      <span>88/100</span>
                    </div>
                    <div className="w-full h-1 bg-white/5">
                      <motion.div 
                        initial={{ width: 0 }}
                        animate={{ width: '88%' }}
                        className="h-full bg-green-500"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div className="flex-1 glass p-8 rounded-none border border-white/5 flex flex-col justify-center gap-4">
              <div className="flex items-center gap-2 text-white/40">
                <CheckCircle2 className="w-4 h-4" />
                <span className="text-[9px] font-display font-bold uppercase tracking-widest">Certification Status</span>
              </div>
              <p className="text-xl font-display font-bold text-white uppercase tracking-tighter">Verified by AI-Link</p>
              <p className="text-[10px] text-white/40 leading-relaxed">
                This strategy has been cross-referenced with 4.2M global infrastructure data points and is certified for immediate implementation.
              </p>
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="flex justify-between items-center pt-4 border-t border-white/5">
          <div className="flex gap-8">
            <div className="flex items-center gap-2">
              <FileTextIcon className="w-4 h-4 text-white/20" />
              <span className="text-[9px] font-display font-bold uppercase tracking-widest text-white/40">PDF Report</span>
            </div>
            <div className="flex items-center gap-2">
              <Database className="w-4 h-4 text-white/20" />
              <span className="text-[9px] font-display font-bold uppercase tracking-widest text-white/40">CSV Data</span>
            </div>
            <div className="flex items-center gap-2">
              <Globe className="w-4 h-4 text-white/20" />
              <span className="text-[9px] font-display font-bold uppercase tracking-widest text-white/40">API Endpoint</span>
            </div>
          </div>
          <div className="text-[9px] font-mono text-white/20 uppercase tracking-widest">Document ID: ONL-2026-842A-X</div>
        </div>
      </div>
    </div>
  );
};

const FileTextIcon = ({ className }: { className?: string }) => (
  <svg className={className} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><line x1="10" y1="9" x2="8" y2="9"/></svg>
);

export default Act5Blueprint;

