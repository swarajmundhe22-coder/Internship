import React, { useState, useEffect, useRef, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Activity, Cpu, Database, ShieldAlert, Terminal, Zap, Layers, Crosshair, Box } from 'lucide-react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Sphere, Float, Stars, MeshDistortMaterial, Points, PointMaterial } from '@react-three/drei';
import * as THREE from 'three';

const MolecularBackground = () => {
  const pointsRef = useRef<THREE.Points>(null!);
  const groupRef = useRef<THREE.Group>(null!);
  
  const particles = useMemo(() => {
    const temp = new Float32Array(2000 * 3);
    for (let i = 0; i < 2000; i++) {
      temp[i * 3] = (Math.random() - 0.5) * 10;
      temp[i * 3 + 1] = (Math.random() - 0.5) * 10;
      temp[i * 3 + 2] = (Math.random() - 0.5) * 10;
    }
    return temp;
  }, []);

  useFrame((state) => {
    const t = state.clock.getElapsedTime();
    const { x, y } = state.mouse;
    
    pointsRef.current.rotation.y = t * 0.05;
    pointsRef.current.rotation.x = t * 0.02;
    
    // Parallax
    groupRef.current.rotation.x = THREE.MathUtils.lerp(groupRef.current.rotation.x, y * 0.1, 0.05);
    groupRef.current.rotation.y = THREE.MathUtils.lerp(groupRef.current.rotation.y, x * 0.1, 0.05);
  });

  return (
    <group ref={groupRef}>
      <Points ref={pointsRef} positions={particles} stride={3}>
        <PointMaterial
          transparent
          color="#c9ff57"
          size={0.02}
          sizeAttenuation={true}
          depthWrite={false}
          blending={THREE.AdditiveBlending}
        />
      </Points>
      <Float speed={2} rotationIntensity={1} floatIntensity={1}>
        <Sphere args={[1, 64, 64]}>
          <MeshDistortMaterial
            color="#c9ff57"
            speed={2}
            distort={0.4}
            radius={1}
            transparent
            opacity={0.1}
            wireframe
          />
        </Sphere>
      </Float>
    </group>
  );
};

const FUIHeader = () => (
  <div className="absolute top-6 left-6 right-6 md:top-12 md:left-12 md:right-12 flex flex-col md:flex-row justify-between items-start md:items-center gap-4 pointer-events-none z-20">
    <div className="flex items-center gap-4">
      <div className="w-8 h-8 md:w-10 md:h-10 border border-accent/40 flex items-center justify-center bg-accent/5">
        <Cpu className="w-4 h-4 md:w-5 md:h-5 text-accent animate-pulse" />
      </div>
      <div>
        <h2 className="text-lg md:text-xl font-display font-black uppercase tracking-tighter text-white">Neural Modeling</h2>
        <p className="text-[7px] md:text-[8px] font-mono text-accent uppercase tracking-[0.2em] md:tracking-[0.3em]">Core: Quantum-V // Thread: 0x842A</p>
      </div>
    </div>
    <div className="text-left md:text-right space-y-1">
      <div className="text-[8px] md:text-[9px] font-mono text-white/40 uppercase tracking-widest">Compute: 12.4 TFLOPS</div>
      <div className="text-[8px] md:text-[9px] font-mono text-white/40 uppercase tracking-widest">Memory: 128GB HBM3</div>
    </div>
  </div>
);

interface Props {
  data: any;
  result: any;
  onComplete: () => void;
}

