import { useEffect, useRef } from "react";
import * as THREE from "three";

type VisualizationPanelProps = {
  intensity: number;
};

export function VisualizationPanel({ intensity }: VisualizationPanelProps) {
  const mountRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!mountRef.current) {
      return;
    }

    const width = mountRef.current.clientWidth;
    const height = 280;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color("#eef3f8");

    const camera = new THREE.PerspectiveCamera(55, width / height, 0.1, 100);
    camera.position.set(0, 0.8, 3.2);

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(width, height);
    mountRef.current.appendChild(renderer.domElement);

    const geometry = new THREE.CylinderGeometry(0.8, 0.8, 2.2, 48, 1, true);
    const corrosion = new THREE.Color().setHSL(Math.max(0, 0.45 - intensity * 0.0045), 0.75, 0.47);
    const material = new THREE.MeshStandardMaterial({ color: corrosion, metalness: 0.35, roughness: 0.65 });
    const cylinder = new THREE.Mesh(geometry, material);
    scene.add(cylinder);

    const lightA = new THREE.DirectionalLight("#ffffff", 1.6);
    lightA.position.set(2, 3, 2);
    scene.add(lightA);
    scene.add(new THREE.AmbientLight("#ffffff", 0.5));

    let animationFrame = 0;
    const animate = () => {
      cylinder.rotation.y += 0.01;
      cylinder.rotation.x = Math.sin(Date.now() * 0.001) * 0.1;
      renderer.render(scene, camera);
      animationFrame = requestAnimationFrame(animate);
    };
    animate();

    return () => {
      cancelAnimationFrame(animationFrame);
      geometry.dispose();
      material.dispose();
      renderer.dispose();
      if (mountRef.current?.contains(renderer.domElement)) {
        mountRef.current.removeChild(renderer.domElement);
      }
    };
  }, [intensity]);

  return (
    <section className="panel p-4">
      <h3 className="mb-3 text-lg font-semibold">3D Corrosion Intensity</h3>
      <div ref={mountRef} className="h-[280px] w-full overflow-hidden rounded-lg border border-slate-200" />
    </section>
  );
}
