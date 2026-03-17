import Link from "next/link";
import { useRouter } from "next/router";
import { useEffect, useMemo, useState } from "react";

import { ChapterHeader, HudBadge, TacticalButton, TelemetryCard } from "../../components/CinematicHud";
import { FilterBar } from "../../components/FilterBar";
import { LayoutShell } from "../../components/LayoutShell";
import { TableShell } from "../../components/TableShell";
import { useApi } from "../../hooks/useApi";
import { useUrlQueryState } from "../../hooks/useUrlQueryState";
import {
  EnvironmentProfile,
  Material,
  PaginatedResponse,
  ProjectCollaborator,
  ProjectDetail,
  ProjectRole,
  ProjectSimulationSummary
} from "../../types/domain";
import { buildQueryString, toDateTimeEnd, toDateTimeStart } from "../../utils/query";

function formatDateTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString();
}

function getCurrentUserIdFromToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }

  const token = window.localStorage.getItem("onlooker_token");
  if (!token) {
    return null;
  }

  try {
    const payload = token.split(".")[1];
    const decoded = JSON.parse(window.atob(payload));
    return typeof decoded.sub === "string" ? decoded.sub : null;
  } catch {
    return null;
  }
}

function roleBadgeClass(role: ProjectRole): string {
  if (role === "Owner") {
    return "border-signal/70 bg-signal/15 text-signal";
  }
  if (role === "Collaborator") {
    return "border-lagoon/70 bg-lagoon/15 text-lagoon";
  }
  return "border-neoviolet/70 bg-neoviolet/15 text-neoviolet";
}

