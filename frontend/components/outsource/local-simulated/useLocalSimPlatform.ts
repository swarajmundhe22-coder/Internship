import { useCallback, useEffect, useState } from 'react';

import { toast } from 'sonner';

import { apiFetch } from '../../../utils/api';
import {
  askCopilot,
  attachSimulationToProject,
  type CriticalRequestOptions,
  getAccessTokenClaims,
  runSimulationWithPersistence,
} from './backendClient';
import {
  displayNameFromEmail,
  generateScenarioId,
  hydrateProjects,
  loadScenarioMap,
  persistScenarioMap,
} from './platformUtils';
import { executeCriticalApiRequest, toErrorSummary } from './resilience';
import { createTraceContext, emitDomainEvent, type TraceContext } from './telemetry';
import type { Act, BackendProjectRecord, LocalProject, LocalScenario, LocalSimUser } from './types';

type ProjectSelectionPayload = {
  id: string;
  name: string;
  ownerId?: string;
  parameters: LocalProject['parameters'];
  scenarios?: LocalProject['scenarios'];
  createdAt?: string;
  updatedAt?: string;
};

export function normalizeProjectPayload(
  project: ProjectSelectionPayload,
  fallbackOwnerId: string | undefined
): LocalProject {
  const nowIso = new Date().toISOString();

  return {
    id: project.id,
    name: project.name,
    ownerId: project.ownerId ?? fallbackOwnerId ?? 'unknown',
    parameters: project.parameters ?? null,
    scenarios: Array.isArray(project.scenarios) ? project.scenarios : [],
    createdAt: project.createdAt ?? nowIso,
    updatedAt: project.updatedAt ?? nowIso,
  };
}

