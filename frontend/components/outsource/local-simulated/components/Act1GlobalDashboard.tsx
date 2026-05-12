import React, { useRef, useMemo, useEffect, useState } from 'react';
import { Canvas, useFrame, useLoader } from '@react-three/fiber';
import { OrbitControls, Stars, PerspectiveCamera, Float, Html } from '@react-three/drei';
import * as THREE from 'three';
import { motion } from 'framer-motion';
import { Terminal, Activity, AlertTriangle, Globe as GlobeIcon, Shield, Zap, Cpu, Layers, Crosshair } from 'lucide-react';
import type { RealtimeHudMetrics } from '../useRealtimeHudMetrics';

const AtmosphereShader = {
  uniforms: {
    lightDirection: { value: new THREE.Vector3(1, 0.5, 1).normalize() },
    time: { value: 0 }
  },
  vertexShader: `
    varying vec3 vNormal;
    varying vec3 vPosition;
    void main() {
      vNormal = normalize(normalMatrix * normal);
      vPosition = (modelViewMatrix * vec4(position, 1.0)).xyz;
      gl_Position = projectionMatrix * vec4(vPosition, 1.0);
    }
  `,
  fragmentShader: `
    varying vec3 vNormal;
    varying vec3 vPosition;
    uniform vec3 lightDirection;
    void main() {
      // Basic atmospheric rim lighting
      float intensity = pow(0.65 - dot(normalize(vNormal), vec3(0.0, 0.0, 1.0)), 3.0);
      vec3 col = mix(vec3(0.2, 0.5, 1.0), vec3(0.78, 1.0, 0.34), 0.15);
      
      // Calculate light intensity
      float li = dot(normalize(vNormal), normalize(lightDirection));
      
      // Fade out on the dark side of the terminator
      float isDay = smoothstep(-0.2, 0.2, li);
      col = mix(col, vec3(0.9, 1.0, 0.8), li * 0.2);
      
      // Multiply by intensity for the rim effect and isDay for the terminator
      gl_FragColor = vec4(col, 1.0) * intensity * isDay * 1.5;
    }
  `
};

type FUIOverlayProps = {
  seismicData: number[];
  systemStats: { cpuCores: number; memTotal: number; memUsed: number; memPercent: number; cpuUsage: number; activeConns: number };
  threatData: { count: number; level: string };
  metrics: RealtimeHudMetrics;
};

