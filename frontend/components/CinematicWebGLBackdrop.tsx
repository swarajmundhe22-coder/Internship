import { useEffect, useRef } from "react";
import * as THREE from "three";
import { EffectComposer } from "three/examples/jsm/postprocessing/EffectComposer.js";
import { RenderPass } from "three/examples/jsm/postprocessing/RenderPass.js";
import { UnrealBloomPass } from "three/examples/jsm/postprocessing/UnrealBloomPass.js";
import { FilmPass } from "three/examples/jsm/postprocessing/FilmPass.js";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/dist/ScrollTrigger";

import { useCinematicQuality } from "../contexts/CinematicQualityContext";
import { onLookersBrandDirection } from "../utils/brandDirection";
import { CinematicRouteTone } from "../utils/cinematicRoute";

const toneCurves: Record<CinematicRouteTone, { startZ: number; endZ: number; y: number; bloom: number; hue: string }> = {
  opening: { startZ: 11.2, endZ: 8.15, y: 0.42, bloom: 1.3, hue: "#43e6ff" },
  mission: { startZ: 10.8, endZ: 7.8, y: 0.2, bloom: 0.95, hue: "#5fd3ff" },
  battle: { startZ: 10.6, endZ: 7.35, y: 0.08, bloom: 1.45, hue: "#ff9f43" },
  briefing: { startZ: 10.9, endZ: 7.95, y: 0.22, bloom: 1.05, hue: "#a584ff" },
  world: { startZ: 11, endZ: 7.55, y: 0.18, bloom: 1.25, hue: "#44ffe1" },
  finale: { startZ: 10.7, endZ: 7.5, y: 0.12, bloom: 1.38, hue: "#ffd071" }
};

type CinematicWebGLBackdropProps = {
  tone: CinematicRouteTone;
};

