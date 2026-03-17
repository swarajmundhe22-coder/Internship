import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";

import { ChapterHeader, TacticalButton, TelemetryCard } from "../components/CinematicHud";
import { LayoutShell } from "../components/LayoutShell";
import { useApi } from "../hooks/useApi";
import { Project } from "../types/domain";

export default function ProjectsPage() {
  const { run, loading, error } = useApi();
  const [projects, setProjects] = useState<Project[]>([]);
  const [name, setName] = useState("");
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    void loadProjects();
  }, []);

  async function loadProjects() {
    try {
      const data = await run<Project[]>("/projects");
      setProjects(data);
      setMessage(null);
    } catch {
      setMessage("Login required to access projects.");
    }
  }

  async function createProject(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!name.trim()) {
      return;
    }
    const created = await run<Project>("/projects", {
      method: "POST",
      body: JSON.stringify({ name })
    });
    setProjects((prev) => [created, ...prev]);
    setName("");
    setMessage("Project created.");
  }

  return (
    <LayoutShell
      title="Project Workspace"
      subtitle="Persist simulation scenarios into projects and maintain engineering context over time."
    >
      <section className="panel mb-6 p-6">
        <ChapterHeader eyebrow="Workspace Module" title="Create Project" />
        <form className="grid gap-3 md:grid-cols-[1fr_auto]" onSubmit={(event) => void createProject(event)}>
          <input
            className="glass-input rounded-md p-2 text-sm"
            placeholder="Project name"
            value={name}
            onChange={(event) => setName(event.target.value)}
            minLength={2}
            maxLength={120}
          />
          <TacticalButton type="submit" tone="support" disabled={loading}>
            {loading ? "Saving..." : "Create Project"}
          </TacticalButton>
        </form>
        {error && <p className="mt-3 text-sm text-red-300">{error}</p>}
        {message && <p className="mt-3 text-sm text-softwhite/75">{message}</p>}
      </section>

      <section className="panel p-6">
        <ChapterHeader eyebrow="Workspace" title="Your Projects" />
        {projects.length === 0 ? (
          <p className="mt-3 text-sm text-softwhite/70">
            No projects available. <Link className="text-lagoon underline" href="/auth/login">Sign in</Link> or create one above.
          </p>
        ) : (
          <ul className="mt-3 grid gap-3">
            {projects.map((project) => (
              <li key={project.id} className="rounded-lg border border-lagoon/30 bg-slatewash/35 p-3 text-sm">
                <div className="flex flex-wrap items-start justify-between gap-2">
                  <div>
                    <TelemetryCard label={project.name} value={`ID: ${project.id}`} tone="primary" />
                  </div>
                  <TacticalButton href={`/projects/${project.id}`}>View Workspace</TacticalButton>
                </div>
              </li>
            ))}
          </ul>
        )}
      </section>
    </LayoutShell>
  );
}