const FUIOverlay = ({ metrics, seismicData, systemStats, threatData }: FUIOverlayProps) => {
  return (
    <div className="absolute inset-0 pointer-events-none z-20 p-6 pt-24 md:p-12 md:pt-32 flex flex-col justify-between overflow-y-auto custom-scrollbar">
      {/* Top Bar */}
      <div className="flex flex-col md:flex-row justify-between items-start gap-6">
        <div className="space-y-4">
          <div className="flex items-center gap-4">
            <div className="w-10 h-10 md:w-12 md:h-12 border border-accent/40 flex items-center justify-center bg-accent/5 backdrop-blur-md">
              <Terminal className="w-5 h-5 md:w-6 md:h-6 text-accent animate-pulse" />
            </div>
            <div>
              <h2 className="text-xl md:text-2xl font-display font-black uppercase tracking-tighter text-white">Global Surveillance</h2>
              <p className="text-[7px] md:text-[9px] font-mono text-accent uppercase tracking-[0.2em] md:tracking-[0.3em]">System Status: Operational // AI-Link: Active</p>
            </div>
          </div>
          <div className="flex gap-2">
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="w-6 md:w-8 h-1 bg-accent/20 overflow-hidden">
                <motion.div 
                  animate={{ x: [-32, 32] }}
                  transition={{ duration: 2, repeat: Infinity, delay: i * 0.2 }}
                  className="w-full h-full bg-accent"
                />
              </div>
            ))}
          </div>
        </div>

        <div className="text-left md:text-right space-y-1 md:space-y-2">
          <div className="text-[8px] md:text-[10px] font-mono text-white/40 uppercase tracking-widest">Network Latency: {metrics.latencyLabel}</div>
          <div className="text-[8px] md:text-[10px] font-mono text-white/40 uppercase tracking-widest">Encryption: {metrics.encryptionLabel}</div>
          <div className="text-[8px] md:text-[10px] font-mono text-accent uppercase tracking-widest font-bold">Live Feed: {metrics.liveFeedUtcLabel}</div>
        </div>
      </div>

      {/* Side Panels */}
      <div className="flex flex-col md:flex-row justify-between items-end gap-6 mt-8 md:mt-0">
        <div className="space-y-4 md:space-y-6 w-full md:w-64 pointer-events-auto">
          <div className="glass p-4 md:p-6 rounded-none border-l-2 border-accent/60 space-y-4">
            <div className="flex items-center gap-2 text-accent">
              <Activity className="w-4 h-4" />
              <span className="text-[8px] md:text-[10px] font-display font-bold uppercase tracking-widest">Seismic Activity</span>
            </div>
            <div className="h-10 md:h-12 flex items-end gap-1">
              {seismicData.slice(0, 20).map((val, i) => (
                  <motion.div
                    key={i}
                    animate={{ height: [val * 0.8, val, val * 0.9] }}
                    transition={{ duration: 1.5, repeat: Infinity, delay: i * 0.05 }}
                    className="flex-1 bg-accent/40"
                    style={{ minHeight: '4px', height: `${val * 10}px` }}
                  />
                ))}
            </div>
          </div>
          
          <div className="glass p-4 md:p-6 rounded-none border-l-2 border-white/20 space-y-1 md:space-y-2">
            <div className="text-[8px] md:text-[9px] text-white/40 uppercase tracking-widest">Active Nodes (Threads)</div>
            <div className="text-xl md:text-2xl font-display font-bold text-white">{systemStats.cpuCores}</div>
          </div>
        </div>

        <div className="space-y-4 md:space-y-6 w-full md:w-64 text-left md:text-right pointer-events-auto">
          <div className="glass p-4 md:p-6 rounded-none border-r-0 md:border-r-2 border-l-2 md:border-l-0 border-accent/60 space-y-4">
            <div className="flex items-center justify-start md:justify-end gap-2 text-accent">
              <span className="text-[8px] md:text-[10px] font-display font-bold uppercase tracking-widest">Threat Detection</span>
              <AlertTriangle className="w-4 h-4" />
            </div>
            <div className="space-y-2">
              <div className="flex justify-between md:justify-end items-center gap-3">
                <span className="text-[8px] text-white/40 uppercase tracking-widest">Critical Nodes</span>
                <span className="text-sm md:text-base font-mono font-bold text-red-500">{threatData.count}</span>
              </div>
              <div className="flex justify-between md:justify-end items-center gap-3">
                <span className="text-[8px] text-white/40 uppercase tracking-widest">Risk Level</span>
                <span className={`text-sm md:text-base font-mono font-bold ${threatData.level === "CRITICAL" ? "text-red-500" : threatData.level === "HIGH" ? "text-orange-500" : "text-accent"}`}>{threatData.level}</span>
              </div>
            </div>
          </div>

          <div className="glass p-4 md:p-6 rounded-none border-r-0 md:border-r-2 border-l-2 md:border-l-0 border-white/20 space-y-1 md:space-y-2">
            <div className="text-[8px] md:text-[9px] text-white/40 uppercase tracking-widest">Compute Load & RAM</div>
            <div className="text-xl md:text-2xl font-display font-bold text-white">CPU {systemStats.cpuUsage}%</div>
   <div className="text-xs font-mono text-white/60 mt-1">RAM {systemStats.memUsed}G / {systemStats.memTotal}G ({systemStats.memPercent}%)</div>
          </div>
        </div>
      </div>
    </div>
  );
};

