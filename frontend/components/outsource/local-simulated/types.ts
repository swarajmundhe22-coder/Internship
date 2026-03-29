import type { SimulationInputPayload, SimulationResultPayload } from './backendClient';

export type Act =
  | 'ACT0'
  | 'ACT1'
  | 'ACT_DASHBOARD'
  | 'ACT2'
  | 'ACT3'
  | 'ACT4'
  | 'ACT5'
  | 'ACT_MANUAL'
  | 'ACT_COMPARISON'
  | 'ACT_COMPLIANCE_ROADMAP'
  | 'ACT_MATERIAL_INTELLIGENCE'
  | 'ACT_PORTFOLIO_ANALYTICS'
  | 'ACT_GEOSPATIAL_MAP';

export type LocalSimUser = {
  uid: string;
  email: string;
  displayName: string;
  role: string;
};

export type LocalScenario = {
  id: string;
  name: string;
  data: SimulationInputPayload & Record<string, unknown>;
  result: (SimulationResultPayload & Record<string, unknown>) | Record<string, unknown>;
  createdAt: string;
};

export type LocalProject = {
  id: string;
  name: string;
  ownerId: string;
  parameters: (SimulationInputPayload & Record<string, unknown>) | null;
  scenarios: LocalScenario[];
  createdAt: string;
  updatedAt: string;
};

export type BackendProjectRecord = {
  id: string;
  name: string;
  user_id: string;
  metadata?: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
};

export type CommandPaletteAction = {
  id: string;
  label: string;
  hint: string;
  run: () => void;
};