export default function ProjectDetailPage() {
  const router = useRouter();
  const { id } = router.query;
  const {
    run,
    loading,
    error,
    getProjectCollaborators,
    addProjectCollaborator,
    updateProjectCollaborator,
    deleteProjectCollaborator
  } = useApi();
  const { state, setQuery, isReady } = useUrlQueryState({
    page: "1",
    page_size: "10",
    material_id: "",
    environment_id: "",
    risk_level: "",
    created_from: "",
    created_to: ""
  });

  const [project, setProject] = useState<ProjectDetail | null>(null);
  const [materials, setMaterials] = useState<Material[]>([]);
  const [environments, setEnvironments] = useState<EnvironmentProfile[]>([]);
  const [collaborators, setCollaborators] = useState<ProjectCollaborator[]>([]);
  const [collaboratorPanelOpen, setCollaboratorPanelOpen] = useState(false);
  const [collaboratorEmail, setCollaboratorEmail] = useState("");
  const [collaboratorRole, setCollaboratorRole] = useState<ProjectRole>("Collaborator");
  const [collaboratorMessage, setCollaboratorMessage] = useState<string | null>(null);
  const [collaboratorError, setCollaboratorError] = useState<string | null>(null);

  const page = Number(state.page) || 1;
  const pageSize = Number(state.page_size) || 10;
  const projectId = project?.id;

  const currentUserId = useMemo(() => getCurrentUserIdFromToken(), [router.isReady]);
  const currentMembership = useMemo(
    () => collaborators.find((item) => item.user_id === currentUserId),
    [collaborators, currentUserId]
  );
  const currentRole: ProjectRole = currentMembership?.role ?? "Viewer";
  const canManageCollaborators = currentRole === "Owner";
  const canChangeProjectData = currentRole === "Owner" || currentRole === "Collaborator";

  const baseSimulationId = useMemo(() => {
    if (!router.isReady) {
      return "";
    }
    const value = router.query.base_simulation_id;
    return typeof value === "string" ? value : "";
  }, [router.isReady, router.query.base_simulation_id]);

  const filterFields = useMemo(
    () => [
      {
        key: "material_id",
        label: "Material",
        type: "select" as const,
        options: materials.map((item) => ({ label: item.name, value: item.id }))
      },
      {
        key: "environment_id",
        label: "Environment",
        type: "select" as const,
        options: environments.map((item) => ({ label: item.profile_name, value: item.id }))
      },
      {
        key: "risk_level",
        label: "Risk Level",
        type: "select" as const,
        options: [
          { label: "Low", value: "low" },
          { label: "Moderate", value: "moderate" },
          { label: "High", value: "high" },
          { label: "Critical", value: "critical" }
        ]
      },
      { key: "created_from", label: "Created From", type: "date" as const },
      { key: "created_to", label: "Created To", type: "date" as const }
    ],
    [materials, environments]
  );

  async function loadProjectDetails() {
    if (typeof id !== "string") {
      return;
    }

    const query = buildQueryString({
      page,
      page_size: pageSize,
      material_id: state.material_id || undefined,
      environment_id: state.environment_id || undefined,
      risk_level: state.risk_level || undefined,
      created_from: toDateTimeStart(state.created_from),
      created_to: toDateTimeEnd(state.created_to)
    });

    const payload = await run<ProjectDetail>(`/projects/${id}${query}`);
    setProject(payload);
  }

  async function loadReferenceData() {
    const [materialPage, environmentPage] = await Promise.all([
      run<PaginatedResponse<Material>>("/materials?page=1&page_size=200"),
      run<PaginatedResponse<EnvironmentProfile>>("/environment?page=1&page_size=200")
    ]);
    setMaterials(materialPage.items);
    setEnvironments(environmentPage.items);
  }

  async function loadCollaborators() {
    if (typeof id !== "string") {
      return;
    }

    try {
      const data = await getProjectCollaborators(id);
      setCollaborators(data);
      setCollaboratorError(null);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unable to load collaborators";
      setCollaboratorError(message);
    }
  }

  useEffect(() => {
    if (!router.isReady) {
      return;
    }

    void loadReferenceData();
  }, [router.isReady]);

  useEffect(() => {
    if (!router.isReady || !isReady || typeof id !== "string") {
      return;
    }

    void loadProjectDetails();
    void loadCollaborators();
  }, [
    router.isReady,
    isReady,
    id,
    state.page,
    state.page_size,
    state.material_id,
    state.environment_id,
    state.risk_level,
    state.created_from,
    state.created_to
  ]);

  async function onAddCollaborator() {
    if (typeof id !== "string" || !collaboratorEmail.trim()) {
      return;
    }

    try {
      await addProjectCollaborator(id, {
        email: collaboratorEmail.trim(),
        role: collaboratorRole
      });
      setCollaboratorEmail("");
      setCollaboratorRole("Collaborator");
      setCollaboratorMessage("Collaborator added successfully.");
      setCollaboratorError(null);
      await loadCollaborators();
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to add collaborator";
      setCollaboratorError(message);
      setCollaboratorMessage(null);
    }
  }

  async function onUpdateCollaboratorRole(userId: string, role: ProjectRole) {
    if (typeof id !== "string") {
      return;
    }

    try {
      await updateProjectCollaborator(id, userId, { role });
      setCollaboratorMessage("Role updated.");
      setCollaboratorError(null);
      await loadCollaborators();
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to update role";
      setCollaboratorError(message);
      setCollaboratorMessage(null);
    }
  }

  async function onRemoveCollaborator(userId: string) {
    if (typeof id !== "string") {
      return;
    }

    const confirmed = typeof window === "undefined"
      ? true
      : window.confirm("Remove this collaborator from the project workspace?");
    if (!confirmed) {
      return;
    }

    try {
      await deleteProjectCollaborator(id, userId);
      setCollaboratorMessage("Collaborator removed.");
      setCollaboratorError(null);
      await loadCollaborators();
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to remove collaborator";
      setCollaboratorError(message);
      setCollaboratorMessage(null);
    }
  }

  return (
    <LayoutShell
      title={project ? `Project: ${project.name}` : "Project Detail"}
      subtitle="Project workspace with simulation-level actions for reporting and comparison."
    >
      <section className="panel mb-6 p-6">
        {loading && <p className="text-sm text-slate-500">Loading project workspace...</p>}
        {error && <p className="text-sm text-red-700">{error}</p>}

        {!loading && !error && project && (
          <div className="grid gap-3 text-sm">
            <div className="flex flex-wrap gap-2">
              <TacticalButton href={`/projects/${project.id}/reports`} tone="support">Open Project Reports Hub</TacticalButton>
              <TacticalButton href={`/projects/${project.id}/comparison-sets`} tone="alert">Open Comparison Sets</TacticalButton>
              <TacticalButton href={`/projects/${project.id}/activity`}>Open Activity Timeline</TacticalButton>
              <TacticalButton href={`/projects/${project.id}/insights`} tone="support">Open AI Insights</TacticalButton>
            </div>

            <div className="hud-grid md:grid-cols-2">
              <TelemetryCard label="Project Name" value={project.name} tone="primary" />
              <TelemetryCard label="Project ID" value={project.id} tone="support" />
              <TelemetryCard label="Created" value={formatDateTime(project.created_at)} tone="primary" />
              <TelemetryCard label="Saved Simulations" value={project.simulations.total} tone="alert" />
            </div>
          </div>
        )}
      </section>

      <section className="panel mb-6 grid gap-4 p-6">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div>
            <ChapterHeader eyebrow="Access Module" title="Collaborators" description="Role-governed access for this project workspace." />
          </div>
          {canManageCollaborators ? (
            <TacticalButton
              type="button"
              onClick={() => setCollaboratorPanelOpen((prev) => !prev)}
            >
              {collaboratorPanelOpen ? "Close Invite Panel" : "Add Collaborator"}
            </TacticalButton>
          ) : (
            <span className="text-xs text-softwhite/60">Read-only collaborator access</span>
          )}
        </div>

        <div className="text-xs text-softwhite/70">
          Your role: <span className="ml-1"><HudBadge label={currentRole} tone={currentRole === "Owner" ? "alert" : currentRole === "Collaborator" ? "primary" : "support"} /></span>
        </div>

        {collaboratorPanelOpen && (
          <div className="rounded-lg border border-neoviolet/40 bg-slatewash/30 p-4 transition">
            <p className="hud-label mb-3 text-[10px]">Invite Collaborator</p>
            <div className="grid gap-3 md:grid-cols-[1fr_180px_auto]">
              <input
                className="glass-input rounded-md p-2 text-sm"
                value={collaboratorEmail}
                onChange={(event) => setCollaboratorEmail(event.target.value)}
                placeholder="engineer@onlooker.ai"
                disabled={!canManageCollaborators}
              />
              <select
                className="glass-input rounded-md p-2 text-sm"
                value={collaboratorRole}
                onChange={(event) => setCollaboratorRole(event.target.value as ProjectRole)}
                disabled={!canManageCollaborators}
              >
                <option value="Collaborator">Collaborator</option>
                <option value="Viewer">Viewer</option>
                <option value="Owner">Owner</option>
              </select>
              <TacticalButton
                type="button"
                onClick={() => void onAddCollaborator()}
                disabled={!canManageCollaborators}
              >
                Save
              </TacticalButton>
            </div>
          </div>
        )}

        {collaboratorMessage && <p className="text-sm text-lagoon">{collaboratorMessage}</p>}
        {collaboratorError && <p className="text-sm text-red-300">{collaboratorError}</p>}

        <div className="overflow-x-auto">
          <table className="min-w-full border-collapse text-sm">
            <thead>
              <tr className="neon-divider text-left text-softwhite/75">
                <th className="px-2 py-2">User</th>
                <th className="px-2 py-2">Role</th>
                <th className="px-2 py-2">Joined</th>
                <th className="px-2 py-2">Actions</th>
              </tr>
            </thead>
            <tbody>
              {collaborators.map((item) => (
                <tr key={item.user_id} className="neon-divider transition hover:bg-lagoon/10">
                  <td className="px-2 py-3">
                    <p className="font-medium text-softwhite">{item.email}</p>
                    <p className="font-mono text-xs text-softwhite/70">{item.user_id}</p>
                  </td>
                  <td className="px-2 py-3">
                    <span className={`rounded-full border px-2 py-1 font-hud text-xs transition hover:animate-hud-pulse ${roleBadgeClass(item.role)}`}>
                      {item.role}
                    </span>
                  </td>
                  <td className="px-2 py-3 text-softwhite/75">{item.joined_at ? formatDateTime(item.joined_at) : "-"}</td>
                  <td className="px-2 py-3">
                    {canManageCollaborators ? (
                      <div className="flex flex-wrap items-center gap-2">
                        <select
                          className="glass-input rounded-md px-2 py-1 text-xs"
                          value={item.role}
                          onChange={(event) => void onUpdateCollaboratorRole(item.user_id, event.target.value as ProjectRole)}
                          disabled={item.user_id === currentUserId}
                        >
                          <option value="Owner">Owner</option>
                          <option value="Collaborator">Collaborator</option>
                          <option value="Viewer">Viewer</option>
                        </select>

                        <button
                          type="button"
                          className="rounded-md border border-signal/60 bg-signal/10 px-2 py-1 text-xs text-signal disabled:opacity-40"
                          onClick={() => void onRemoveCollaborator(item.user_id)}
                          disabled={item.user_id === currentUserId}
                        >
                          Remove
                        </button>
                      </div>
                    ) : (
                      <span className="text-xs text-softwhite/60">No edit permissions</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <TableShell<ProjectSimulationSummary>
        title="Project Simulations"
        items={project?.simulations.items ?? []}
        total={project?.simulations.total ?? 0}
        page={page}
        pageSize={pageSize}
        loading={loading}
        error={error}
        emptyMessage="No simulations yet for this project and filter selection."
        filters={
          <FilterBar
            fields={filterFields}
            values={state}
            onChange={(key, value) => setQuery({ [key]: value })}
            onReset={() =>
              setQuery(
                {
                  material_id: undefined,
                  environment_id: undefined,
                  risk_level: undefined,
                  created_from: undefined,
                  created_to: undefined
                },
                { resetPage: true }
              )
            }
          />
        }
        onPageChange={(nextPage) => setQuery({ page: String(nextPage) }, { resetPage: false })}
        onPageSizeChange={(size) => setQuery({ page_size: String(size), page: "1" }, { resetPage: false })}
      >
        {(items) => (
          <>
            <div className="mb-3 flex flex-wrap items-center justify-between gap-2 text-sm">
              <p className="text-softwhite/75">Filter results for project-scoped simulation workspace actions.</p>
              <TacticalButton href="/simulations">Go to simulations to save one into this project.</TacticalButton>
            </div>

            <div className="overflow-x-auto">
              <table className="min-w-full border-collapse text-sm">
                <thead>
                  <tr className="neon-divider text-left text-softwhite/75">
                    <th className="px-2 py-2">Simulation ID</th>
                    <th className="px-2 py-2">Material</th>
                    <th className="px-2 py-2">Environment</th>
                    <th className="px-2 py-2">Risk Level</th>
                    <th className="px-2 py-2">Lifespan</th>
                    <th className="px-2 py-2">Created</th>
                    <th className="px-2 py-2">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((item) => {
                    const compareQuery = buildQueryString({
                      left_simulation_id: baseSimulationId || item.simulation_id,
                      right_simulation_id: baseSimulationId ? item.simulation_id : undefined
                    });

                    return (
                      <tr key={item.simulation_id} className="neon-divider align-top transition hover:bg-lagoon/10">
                        <td className="px-2 py-3 font-mono text-xs">{item.simulation_id}</td>
                        <td className="px-2 py-3">{item.material}</td>
                        <td className="px-2 py-3">{item.environment}</td>
                        <td className="px-2 py-3 uppercase">{item.risk_level}</td>
                        <td className="px-2 py-3">{item.lifespan_years.toFixed(1)} years</td>
                        <td className="px-2 py-3">{formatDateTime(item.created_at)}</td>
                        <td className="px-2 py-3">
                          <div className="flex flex-wrap gap-2">
                            <Link
                              href={`/simulations/${item.simulation_id}`}
                              className={`tactical-btn ${!canChangeProjectData ? "pointer-events-none opacity-50" : ""}`}
                              aria-disabled={!canChangeProjectData}
                            >
                              Open Simulation
                            </Link>
                            <Link
                              href={`/simulations/${item.simulation_id}`}
                              className={`tactical-btn ${!canChangeProjectData ? "pointer-events-none opacity-50" : ""}`}
                              aria-disabled={!canChangeProjectData}
                            >
                              Generate/View Report
                            </Link>
                            <Link
                              href={`/simulations/compare${compareQuery}`}
                              className={`tactical-btn ${!canChangeProjectData ? "pointer-events-none opacity-50" : ""}`}
                              aria-disabled={!canChangeProjectData}
                            >
                              Compare
                            </Link>
                            <Link
                              href={projectId
                                ? `/projects/${projectId}/comparison-sets${buildQueryString({ add_simulation_id: item.simulation_id })}`
                                : "/projects"
                              }
                              className={`tactical-btn ${!canChangeProjectData ? "pointer-events-none opacity-50" : ""}`}
                              aria-disabled={!canChangeProjectData}
                            >
                              Add To Comparison Set
                            </Link>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </>
        )}
      </TableShell>
    </LayoutShell>
  );
}