const Globe = () => {
  const globeRef = useRef<THREE.Mesh>(null!);
  const cloudsRef = useRef<THREE.Mesh>(null!);
  const heatmapRef = useRef<THREE.Mesh>(null!);
  const groupRef = useRef<THREE.Group>(null!);
  
  const [dayMap, normalMap, specMap, cloudsMap] = useLoader(THREE.TextureLoader, [
    'https://raw.githubusercontent.com/mrdoob/three.js/master/examples/textures/planets/earth_atmos_2048.jpg',
    'https://raw.githubusercontent.com/mrdoob/three.js/master/examples/textures/planets/earth_normal_2048.jpg',
    'https://raw.githubusercontent.com/mrdoob/three.js/master/examples/textures/planets/earth_specular_2048.jpg',
    'https://raw.githubusercontent.com/mrdoob/three.js/master/examples/textures/planets/earth_clouds_1024.png'
  ]);

  const heatmapTexture = useMemo(() => {
    const canvas = document.createElement('canvas');
    canvas.width = 1024;
    canvas.height = 512;
    const ctx = canvas.getContext('2d')!;
    ctx.fillStyle = '#0a0a0a';
    ctx.fillRect(0, 0, 1024, 512);

    const hotspots = [
      { x: 200, y: 180, r: 80, color: 'rgba(255,80,50,' },
      { x: 750, y: 200, r: 60, color: 'rgba(255,160,30,' },
      { x: 500, y: 150, r: 50, color: 'rgba(201,255,87,' },
      { x: 350, y: 280, r: 70, color: 'rgba(255,80,50,' },
    ];

    hotspots.forEach(h => {
      const grad = ctx.createRadialGradient(h.x, h.y, 0, h.x, h.y, h.r);
      grad.addColorStop(0, h.color + '0.6)');
      grad.addColorStop(0.4, h.color + '0.25)');
      grad.addColorStop(1, h.color + '0)');
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, 1024, 512);
    });

    return new THREE.CanvasTexture(canvas);
  }, []);

  useFrame((state) => {
    const t = state.clock.getElapsedTime();
    const { x, y } = state.mouse;
    
    // Smooth rotation
    globeRef.current.rotation.y += 0.001;
    cloudsRef.current.rotation.y += 0.0015;
    heatmapRef.current.rotation.y = globeRef.current.rotation.y;
    
    // Mouse parallax
    groupRef.current.rotation.x = THREE.MathUtils.lerp(groupRef.current.rotation.x, y * 0.2, 0.05);
    groupRef.current.rotation.y = THREE.MathUtils.lerp(groupRef.current.rotation.y, x * 0.2, 0.05);
    
    const mat = heatmapRef.current.material as THREE.MeshStandardMaterial;
    mat.opacity = 0.5 + Math.sin(t * 0.8) * 0.15;
  });

  return (
    <group ref={groupRef}>
      {/* Base Earth */}
      <mesh ref={globeRef} castShadow receiveShadow>
        <sphereGeometry args={[2.5, 128, 128]} />
        <meshPhongMaterial
          map={dayMap}
          normalMap={normalMap}
          specularMap={specMap}
          normalScale={new THREE.Vector2(0.8, 0.8)}
          shininess={100}
          specular={new THREE.Color(0x333333)}
        />
      </mesh>

      {/* Heatmap Overlay */}
      <mesh ref={heatmapRef}>
        <sphereGeometry args={[2.51, 128, 128]} />
        <meshBasicMaterial
          map={heatmapTexture}
          transparent
          opacity={0.65}
          blending={THREE.AdditiveBlending}
          depthWrite={false}
        />
      </mesh>

      {/* Clouds */}
      <mesh ref={cloudsRef}>
        <sphereGeometry args={[2.52, 64, 64]} />
        <meshPhongMaterial
          map={cloudsMap}
          transparent
          opacity={0.3}
          depthWrite={false}
          color={0xffffff}
        />
      </mesh>

      {/* Atmosphere */}
      <mesh scale={[1.02, 1.02, 1.02]}>
        <sphereGeometry args={[2.5, 64, 64]} />
        <shaderMaterial
          {...AtmosphereShader}
          blending={THREE.AdditiveBlending}
          side={THREE.BackSide}
          transparent
        />
      </mesh>
    </group>
  );
};

type Act1GlobalDashboardProps = {
  metrics: RealtimeHudMetrics;
};

