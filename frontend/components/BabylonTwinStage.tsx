import { useEffect, useRef } from "react";

import { TwinHotspot } from "../types/domain";

type BabylonTwinStageProps = {
  hotspots: TwinHotspot[];
};

const severityHex: Record<string, string> = {
  green: "#22c55e",
  yellow: "#facc15",
  red: "#ef4444"
};

export function BabylonTwinStage({ hotspots }: BabylonTwinStageProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    if (!canvasRef.current) {
      return;
    }

    let disposed = false;
    let cleanup: (() => void) | null = null;

    async function boot() {
      const [{ Engine, Scene, ArcRotateCamera, Vector3, HemisphericLight, MeshBuilder, Color3, StandardMaterial }, { GlowLayer }] =
        await Promise.all([import("@babylonjs/core"), import("@babylonjs/core/Layers/glowLayer")]);

      if (!canvasRef.current || disposed) {
        return;
      }

      const engine = new Engine(canvasRef.current, true, { preserveDrawingBuffer: true, stencil: true });
      const scene = new Scene(engine);

      const camera = new ArcRotateCamera("camera", Math.PI / 2.8, Math.PI / 2.7, 10, Vector3.Zero(), scene);
      camera.attachControl(canvasRef.current, true);
      camera.lowerRadiusLimit = 5;
      camera.upperRadiusLimit = 16;

      const light = new HemisphericLight("light", new Vector3(0, 1, 0), scene);
      light.intensity = 0.95;

      const glow = new GlowLayer("glow", scene, { blurKernelSize: 32 });
      glow.intensity = 0.85;

      const core = MeshBuilder.CreateBox("core-asset", { size: 2.4 }, scene);
      const coreMaterial = new StandardMaterial("core-material", scene);
      coreMaterial.diffuseColor = Color3.FromHexString("#15202D");
      coreMaterial.emissiveColor = Color3.FromHexString("#1A3342");
      core.material = coreMaterial;

      const ring = MeshBuilder.CreateTorus("status-ring", { diameter: 4.2, thickness: 0.08 }, scene);
      ring.rotation.x = Math.PI / 2;
      const ringMaterial = new StandardMaterial("ring-material", scene);
      ringMaterial.emissiveColor = Color3.FromHexString("#00E5FF");
      ringMaterial.diffuseColor = Color3.FromHexString("#00E5FF");
      ring.material = ringMaterial;

      hotspots.forEach((spot, index) => {
        const marker = MeshBuilder.CreateSphere(`hotspot-${index}`, { diameter: 0.3 }, scene);
        marker.position = new Vector3(spot.x, spot.y, spot.z);
        const markerMaterial = new StandardMaterial(`hotspot-material-${index}`, scene);
        markerMaterial.emissiveColor = Color3.FromHexString(severityHex[spot.severity] ?? "#93C5FD");
        markerMaterial.diffuseColor = Color3.FromHexString("#1F2937");
        marker.material = markerMaterial;
      });

      engine.runRenderLoop(() => {
        ring.rotation.z += 0.003;
        core.rotation.y += 0.004;
        scene.render();
      });

      const onResize = () => engine.resize();
      window.addEventListener("resize", onResize);
      cleanup = () => {
        window.removeEventListener("resize", onResize);
        engine.stopRenderLoop();
        scene.dispose();
        engine.dispose();
      };
    }

    void boot();

    return () => {
      disposed = true;
      if (cleanup) {
        cleanup();
      }
    };
  }, [hotspots]);

  return <canvas ref={canvasRef} width={1200} height={520} className="w-full rounded-lg border border-lagoon/30" />;
}
