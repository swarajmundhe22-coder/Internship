import type { BackendProjectRecord, LocalProject, LocalScenario } from './types';

const SCENARIO_STORAGE_KEY = 'onlooker_local_simulated_scenarios_v1';

export function displayNameFromEmail(email: string): string {
  const fallback = 'Operator';
  const localPart = email.split('@')[0]?.trim();
  if (!localPart) {
    return fallback;
  }

  return localPart
    .split(/[._-]/g)
    .filter(Boolean)
    .map((token) => token.charAt(0).toUpperCase() + token.slice(1))
    .join(' ');
}

export function loadScenarioMap(): Record<string, LocalScenario[]> {
  if (typeof window === 'undefined') {
    return {};
  }

  try {
    const raw = window.localStorage.getItem(SCENARIO_STORAGE_KEY);
    if (!raw) {
      return {};
    }

    const parsed = JSON.parse(raw);
    return typeof parsed === 'object' && parsed ? parsed : {};
  } catch {
    return {};
  }
}

export function persistScenarioMap(map: Record<string, LocalScenario[]>): void {
  if (typeof window === 'undefined') {
    return;
  }

  window.localStorage.setItem(SCENARIO_STORAGE_KEY, JSON.stringify(map));
}

export function hydrateProjects(
  projects: BackendProjectRecord[],
  scenarioMap: Record<string, LocalScenario[]>
): LocalProject[] {
  return projects.map((project) => {
    const metadata = typeof project.metadata === 'object' && project.metadata ? project.metadata : {};
    const metadataScenarios = Array.isArray((metadata as { scenarios?: unknown }).scenarios)
      ? ((metadata as { scenarios?: LocalScenario[] }).scenarios ?? [])
      : [];
    const storedScenarios = Array.isArray(scenarioMap[project.id]) ? scenarioMap[project.id] : [];

    return {
      id: project.id,
      name: project.name,
      ownerId: project.user_id,
      parameters: ((metadata as { parameters?: LocalProject['parameters'] }).parameters ?? null),
      scenarios: storedScenarios.length > 0 ? storedScenarios : metadataScenarios,
      createdAt: project.created_at,
      updatedAt: project.updated_at,
    };
  });
}

export function generateScenarioId(): string {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }
  return Math.random().toString(36).slice(2, 11);
}