export function CinematicWebGLBackdrop({ tone }: CinematicWebGLBackdropProps) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const { config } = useCinematicQuality();

  useEffect(() => {
    if (!canvasRef.current || typeof window === "undefined") {
      return;
    }

    const hasMatchMedia = typeof window.matchMedia === "function";
    if (hasMatchMedia) {
      gsap.registerPlugin(ScrollTrigger);
    }

    const toneCurve = toneCurves[tone];
    const sceneDirection = onLookersBrandDirection.sceneByTone[tone];
    const intensity = onLookersBrandDirection.intensity;
    const cameraFactor = Math.max(0.7, intensity.cameraMovementIntensity / 6);
    const glowFactor = Math.max(0.7, intensity.glowIntensity / 6);

    const canvas = canvasRef.current;
    let renderer: THREE.WebGLRenderer;

    try {
      renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
    } catch {
      return;
    }
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, config.pixelRatioMax));
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.08;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(50, 1, 0.1, 120);
    camera.position.set(0, toneCurve.y, toneCurve.endZ);

    const heroRig = new THREE.Group();
    scene.add(heroRig);

    const ambient = new THREE.AmbientLight("#6b86c7", 0.65);
    scene.add(ambient);

    const key = new THREE.PointLight(toneCurve.hue, 1.7, 30, 2);
    key.position.set(4.4, 2.5, 5.2);
    scene.add(key);

    const fill = new THREE.PointLight("#ffb84d", 1.2, 24, 2);
    fill.position.set(-4.5, -2.1, 3.6);
    scene.add(fill);

    const planetGeo = new THREE.SphereGeometry(1.55, 128, 128);
    const planetMat = new THREE.MeshStandardMaterial({
      color: sceneDirection.colorBias,
      emissive: sceneDirection.colorBias,
      emissiveIntensity: 0.35,
      roughness: 0.46,
      metalness: 0.22
    });
    const textureLoader = new THREE.TextureLoader();
    if (onLookersBrandDirection.assetOverrides.heroNormalMapUrl) {
      const normalTexture = textureLoader.load(onLookersBrandDirection.assetOverrides.heroNormalMapUrl);
      normalTexture.wrapS = THREE.RepeatWrapping;
      normalTexture.wrapT = THREE.RepeatWrapping;
      normalTexture.repeat.set(1.15, 1.15);
      planetMat.normalMap = normalTexture;
      planetMat.normalScale = new THREE.Vector2(0.35, 0.35);
    }
    const planet = new THREE.Mesh(planetGeo, planetMat);
    heroRig.add(planet);
    heroRig.scale.setScalar(sceneDirection.heroScale);
    heroRig.position.y = sceneDirection.heroYOffset;

    const shellGeo = new THREE.SphereGeometry(1.7, 96, 96);
    const shellMat = new THREE.MeshBasicMaterial({
      color: "#00e5ff",
      transparent: true,
      opacity: 0.08,
      wireframe: true
    });
    const shell = new THREE.Mesh(shellGeo, shellMat);
    heroRig.add(shell);

    const ringGeo = new THREE.TorusGeometry(2.25, 0.02, 16, 320);
    const ringMat = new THREE.MeshBasicMaterial({ color: "#75d8ff", transparent: true, opacity: 0.25 });
    const ring = new THREE.Mesh(ringGeo, ringMat);
    ring.rotation.x = Math.PI * sceneDirection.ringTiltX;
    ring.rotation.y = Math.PI * sceneDirection.ringTiltY;
    heroRig.add(ring);

    const energyGeo = new THREE.TorusKnotGeometry(1.95, 0.045, 220, 24, 3, 5);
    const energyMat = new THREE.MeshBasicMaterial({ color: toneCurve.hue, transparent: true, opacity: 0.24, wireframe: true });
    const energyMesh = new THREE.Mesh(energyGeo, energyMat);
    energyMesh.rotation.x = Math.PI * (0.2 + sceneDirection.ringTiltY * 0.2);
    energyMesh.rotation.z = Math.PI * 0.1;
    heroRig.add(energyMesh);

    const starCount = config.starCount;
    const starPositions = new Float32Array(starCount * 3);
    for (let i = 0; i < starCount; i += 1) {
      const i3 = i * 3;
      const radius = 16 + Math.random() * 24;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos((Math.random() * 2) - 1);
      starPositions[i3] = radius * Math.sin(phi) * Math.cos(theta);
      starPositions[i3 + 1] = radius * Math.sin(phi) * Math.sin(theta);
      starPositions[i3 + 2] = radius * Math.cos(phi);
    }

    const starsGeo = new THREE.BufferGeometry();
    starsGeo.setAttribute("position", new THREE.BufferAttribute(starPositions, 3));
    const starsMat = new THREE.PointsMaterial({ color: "#ddf2ff", size: 0.06, sizeAttenuation: true, transparent: true, opacity: 0.55 });
    const stars = new THREE.Points(starsGeo, starsMat);
    scene.add(stars);

    const sectionTweens: gsap.core.Animation[] = [];
    const sectionTriggers: ScrollTrigger[] = [];

    const composer = new EffectComposer(renderer);
    const renderPass = new RenderPass(scene, camera);
    const bloomPass = new UnrealBloomPass(new THREE.Vector2(window.innerWidth, window.innerHeight), config.bloomBase, 0.65, 0.2);
    const filmPass = new FilmPass(config.filmIntensity, false);
    composer.addPass(renderPass);
    composer.addPass(bloomPass);
    composer.addPass(filmPass);

    const pointer = { x: 0, y: 0 };
    const pointerTarget = { x: 0, y: 0 };

    const onPointerMove = (event: PointerEvent) => {
      pointerTarget.x = (event.clientX / window.innerWidth) * 2 - 1;
      pointerTarget.y = (event.clientY / window.innerHeight) * 2 - 1;
    };

    const setSize = () => {
      const width = window.innerWidth;
      const height = window.innerHeight;
      renderer.setSize(width, height, false);
      composer.setSize(width, height);
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
    };

    setSize();
    window.addEventListener("resize", setSize);
    window.addEventListener("pointermove", onPointerMove, { passive: true });

    const intro = gsap.timeline({ defaults: { ease: "power2.out" } });
    intro.fromTo(
      camera.position,
      { z: toneCurve.startZ, y: toneCurve.y + 0.62 },
      { z: toneCurve.endZ, y: toneCurve.y, duration: 2.2 / cameraFactor }
    );
    intro.fromTo(planet.scale, { x: 0.5, y: 0.5, z: 0.5 }, { x: 1, y: 1, z: 1, duration: 1.4 }, "<");
    intro.fromTo(bloomPass, { strength: 2.3 }, { strength: (toneCurve.bloom + sceneDirection.bloomLift) * glowFactor, duration: 2.2 / cameraFactor }, "<");

    const hudPulse = gsap.timeline({ repeat: -1, repeatDelay: 1.8 });
    hudPulse
      .to(".hud-label", { textShadow: `0 0 14px ${toneCurve.hue}66`, duration: 0.4, stagger: 0.02 })
      .to(".hud-label", { textShadow: "0 0 0 rgba(0,0,0,0)", duration: 0.5, stagger: 0.02 });

    const scrollControl = hasMatchMedia
      ? ScrollTrigger.create({
          trigger: document.documentElement,
          start: "top top",
          end: "bottom bottom",
          scrub: 1.1,
          onUpdate: (self) => {
            const progress = self.progress;
            camera.position.z = toneCurve.endZ - progress * (1.55 * cameraFactor);
            camera.position.y = toneCurve.y - progress * (0.34 * cameraFactor);
            bloomPass.strength = (config.bloomBase + sceneDirection.bloomLift + progress * config.bloomBoost) * glowFactor;
            heroRig.rotation.y = progress * (0.5 + sceneDirection.energySpin * 0.14) * cameraFactor;
            renderer.toneMappingExposure = 1.02 + progress * 0.18;
          }
        })
      : null;

    if (hasMatchMedia) {
      const storyPanels = gsap.utils.toArray<HTMLElement>("[data-story-panel='true'], [data-story-chapter='true']");
      storyPanels.forEach((panel, index) => {
        const influence = 0.14 + Math.min(index * 0.03, 0.12);
        const tween = gsap.timeline({
          scrollTrigger: {
            trigger: panel,
            start: "top 84%",
            end: "top 34%",
            scrub: 0.65
          }
        });

        tween
          .to(heroRig.rotation, { x: -influence * 0.55 * cameraFactor, y: influence * cameraFactor, z: influence * 0.15, duration: 1, ease: "none" }, 0)
          .to(energyMesh.rotation, { x: Math.PI * (0.22 + influence), y: influence * (1.8 + sceneDirection.energySpin), duration: 1, ease: "none" }, 0)
          .to(key.position, { x: 4.4 - influence * 2.1 * cameraFactor, y: 2.5 + influence * 1.5 * cameraFactor, duration: 1, ease: "none" }, 0)
          .to(fill.position, { x: -4.5 + influence * 2.4 * cameraFactor, y: -2.1 + influence * 1.2 * cameraFactor, duration: 1, ease: "none" }, 0)
          .to(camera, { fov: 50 - influence * 16 * cameraFactor, duration: 1, ease: "none", onUpdate: () => camera.updateProjectionMatrix() }, 0);

        sectionTweens.push(tween);
        if (tween.scrollTrigger) {
          sectionTriggers.push(tween.scrollTrigger);
        }
      });
    }

    let raf = 0;
    const clock = new THREE.Clock();

    const frame = () => {
      const elapsed = clock.getElapsedTime();
      pointer.x += (pointerTarget.x - pointer.x) * 0.032;
      pointer.y += (pointerTarget.y - pointer.y) * 0.032;

      planet.rotation.y += 0.0012;
      planet.rotation.x = Math.sin(elapsed * 0.13) * 0.12;
      shell.rotation.y -= 0.0016;
      shell.rotation.z = Math.sin(elapsed * 0.08) * 0.24;
      ring.rotation.z += 0.0009;
      energyMesh.rotation.z += 0.0018 * sceneDirection.energySpin;
      stars.rotation.y += 0.00015;

      camera.position.x += (pointer.x * 0.75 - camera.position.x) * 0.022;
      camera.lookAt(0, 0, 0);

      composer.render();
      raf = window.requestAnimationFrame(frame);
    };

    frame();

    return () => {
      window.cancelAnimationFrame(raf);
      scrollControl?.kill();
      sectionTriggers.forEach((trigger) => trigger.kill());
      sectionTweens.forEach((tween) => tween.kill());
      intro.kill();
      hudPulse.kill();
      window.removeEventListener("resize", setSize);
      window.removeEventListener("pointermove", onPointerMove);

      planetGeo.dispose();
      if (planetMat.normalMap) {
        planetMat.normalMap.dispose();
      }
      planetMat.dispose();
      shellGeo.dispose();
      shellMat.dispose();
      ringGeo.dispose();
      ringMat.dispose();
      energyGeo.dispose();
      energyMat.dispose();
      starsGeo.dispose();
      starsMat.dispose();
      composer.dispose();
      renderer.dispose();
    };
  }, [config.bloomBase, config.bloomBoost, config.filmIntensity, config.pixelRatioMax, config.starCount, tone]);

  return <canvas ref={canvasRef} className="cinematic-webgl-backdrop" aria-hidden="true" />;
}
