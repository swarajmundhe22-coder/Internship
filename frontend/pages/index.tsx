import { Toaster } from "sonner";

import AlgorithmSection from "../components/outsource/AlgorithmSection";
import FeaturesSection from "../components/outsource/FeaturesSection";
import FooterSection from "../components/outsource/FooterSection";
import HeroSection from "../components/outsource/HeroSection";
import IndustriesSection from "../components/outsource/IndustriesSection";
import Navigation from "../components/outsource/Navigation";
import PlatformSection from "../components/outsource/PlatformSection";
import RoadmapSection from "../components/outsource/RoadmapSection";
import SimulationSection from "../components/outsource/SimulationSection";

export default function LandingPage() {
  return (
    <div className="outsource-home min-h-screen" style={{ background: "#050508", color: "#f0f0f5" }}>
      <Toaster richColors position="top-right" />
      <div className="noise-overlay" />
      <div className="scan-line" />
      <Navigation />

      <main>
        <HeroSection />
        <PlatformSection />
        <AlgorithmSection />
        <FeaturesSection />
        <SimulationSection />
        <IndustriesSection />
        <RoadmapSection />
      </main>

      <FooterSection />
    </div>
  );
}