const Act3PredictionEngine = ({ data, result, onComplete }: Props) => {
  const [progress, setProgress] = useState(0);
  const [logs, setLogs] = useState<string[]>([]);

  const simulationSteps = [
    "Initializing Environmental Modeling Engine...",
    "Calculating Electrochemical Potential (Nernst Equation)...",
    "Analyzing Faraday's Law for Material Dissolution...",
    "Identifying Corrosion Type: Pitting & Galvanic...",
    "Modeling Structural Integrity Degradation...",
    "Finalizing Risk Score & Lifespan Prediction...",
  ];

  useEffect(() => {
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          return 100;
        }
        return prev + 1;
      });
    }, 50);

    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const logInterval = setInterval(() => {
      if (logs.length < simulationSteps.length) {
        setLogs((prev) => [...prev, simulationSteps[prev.length]]);
      } else if (progress >= 100 && result) {
        clearInterval(logInterval);
        setTimeout(() => {
          onComplete();
        }, 1000);
      }
    }, 800);

    return () => clearInterval(logInterval);
  }, [logs, progress, onComplete, result]);

  return (
    <div className="relative w-full h-screen bg-bg flex flex-col items-center justify-center overflow-hidden">
      <FUIHeader />
      
      {/* 3D Background */}
      <div className="absolute inset-0 z-0">
        <Canvas camera={{ position: [0, 0, 5] }}>
          <ambientLight intensity={0.5} />
          <pointLight position={[10, 10, 10]} />
          <MolecularBackground />
          <Stars radius={100} depth={50} count={5000} factor={4} saturation={0} fade speed={1} />
        </Canvas>
      </div>

      <div className="relative z-10 w-full max-w-5xl px-4 md:px-12 space-y-8 md:space-y-12">
        <div className="glass p-6 md:p-12 rounded-none border border-white/5 shadow-2xl space-y-8 md:space-y-12 backdrop-blur-3xl">
          <div className="space-y-6">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4">
              <div className="space-y-1">
                <span className="text-[8px] md:text-[10px] font-display font-bold uppercase tracking-widest text-accent flex items-center gap-2">
                  <Activity className="w-3 h-3 animate-pulse" /> Simulation Progress
                </span>
                <div className="text-4xl md:text-6xl font-display font-black text-white tracking-tighter">
                  {progress.toString().padStart(3, '0')}<span className="text-xl md:text-2xl opacity-40">%</span>
                </div>
              </div>
              <div className="text-left md:text-right space-y-1">
                <div className="text-[8px] md:text-[9px] font-mono text-white/40 uppercase tracking-widest">ETA: 00:00:04</div>
                <div className="text-[8px] md:text-[9px] font-mono text-accent uppercase tracking-widest font-bold">Status: Processing</div>
              </div>
            </div>
            <div className="h-1 w-full bg-white/5 rounded-none overflow-hidden relative">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${progress}%` }}
                className="h-full bg-accent shadow-[0_0_30px_rgba(201,255,87,0.8)] relative z-10"
              />
              <div className="absolute inset-0 bg-[linear-gradient(90deg,transparent_0%,var(--color-accent)_50%,transparent_100%)] opacity-10 animate-shimmer" />
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 md:gap-8">
            <div className="lg:col-span-1 space-y-4 md:space-y-6">
              <h3 className="text-[9px] md:text-[10px] font-display font-bold uppercase tracking-widest text-white/40 flex items-center gap-2">
                <Layers className="w-3 h-3" /> Parameters
              </h3>
              <div className="grid grid-cols-2 lg:grid-cols-1 gap-2">
                {Object.entries(data).slice(0, 6).map(([key, value]) => (
                  <div key={key} className="p-2 md:p-3 bg-white/5 border-l border-white/10 flex justify-between items-center">
                    <span className="text-[7px] md:text-[8px] uppercase tracking-widest text-white/30 truncate mr-2">{key}</span>
                    <span className="text-[9px] md:text-[10px] font-mono font-bold text-white shrink-0">{String(value)}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="lg:col-span-2 space-y-4 md:space-y-6">
              <h3 className="text-[9px] md:text-[10px] font-display font-bold uppercase tracking-widest text-white/40 flex items-center gap-2">
                <Terminal className="w-3 h-3" /> Kernel Output
              </h3>
              <div className="h-40 md:h-48 overflow-y-auto font-mono text-[9px] md:text-[10px] space-y-2 md:space-y-3 p-4 md:p-6 bg-black/60 rounded-none border border-white/5 custom-scrollbar backdrop-blur-md">
                <AnimatePresence mode="popLayout">
                  {logs.map((log, i) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      className="flex items-start gap-3 text-accent/80 border-b border-white/5 pb-2"
                    >
                      <span className="opacity-40 font-mono shrink-0 text-[8px] md:text-[10px]">[{new Date().toLocaleTimeString([], { hour12: false, minute: '2-digit', second: '2-digit' })}]</span>
                      <span className="leading-relaxed">{log}</span>
                      <div className="ml-auto">
                        <div className="w-1 h-1 bg-accent rounded-full animate-pulse" />
                      </div>
                    </motion.div>
                  ))}
                </AnimatePresence>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Scanning Grid Overlay */}
      <div className="absolute inset-0 pointer-events-none z-10">
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#ffffff03_1px,transparent_1px),linear-gradient(to_bottom,#ffffff03_1px,transparent_1px)] bg-[size:20px_20px]" />
        <motion.div 
          animate={{ x: ['-100%', '100%'] }}
          transition={{ duration: 5, repeat: Infinity, ease: "linear" }}
          className="absolute top-0 bottom-0 w-[1px] bg-accent/20 shadow-[0_0_15px_rgba(201,255,87,0.3)]"
        />
      </div>
    </div>
  );
};

export default Act3PredictionEngine;

