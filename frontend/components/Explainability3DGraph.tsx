import React, { useRef, useMemo } from "react";
import * as THREE from "three";
import { useFrame } from "@react-three/fiber";
import { Line, Sphere, Text, Float } from "@react-three/drei";

type ExplainabilityGraphProps = {
  data?: Array<{ name: string; impact: number; category: string }>;
};

/**
 * Interactive 3D force-directed graph for SHAP/LIME explainability.
 * Rendered within the cinematic scene to provide data transparency.
 */
export function Explainability3DGraph({ data }: ExplainabilityGraphProps) {
  const groupRef = useRef<THREE.Group>(null!);

  const nodes = useMemo(() => {
    const defaultData = [
      { name: "UV Index", impact: 0.85, category: "Environment" },
      { name: "Salinity", impact: 0.92, category: "Environment" },
      { name: "Material", impact: 0.78, category: "Asset" },
      { name: "Age", impact: 0.65, category: "Temporal" },
      { name: "Load", impact: 0.45, category: "Operational" },
    ];
    const displayData = data || defaultData;

    return displayData.map((d, i) => {
      const angle = (i / displayData.length) * Math.PI * 2;
      const radius = 3 + d.impact * 2;
      return {
        ...d,
        position: [
          Math.cos(angle) * radius,
          Math.sin(angle) * radius,
          (Math.random() - 0.5) * 2,
        ] as [number, number, number],
        color: d.category === "Environment" ? "#00e5ff" : d.category === "Asset" ? "#c9ff57" : "#ff9f43",
      };
    });
  }, [data]);

  useFrame((state) => {
    const t = state.clock.getElapsedTime();
    groupRef.current.rotation.y = t * 0.1;
    groupRef.current.rotation.z = Math.sin(t * 0.2) * 0.05;
  });

  return (
    <group ref={groupRef}>
      {/* Central Node (Target Prediction) */}
      <Sphere args={[0.5, 32, 32]}>
        <meshStandardMaterial color="#ffffff" emissive="#ffffff" emissiveIntensity={0.5} />
      </Sphere>
      <Text
        position={[0, 0.8, 0]}
        fontSize={0.2}
        color="white"
        font="https://fonts.gstatic.com/s/orbitron/v25/y97pyXjdzB_Z9_93m0.woff"
      >
        PREDICTION
      </Text>

      {/* Feature Nodes & Connections */}
      {nodes.map((node, i) => (
        <group key={i} position={node.position}>
          <Float speed={2} rotationIntensity={0.5} floatIntensity={0.5}>
            <Sphere args={[0.2 * node.impact, 16, 16]}>
              <meshStandardMaterial color={node.color} emissive={node.color} emissiveIntensity={0.8} />
            </Sphere>
            <Text
              position={[0, 0.4, 0]}
              fontSize={0.15}
              color="white"
              maxWidth={1}
              textAlign="center"
              font="https://fonts.gstatic.com/s/spacegrotesk/v13/V8mQoQDjQSkFtoMM3T6r8E7mF71Q-g.woff"
            >
              {node.name}\n{(node.impact * 100).toFixed(0)}%
            </Text>
          </Float>

          {/* Connection to Center */}
          <Line
            points={[[0, 0, 0], [-node.position[0], -node.position[1], -node.position[2]]]}
            color={node.color}
            lineWidth={1}
            transparent
            opacity={0.3}
          />
        </group>
      ))}

      {/* Ambient particles for the graph */}
      <AmbientPoints count={500} />
    </group>
  );
}

function AmbientPoints({ count = 500 }) {
  const positions = useMemo(() => {
    const pos = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      pos[i * 3] = (Math.random() - 0.5) * 10;
      pos[i * 3 + 1] = (Math.random() - 0.5) * 10;
      pos[i * 3 + 2] = (Math.random() - 0.5) * 10;
    }
    return pos;
  }, [count]);

  return (
    <points>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          count={positions.length / 3}
          array={positions}
          itemSize={3}
        />
      </bufferGeometry>
      <pointsMaterial size={0.05} color="#ffffff" transparent opacity={0.1} />
    </points>
  );
}
