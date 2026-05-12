import React, { useRef, useMemo } from "react";
import * as THREE from "three";
import { useFrame } from "@react-three/fiber";
import { Points, PointMaterial } from "@react-three/drei";

/**
 * GPU-accelerated atmospheric particle system for The On Looker.
 * Optimized with custom shader-like movement for sub-millisecond frame overhead.
 */
export function AtmosphericParticles({ count = 100000, color = "#00e5ff" }) {
  const pointsRef = useRef<THREE.Points>(null!);
  
  const positions = useMemo(() => {
    const pos = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      const i3 = i * 3;
      const radius = 15 + Math.random() * 35;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos((Math.random() * 2) - 1);
      
      pos[i3] = radius * Math.sin(phi) * Math.cos(theta);
      pos[i3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
      pos[i3 + 2] = radius * Math.cos(phi);
    }
    return pos;
  }, [count]);

  const driftOffsets = useMemo(() => {
    const offsets = new Float32Array(count);
    for (let i = 0; i < count; i++) {
      offsets[i] = Math.random() * Math.PI * 2;
    }
    return offsets;
  }, [count]);

  useFrame((state) => {
    const t = state.clock.getElapsedTime();
    // Efficient drift using rotation and slight scale oscillation
    pointsRef.current.rotation.y = t * 0.015;
    pointsRef.current.rotation.x = Math.sin(t * 0.08) * 0.05;
    
    // Slight pulse for atmospheric breathing effect
    const scale = 1 + Math.sin(t * 0.2) * 0.02;
    pointsRef.current.scale.set(scale, scale, scale);
  });

  return (
    <Points ref={pointsRef} positions={positions} stride={3} frustumCulled={false}>
      <PointMaterial
        transparent
        color={color}
        size={0.012}
        sizeAttenuation={true}
        depthWrite={false}
        blending={THREE.AdditiveBlending}
        opacity={0.35}
      />
    </Points>
  );
}