const Act1GlobalDashboard = ({ metrics }: Act1GlobalDashboardProps) => {
  const [corrosionCost, setCorrosionCost] = React.useState(0);
  const [seismicData, setSeismicData] = React.useState([...Array(20)].map(() => 10));
  const [systemStats, setSystemStats] = React.useState({ cpuCores: 0, memTotal: 0, memUsed: 0, memPercent: 0, cpuUsage: 0, activeConns: 0 });
  const [threatData, setThreatData] = React.useState({ count: 12, level: 'LOADING...' });

  React.useEffect(() => {
    const startOfYear = new Date(new Date().getFullYear(), 0, 1).getTime();
    const updateCost = () => {
      const now = Date.now();
      const secondsSinceYearStart = (now - startOfYear) / 1000;
      setCorrosionCost(secondsSinceYearStart * 79274.48);
    };
    const timer = setInterval(updateCost, 1000);
    updateCost();

    const fetchSeismic = async () => {
      try {
        const res = await fetch('https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson');
        const data = await res.json();
        let heights = [];
        if (data && data.features) {
          heights = data.features.slice(0, 20).map((f) => Math.max(2, (f.properties?.mag || 1) * 5));
        }
        if (heights.length < 20) {
          while (heights.length < 20) heights.push(2);
        }
        setSeismicData(heights);
      } catch (err) {}
    };

    const fetchSystem = async () => {
      const localCores = typeof navigator !== 'undefined' ? navigator.hardwareConcurrency || 4 : 4;
      try {
        const res = await fetch('http://localhost:8000/ops/metrics/live?api_key=SIMULATED_KEY_123');
        if (res.ok) {
          const s = await res.json();
          setSystemStats({
            cpuCores: s.cpu?.cores || localCores,
            memTotal: s.memory?.total_gb || 0,
            memUsed: s.memory?.used_gb || 0,
            memPercent: s.memory?.usage_percent || 0,
            cpuUsage: s.cpu?.usage_percent || 0,
            activeConns: s.network?.active_connections || 0
          });
        }
      } catch (err) {
        setSystemStats(prev => ({ ...prev, cpuCores: localCores }));
      }
    };

    const fetchThreats = async () => {
      try {
        const res = await fetch('https://urlhaus-api.abuse.ch/v1/urls/recent/', { method: 'GET'});
        if (res.ok) {
          const data = await res.json();
          const count = data.urls ? data.urls.length : 12;
          setThreatData({ count, level: count > 50 ? 'CRITICAL' : 'HIGH' });
        } else {
          setThreatData({ count: 12, level: 'HIGH' });
        }
      } catch (err) {
        setThreatData({ count: 12, level: 'HIGH' });
      }
    };

    fetchSeismic();
    fetchSystem();
    fetchThreats();

    const intS = setInterval(fetchSeismic, 5 * 60 * 1000);
    const intH = setInterval(fetchSystem, 3000);
    const intT = setInterval(fetchThreats, 10 * 60 * 1000);

    return () => {
      clearInterval(timer);
      clearInterval(intS);
      clearInterval(intH);
      clearInterval(intT);
    };
  }, []);

  const stats = [
    { label: 'Est. Global Loss (YTD)', value: `$${(corrosionCost / 1e9).toFixed(2)}B`, icon: GlobeIcon, color: 'text-accent' },
    { label: 'Annual GDP Impact', value: '3.4%', icon: Shield, color: 'text-blue-400' },
    { label: 'Network Connections', value: systemStats.activeConns.toLocaleString(), icon: Cpu, color: 'text-accent' },
    { label: 'Threat Traces', value: threatData.count.toLocaleString(), icon: Activity, color: 'text-accent' },
  ];

  

  return (
    <div className="relative w-full h-screen bg-bg overflow-hidden">
      <FUIOverlay metrics={metrics} seismicData={seismicData} systemStats={systemStats} threatData={threatData} />
      
      {/* Background Grid */}
      <div className="absolute inset-0 z-0 opacity-20 pointer-events-none">
        <div className="absolute inset-0 bg-[linear-gradient(to_right,#ffffff05_1px,transparent_1px),linear-gradient(to_bottom,#ffffff05_1px,transparent_1px)] bg-[size:40px_40px]" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,var(--color-accent),transparent_70%)] opacity-10" />
      </div>

      <div className="absolute inset-0 z-10">
        <Canvas shadows>
          <PerspectiveCamera makeDefault position={[0, 0, 8]} fov={45} />
          <ambientLight intensity={0.3} />
          <directionalLight position={[5, 3, 5]} intensity={1.5} castShadow />
          <directionalLight position={[-3, -1, -3]} intensity={0.4} color="#4a90e2" />
          
          <Stars radius={100} depth={50} count={12000} factor={4} saturation={0} fade speed={1} />
          
          <React.Suspense fallback={null}>
            <Globe />
          </React.Suspense>
          
          <OrbitControls enableZoom={false} autoRotate autoRotateSpeed={0.5} />
        </Canvas>
      </div>

      {/* Bottom Stats - Bento Style */}
      <div className="absolute bottom-12 left-1/2 -translate-x-1/2 z-30 w-full max-w-6xl px-12">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 pointer-events-auto">
          {stats.map((stat, i) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1, duration: 0.8 }}
              className="glass p-6 rounded-none border border-white/5 hover:border-accent/40 transition-all group cursor-pointer"
            >
              <div className="flex items-center gap-4">
                <div className={`p-3 bg-white/5 rounded-none group-hover:bg-accent/10 transition-colors`}>
                  <stat.icon className={`w-5 h-5 ${stat.color}`} />
                </div>
                <div>
                  <p className="text-[9px] font-display font-bold uppercase tracking-widest text-white/40">{stat.label}</p>
                  <p className="text-xl font-display font-black text-white">{stat.value}</p>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </div>

      {/* Scanning Line */}
      <motion.div 
        animate={{ top: ['0%', '100%', '0%'] }}
        transition={{ duration: 10, repeat: Infinity, ease: "linear" }}
        className="absolute left-0 w-full h-[1px] bg-accent/20 z-20 pointer-events-none shadow-[0_0_15px_rgba(0,255,0,0.3)]"
      />

      {/* Cinematic Overlays */}
      <div className="absolute inset-0 pointer-events-none bg-[radial-gradient(circle_at_center,transparent_0%,black_100%)] opacity-70" />
      <div className="absolute inset-0 pointer-events-none bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 mix-blend-overlay" />
    </div>
  );
};

export default Act1GlobalDashboard;

