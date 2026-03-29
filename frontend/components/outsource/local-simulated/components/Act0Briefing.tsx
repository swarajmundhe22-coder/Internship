import React, { useRef, useMemo } from 'react';
import { motion } from 'framer-motion';
import { Shield, AlertTriangle, Activity, ChevronRight } from 'lucide-react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Float, Sphere, MeshDistortMaterial, Stars } from '@react-three/drei';
import * as THREE from 'three';

const BackgroundScene = () => {
  const meshRef = useRef<THREE.Mesh>(null!);
  
  useFrame((state) => {
    const t = state.clock.getElapsedTime();
    meshRef.current.rotation.y = t * 0.1;
    meshRef.current.position.y = Math.sin(t * 0.5) * 0.2;
  });

  return (
    <group>
      <Float speed={2} rotationIntensity={0.5} floatIntensity={0.5}>
        <mesh ref={meshRef}>
          <sphereGeometry args={[2, 64, 64]} />
          <MeshDistortMaterial
            color="#c9ff57"
            speed={1.5}
            distort={0.3}
            radius={1}
            transparent
            opacity={0.05}
            wireframe
          />
        </mesh>
      </Float>
      <Stars radius={100} depth={50} count={2000} factor={4} saturation={0} fade speed={1} />
    </group>
  );
};

interface Props {
  onStart: () => void;
}

const Act0Briefing = ({ onStart }: Props) => {
  return (
    <div className="relative w-full h-screen bg-bg flex flex-col items-center justify-center overflow-hidden">
      {/* 3D Background */}
      <div className="absolute inset-0 z-0 pointer-events-none">
        <Canvas camera={{ position: [0, 0, 5] }}>
          <ambientLight intensity={0.5} />
          <pointLight position={[10, 10, 10]} />
          <BackgroundScene />
        </Canvas>
      </div>

      <div className="relative z-10 w-full max-w-6xl px-6 md:px-12 flex flex-col items-center text-center space-y-12 md:space-y-16">
        <div className="space-y-4 md:space-y-6">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1.5, ease: [0.22, 1, 0.36, 1] }}
            className="flex flex-col items-center gap-3 md:gap-4"
          >
            <div className="w-10 h-10 md:w-12 md:h-12 border border-accent/30 flex items-center justify-center bg-accent/5 rounded-full">
              <Shield className="w-4 h-4 md:w-5 md:h-5 text-accent animate-pulse" />
            </div>
            <p className="text-[8px] md:text-[10px] font-display font-bold uppercase tracking-[0.4em] md:tracking-[0.8em] text-accent/60">The Onlooker Project</p>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 40 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3, duration: 1.5, ease: [0.22, 1, 0.36, 1] }}
            className="text-6xl md:text-8xl lg:text-[10rem] font-display font-black uppercase tracking-tighter text-white leading-[0.85] mix-blend-difference"
          >
            Silent <br /> <span className="text-accent">Decay</span>
          </motion.h1>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6, duration: 1.5, ease: [0.22, 1, 0.36, 1] }}
          className="max-w-2xl space-y-6 md:space-y-8"
        >
          <p className="text-base md:text-lg font-sans text-white/60 leading-relaxed tracking-wide px-4 md:px-0">
            Corrosion is a global crisis. According to the <span className="text-white font-bold">AMPP (formerly NACE)</span>, the global cost of corrosion is estimated at <span className="text-white font-bold">$2.5 trillion USD</span> annually - equivalent to 3.4% of the global GDP.
          </p>
          
          <div className="flex flex-wrap justify-center gap-6 md:gap-12 pt-4 md:pt-8">
            <div className="space-y-1 text-center">
              <p className="text-[8px] md:text-[9px] font-display font-bold uppercase tracking-widest text-white/30">Global GDP Impact</p>
              <p className="text-lg md:text-xl font-display font-bold text-white">3.4%</p>
            </div>
            <div className="hidden md:block w-px h-12 bg-white/10" />
            <div className="space-y-1 text-center">
              <p className="text-[8px] md:text-[9px] font-display font-bold uppercase tracking-widest text-white/30">Annual Cost</p>
              <p className="text-lg md:text-xl font-display font-bold text-white">$2.5T</p>
            </div>
            <div className="hidden md:block w-px h-12 bg-white/10" />
            <div className="space-y-1 text-center">
              <p className="text-[8px] md:text-[9px] font-display font-bold uppercase tracking-widest text-white/30">Source</p>
              <p className="text-lg md:text-xl font-display font-bold text-white uppercase">AMPP/NACE</p>
            </div>
          </div>
        </motion.div>

        <motion.button
          initial={{ opacity: 0, scale: 0.9 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 1.2, duration: 1.5, ease: [0.22, 1, 0.36, 1] }}
          whileHover={{ scale: 1.05 }}
          whileTap={{ scale: 0.95 }}
          onClick={onStart}
          className="group relative px-8 md:px-16 py-4 md:py-6 bg-accent text-bg font-display font-black uppercase tracking-[0.3em] md:tracking-[0.5em] text-[10px] md:text-xs transition-all hover:brightness-110 shadow-[0_0_50px_rgba(201,255,87,0.2)]"
        >
          <span className="relative z-10 flex items-center gap-3 md:gap-4">
            Initialize Platform <ChevronRight className="w-4 h-4 group-hover:translate-x-2 transition-transform" />
          </span>
        </motion.button>
      </div>

      {/* Cinematic Overlays */}
      <div className="absolute top-0 left-0 w-full h-32 bg-gradient-to-b from-bg to-transparent z-20 pointer-events-none" />
      <div className="absolute bottom-0 left-0 w-full h-32 bg-gradient-to-t from-bg to-transparent z-20 pointer-events-none" />
    </div>
  );
};

export default Act0Briefing;

