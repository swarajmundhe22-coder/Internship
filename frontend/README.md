# The On Looker Frontend

Next.js + Tailwind + Three.js frontend starter for The On Looker platform.

## Run

```bash
npm install
npm run dev
```

## Pages

- `/` cinematic landing and demo entry page
- `/dashboard` analytics dashboard
- `/materials` materials management
- `/environments` environment profiles
- `/simulations` simulation controls, result panel, and list
- `/simulations/[id]` simulation detail with 3D visualization
- `/simulations/compare` side-by-side scenario delta view
- `/reports` report list with filters and pagination
- `/reports/[id]` report edit with optimistic-lock conflict handling
- `/projects` project list and creation
- `/projects/[id]` project workspace showing saved simulations and actions
- `/projects/[id]/reports` project-level report collection with filters and pagination
- `/projects/[id]/activity` project activity timeline with URL-synced filters
- `/projects/[id]/comparison-sets` project comparison set creation, listing, and quick compare launch
- `/projects/[id]/insights` AI insight HUD and report export

## List Behavior

- Materials, environments, simulations, and reports use server-side pagination.
- URL query params are source-of-truth for page, page size, and filters.
- Refresh and share preserve list state.

## Concurrency UX

- Simulation and report edit pages submit `expected_version` during updates.
- On stale version conflict, UI provides:
	- reload latest record
	- simple diff view between user edits and latest persisted values

## Notes

- Configure backend endpoint via `NEXT_PUBLIC_API_BASE_URL`.
- Configure Firebase project credentials in `components/outsource/local-simulated/firebase-applet-config.json`.
- Three.js panel currently renders a corrosion-intensity mapped structure placeholder.

## Social Login Setup

- Google social login uses Firebase popup sign-in first, then exchanges identity through backend `POST /api/v1/auth/sso/exchange`.
- In Firebase Console, enable Google provider and add authorized domains for each environment (including localhost and deployed hostnames).
- Keep `NEXT_PUBLIC_ENABLE_LOCAL_SOCIAL_FALLBACK=false` for real OAuth behavior. Set it to `true` only when you intentionally want synthetic local fallback tokens.

## Cinematic Design System

- Global visual language uses industrial holographic styling: dark gradient canvases, neon accent tokens, and glassmorphism panels.
- Shared shell and controls (`LayoutShell`, `FilterBar`, `TableShell`, `PaginationControls`) are themed with HUD typography and glow/scanline effects.
- Dashboard and timeline surfaces include animated ambient layers to simulate command-center depth.

## Project Workspaces

- Each project has a dedicated detail page showing saved simulation records.
- Workspace includes collaborator management with role badges and owner-only access controls.
- Roles currently surfaced in UI are `Owner`, `Collaborator`, and `Viewer`.
- Simulation row actions:
	- Open simulation detail
	- Generate or view report from simulation workflow
	- Jump into compare flow with prefilled simulation IDs
- Project reports hub includes `Open Report`, `Download HTML`, and working `Download PDF` actions.
- `ReportViewer` also supports direct PDF export with loading and error feedback by resolving the report record and calling backend PDF endpoints.
- If a project has no simulations, UI provides a CTA linking to `/simulations` to save one into the project.

## Dashboard Analytics

- Dashboard now surfaces aggregate analytics cards for simulation, report, and high-risk counts.
- Inline visual panels render:
	- simulations-over-time trend bars
	- risk distribution bars by risk level
	- top material and environment usage distributions

## Comparison Sets

- Project workspace rows include an `Add To Comparison Set` action.
- Comparison sets page supports:
	- selecting 2-4 project simulations
	- saving named comparison sets
	- opening compare-ready set payloads
	- deleting stale sets
- Compare workspace supports `set_id` query mode for loading saved set comparisons directly.

## Phase 6 Cinematic Playback

- Simulation detail now includes predictive playback controls tied to project-scoped predictions.
- Playback workflow on `/simulations/[id]`:
	- save simulation to a project
	- generate predictive playback frames
	- play, pause, reset, and scrub forecast timeline
- Holographic playback panel includes:
	- animated risk progression badges and timeline nodes
	- glow/pulse transitions during active playback
	- Three.js intensity updates per forecast frame

## Phase 6 Advanced Comparison Visuals

- Compare panel now renders side-by-side holographic records for selected left/right simulations.
- Delta channels include animated bars and glow-coded metric shifts for risk/lifespan/environment/material changes.
- Export controls support:
	- `Export PDF Snapshot` (structured comparison summary)
	- `Export Playback Video` (animated WebM delta playback)

## Phase 6 AI Insights Workspace

- Project workspace now links directly to an `Open AI Insights` tab.
- Insights page provides:
	- AI-generated risk summary
	- recommendations panel
	- anomaly detection cards
- `Export Insights Report` downloads a report-friendly text artifact from backend insights services.
