export type StoryboardPhase = {
  phase: number;
  name: string;
  camera: string;
  lighting: string;
  transition: string;
  narrative: string;
};

export const phaseStoryboard: StoryboardPhase[] = [
  {
    phase: 1,
    name: "Simulation Engine",
    camera: "Wide establishing shot over rotating planetary surface.",
    lighting: "Cold blue with predictive sparks.",
    transition: "HUD schematics materialize from particle fog.",
    narrative: "Initiating physics-driven foresight. Risk stratification engaged."
  },
  {
    phase: 2,
    name: "Tenant Backbone",
    camera: "Cockpit close-up with panel assembly around operator.",
    lighting: "Cyan identity beams tracing tenant channels.",
    transition: "Panels lock in with rippled hologram snap.",
    narrative: "Tenant identity secured. Role-governed cockpit provisioned."
  },
  {
    phase: 3,
    name: "RBAC Enforcement",
    camera: "Security gate zoom with lock glyph overlays.",
    lighting: "Red pulses signal denied access attempts.",
    transition: "Alarm sweep and gate hard-close animation.",
    narrative: "Role-based access enforced. Unauthorized entry blocked."
  },
  {
    phase: 4,
    name: "Copilot Endpoints",
    camera: "Cinematic sweep across neural pathways.",
    lighting: "Gold thread responses through advisor nodes.",
    transition: "Advisor panes appear as holographic apparitions.",
    narrative: "AI foresight companion online. Query channels open."
  },
  {
    phase: 5,
    name: "Billing Integration",
    camera: "Subscription emblem close-up.",
    lighting: "Green acceptance pulse, red rejection ripple.",
    transition: "Vault-like unlock and tier elevation flare.",
    narrative: "Subscription tier validated. Planetary foresight unlocked."
  },
  {
    phase: 6,
    name: "Audit Logs",
    camera: "Data corridor tracking every logged action.",
    lighting: "White tracer beams with archival glow.",
    transition: "Log waterfall cascading into immutable timeline.",
    narrative: "Audit trail complete. Regulator-ready compliance dossier formed."
  },
  {
    phase: 7,
    name: "Multi-Tenant Backbone",
    camera: "Wide fleet formation around a central world model.",
    lighting: "Distinct cockpit signatures per tenant channel.",
    transition: "Federated HUDs materialize into synchronized orbit.",
    narrative: "Multi-tenant backbone activated. Global foresight federation online."
  },
  {
    phase: 8,
    name: "Immersive Visualization",
    camera: "Digital twin zoom with hazard overlays.",
    lighting: "Escalating glow from green to red severity.",
    transition: "Playback slider drives a cinematic mission timeline.",
    narrative: "Immersive foresight playback engaged. Digital twin activated."
  },
  {
    phase: 9,
    name: "Global Intelligence Network",
    camera: "Planetary sweep with satellite constellations.",
    lighting: "Continental pulses and aurora overlays.",
    transition: "Atlas zoom transitions into regional focus.",
    narrative: "Global risk atlas online. IoT and satellite foresight integrated."
  },
  {
    phase: 10,
    name: "Governance Consortium",
    camera: "Emblem close-up in final-act framing.",
    lighting: "Golden pulses for tier unlock and governance authority.",
    transition: "Badge forms from light particles and resolves to cockpit HUD.",
    narrative: "Planetary Intelligence Order established. Governance cockpit complete."
  }
];