export function useLocalSimPlatform() {
  const [user, setUser] = useState<LocalSimUser | null>(null);
  const [isAuthReady, setIsAuthReady] = useState(false);
  const [currentAct, setCurrentAct] = useState<Act>('ACT0');
  const [simulationData, setSimulationData] = useState<any>(null);
  const [simulationResult, setSimulationResult] = useState<any>(null);
  const [narrative, setNarrative] = useState('');
  const [activeProjectId, setActiveProjectId] = useState<string | null>(null);
  const [currentProject, setCurrentProject] = useState<LocalProject | null>(null);
  const [isSyncing, setIsSyncing] = useState(false);
  const [showAIAdvisor, setShowAIAdvisor] = useState(false);
  const [allProjects, setAllProjects] = useState<LocalProject[]>([]);
  const [scenarioMap, setScenarioMap] = useState<Record<string, LocalScenario[]>>({});
  const [hasShownGuestModeNotice, setHasShownGuestModeNotice] = useState(false);

  useEffect(() => {
    const traceContext = createTraceContext();
    const claims = getAccessTokenClaims();
    if (!claims) {
      emitDomainEvent('auth.session.missing', {}, traceContext, 'warn');
      setUser(null);
      setIsAuthReady(true);
      return;
    }

    emitDomainEvent(
      'auth.session.restored',
      {
        actorId: claims.sub,
        role: claims.role,
      },
      traceContext
    );

    setUser({
      uid: claims.sub,
      email: claims.email,
      displayName: displayNameFromEmail(claims.email),
      role: claims.role,
    });
    setIsAuthReady(true);
  }, []);

  useEffect(() => {
    setScenarioMap(loadScenarioMap());
  }, []);

  const refreshProjects = useCallback(async (traceSeed?: Partial<TraceContext>) => {
    const traceContext = createTraceContext({
      ...traceSeed,
      actorId: traceSeed?.actorId ?? user?.uid,
      projectId: traceSeed?.projectId ?? activeProjectId ?? undefined,
    });

    if (!user) {
      emitDomainEvent('projects.refresh.skipped', { reason: 'anonymous_session' }, traceContext, 'warn');
      setAllProjects([]);
      return;
    }

    emitDomainEvent('projects.refresh.started', {}, traceContext);

    try {
      const projects = await executeCriticalApiRequest(
        () => apiFetch<BackendProjectRecord[]>('/projects'),
        {
          operation: 'projects.list',
          path: '/projects',
          method: 'GET',
          traceContext,
          maxAttempts: 3,
        }
      );

      emitDomainEvent(
        'projects.refresh.succeeded',
        {
          projectCount: projects.length,
        },
        traceContext
      );

      setAllProjects(hydrateProjects(projects, scenarioMap));
    } catch (error) {
      emitDomainEvent(
        'projects.refresh.failed',
        {
          ...toErrorSummary(error),
        },
        traceContext,
        'error'
      );
      console.error('Project load error:', error);
      toast.error('Unable to load project vault');
    }
  }, [activeProjectId, scenarioMap, user]);

  useEffect(() => {
    void refreshProjects();
  }, [refreshProjects]);

  const handleSignIn = useCallback(async () => {
    emitDomainEvent('auth.sign_in.redirect_requested', {}, createTraceContext());
    if (typeof window !== 'undefined') {
      window.location.href = '/auth/login?next=/';
    }
  }, []);

  const handleSignOut = useCallback(async () => {
    const traceContext = createTraceContext({
      actorId: user?.uid,
      projectId: activeProjectId ?? undefined,
    });

    if (typeof window !== 'undefined') {
      window.localStorage.removeItem('onlooker_token');
      window.localStorage.removeItem('onlooker_refresh_token');
    }

    setUser(null);
    setAllProjects([]);
    setActiveProjectId(null);
    setCurrentProject(null);
    emitDomainEvent('auth.sign_out.completed', {}, traceContext);
    toast.info('Session closed');
  }, [activeProjectId, user?.uid]);

  const generateNarrative = useCallback(async (data: any, result: any, traceSeed?: Partial<TraceContext>) => {
    const traceContext = createTraceContext({
      ...traceSeed,
      actorId: traceSeed?.actorId ?? user?.uid,
      projectId: traceSeed?.projectId ?? activeProjectId ?? undefined,
    });

    emitDomainEvent(
      'narrative.generation.started',
      {
        material: data.material,
        structure: data.structure,
      },
      traceContext
    );

    try {
      const prompt = `You are a Senior Corrosion Engineer. Based on the following real-world data and simulation results, provide a 2-sentence cinematic risk briefing.
      Material: ${data.material}
      Structure: ${data.structure}
      Environment: Temp ${data.temperature} C, Humidity ${data.humidity}%, Salinity ${data.salinity}g/L, pH ${data.pH}.
      Simulation Result: Risk Score ${result.riskScore}/100, Predicted Lifespan ${result.predictedLifespan} years.
      
      Respond with concise executive language. No markdown.`;

      const response = await askCopilot(prompt, undefined, {
        traceId: traceContext.traceId,
        actorId: traceContext.actorId,
        projectId: traceContext.projectId,
      });
      setNarrative(response || result.recommendationSummary || 'Simulation complete. Priority intervention required.');
      emitDomainEvent('narrative.generation.succeeded', { hasResponse: Boolean(response) }, traceContext);
    } catch (error) {
      emitDomainEvent(
        'narrative.generation.failed',
        {
          ...toErrorSummary(error),
        },
        traceContext,
        'error'
      );
      console.error('Narrative generation error:', error);
      setNarrative('The microscopic battle has concluded. Structural failure is imminent.');
    }
  }, [activeProjectId, user?.uid]);

  const startSimulation = useCallback(
    async (data: any) => {
      const traceContext = createTraceContext({
        actorId: user?.uid,
        projectId: activeProjectId ?? undefined,
      });

      if (data.goToManual) {
        emitDomainEvent('orchestration.simulation.redirect_manual', {}, traceContext);
        setCurrentAct('ACT_MANUAL');
        return;
      }

      emitDomainEvent(
        'orchestration.simulation.started',
        {
          structure: data?.structure,
          material: data?.material,
        },
        traceContext
      );

      setSimulationData(data);
      setCurrentAct('ACT3');
      setIsSyncing(true);

      try {
        const requestOptions: CriticalRequestOptions = {
          traceId: traceContext.traceId,
          actorId: traceContext.actorId,
          projectId: traceContext.projectId,
        };

        const result = await runSimulationWithPersistence(data, requestOptions);
        setSimulationResult({ ...result, inputData: data });

        if (user) {
          if (activeProjectId) {
            await attachSimulationToProject(activeProjectId, result.backendSimulationId, requestOptions);
            toast.success('Simulation linked to active project');
          } else {
            const createdProject = await executeCriticalApiRequest(
              () =>
                apiFetch<{ id: string }>('/projects', {
                  method: 'POST',
                  body: JSON.stringify({
                    name: `${data.structure} Analysis`,
                    metadata: {
                      source: 'local-simulated-v2',
                      parameters: data,
                    },
                  }),
                }),
              {
                operation: 'projects.create',
                path: '/projects',
                method: 'POST',
                traceContext,
                maxAttempts: 3,
              }
            );

            emitDomainEvent(
              'projects.created',
              {
                projectId: createdProject.id,
              },
              traceContext
            );

            setActiveProjectId(createdProject.id);
            await attachSimulationToProject(createdProject.id, result.backendSimulationId, {
              ...requestOptions,
              projectId: createdProject.id,
            });
            toast.success('Project created and simulation archived');
          }
        } else {
          emitDomainEvent('orchestration.simulation.anonymous_archive_skipped', {}, traceContext, 'warn');
          toast.info('Sign in to archive this simulation to your project vault');
        }

        await refreshProjects({
          traceId: traceContext.traceId,
          actorId: traceContext.actorId,
          projectId: activeProjectId ?? undefined,
        });

        emitDomainEvent(
          'orchestration.simulation.completed',
          {
            backendSimulationId: result.backendSimulationId,
          },
          traceContext
        );
      } catch (error) {
        emitDomainEvent(
          'orchestration.simulation.failed',
          {
            ...toErrorSummary(error),
          },
          traceContext,
          'error'
        );
        console.error('Simulation calculation error:', error);
        setSimulationResult({
          riskScore: 65,
          corrosionRate: 0.08,
          predictedLifespan: 15,
          degradationTimeline: [
            { year: 0, thickness: 100 },
            { year: 5, thickness: 95 },
            { year: 10, thickness: 90 },
            { year: 15, thickness: 85 },
            { year: 20, thickness: 80 },
          ],
        });
        toast.error('Simulation service unavailable. Showing fallback estimate.');
      } finally {
        setIsSyncing(false);
      }
    },
    [activeProjectId, refreshProjects, user]
  );

  const handleProjectSelect = useCallback((project: ProjectSelectionPayload) => {
    const normalizedProject = normalizeProjectPayload(project, user?.uid);
    const traceContext = createTraceContext({
      actorId: user?.uid,
      projectId: normalizedProject.id,
    });

    emitDomainEvent(
      'orchestration.project.selected',
      {
        projectId: normalizedProject.id,
      },
      traceContext
    );

    setActiveProjectId(normalizedProject.id);
    setCurrentProject(normalizedProject);

    const fallbackData =
      normalizedProject.parameters ??
      normalizedProject.scenarios?.[normalizedProject.scenarios.length - 1]?.data ??
      null;

    setSimulationData(fallbackData);
    setCurrentAct('ACT2');
    toast.info(`Resuming ${normalizedProject.name}`);
  }, [user?.uid]);

  const openProjectComparison = useCallback((project: ProjectSelectionPayload) => {
    const normalizedProject = normalizeProjectPayload(project, user?.uid);
    emitDomainEvent(
      'orchestration.project.comparison_opened',
      {
        projectId: normalizedProject.id,
      },
      createTraceContext({
        actorId: user?.uid,
        projectId: normalizedProject.id,
      })
    );
    setCurrentProject(normalizedProject);
    setCurrentAct('ACT_COMPARISON');
  }, [user?.uid]);

  const handleSaveScenario = useCallback(
    async (name: string) => {
      const traceContext = createTraceContext({
        actorId: user?.uid,
        projectId: activeProjectId ?? undefined,
      });

      if (!activeProjectId) {
        emitDomainEvent('orchestration.scenario.save_skipped', { reason: 'no_active_project' }, traceContext, 'warn');
        toast.error('Create or open a project before saving scenarios');
        return;
      }

      emitDomainEvent(
        'orchestration.scenario.save_started',
        {
          scenarioName: name,
        },
        traceContext
      );

      const newScenario: LocalScenario = {
        id: generateScenarioId(),
        name,
        data: simulationData,
        result: simulationResult,
        createdAt: new Date().toISOString(),
      };

      try {
        setScenarioMap((previousMap) => {
          const nextMap = {
            ...previousMap,
            [activeProjectId]: [...(previousMap[activeProjectId] || []), newScenario],
          };

          persistScenarioMap(nextMap);
          return nextMap;
        });

        setCurrentProject((previousProject) => {
          if (!previousProject) {
            return previousProject;
          }

          return {
            ...previousProject,
            scenarios: [...previousProject.scenarios, newScenario],
          };
        });

        setAllProjects((previousProjects) =>
          previousProjects.map((project) =>
            project.id !== activeProjectId
              ? project
              : { ...project, scenarios: [...project.scenarios, newScenario] }
          )
        );

        emitDomainEvent(
          'orchestration.scenario.save_succeeded',
          {
            scenarioId: newScenario.id,
            scenarioName: newScenario.name,
          },
          traceContext
        );
        toast.success('Scenario saved to project vault');
      } catch (error) {
        emitDomainEvent(
          'orchestration.scenario.save_failed',
          {
            scenarioName: name,
            ...toErrorSummary(error),
          },
          traceContext,
          'error'
        );
        console.error(error);
        toast.error('Failed to save scenario');
      }
    },
    [activeProjectId, simulationData, simulationResult, user?.uid]
  );

  const handleNewProject = useCallback(() => {
    if (!user && !hasShownGuestModeNotice) {
      emitDomainEvent(
        'orchestration.guest_mode.notice_shown',
        {
          destinationAct: 'ACT2',
        },
        createTraceContext()
      );
      toast.info('Guest mode enabled: live reports, analytics graphs, and project vault data require sign in.');
      setHasShownGuestModeNotice(true);
    }

    emitDomainEvent(
      'orchestration.project.new_requested',
      {},
      createTraceContext({
        actorId: user?.uid,
      })
    );
    setActiveProjectId(null);
    setSimulationData(null);
    setCurrentAct('ACT2');
  }, [hasShownGuestModeNotice, user]);

  const completeSimulation = useCallback(async () => {
    const traceContext = createTraceContext({
      actorId: user?.uid,
      projectId: activeProjectId ?? undefined,
    });

    emitDomainEvent('orchestration.simulation.complete_requested', {}, traceContext);
    setCurrentAct('ACT4');
    if (simulationData && simulationResult) {
      await generateNarrative(simulationData, simulationResult, traceContext);
    }
  }, [activeProjectId, generateNarrative, simulationData, simulationResult, user?.uid]);

  const resetToStart = useCallback(() => {
    emitDomainEvent(
      'orchestration.reset_to_start',
      {},
      createTraceContext({
        actorId: user?.uid,
      })
    );
    setActiveProjectId(null);
    setSimulationData(null);
    setSimulationResult(null);
    setCurrentAct('ACT0');
  }, [user?.uid]);

  return {
    user,
    isAuthReady,
    currentAct,
    setCurrentAct,
    simulationData,
    simulationResult,
    narrative,
    currentProject,
    isSyncing,
    showAIAdvisor,
    setShowAIAdvisor,
    allProjects,
    handleSignIn,
    handleSignOut,
    startSimulation,
    handleProjectSelect,
    openProjectComparison,
    handleSaveScenario,
    handleNewProject,
    completeSimulation,
    resetToStart,
    refreshProjects,
  };
}
