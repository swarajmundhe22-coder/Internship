import { FormEvent, useState } from "react";

import { ChapterHeader, HudBadge, TacticalButton, TelemetryCard } from "../../components/CinematicHud";
import { CinematicScene } from "../../components/CinematicScene";
import { LayoutShell } from "../../components/LayoutShell";
import { TableShell } from "../../components/TableShell";
import { useApi } from "../../hooks/useApi";
import {
  ConsortiumDashboardResponse,
  ConsortiumMembershipResponse,
  DeckExportResponse,
  DossierGenerateResponse
} from "../../types/domain";

type GovernanceActionLog = {
  id: string;
  action: string;
  status: string;
  artifact_uri?: string;
  tier?: string;
  timestamp: string;
};

function nowIso(): string {
  return new Date().toISOString();
}

export default function AdminGovernancePage() {
  const { loading, error, apiError, generateDossier, exportDeck, manageConsortium, getConsortiumDashboard } = useApi();

  const [tenantId, setTenantId] = useState("");
  const [simulationId, setSimulationId] = useState("");
  const [dossierFormat, setDossierFormat] = useState<"pdf" | "json" | "xml">("pdf");
  const [industryModule, setIndustryModule] = useState("energy_grid");

  const [projectId, setProjectId] = useState("");
  const [deckExportType, setDeckExportType] = useState<"pptx" | "pdf" | "mp4">("pptx");

  const [consortiumAction, setConsortiumAction] = useState<"join" | "upgrade" | "downgrade">("join");

  const [dashboard, setDashboard] = useState<ConsortiumDashboardResponse | null>(null);
  const [actionLog, setActionLog] = useState<GovernanceActionLog[]>([]);

  function addLog(entry: GovernanceActionLog): void {
    setActionLog((current) => [entry, ...current].slice(0, 12));
  }

  async function onGenerateDossier(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const result: DossierGenerateResponse = await generateDossier({
      tenant_id: tenantId,
      simulation_id: simulationId,
      format: dossierFormat,
      industry_module: industryModule
    });
    addLog({
      id: result.dossier_id,
      action: `dossier:${result.format}`,
      status: result.status,
      artifact_uri: result.artifact_uri,
      timestamp: nowIso()
    });
  }

  async function onExportDeck(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const result: DeckExportResponse = await exportDeck({
      tenant_id: tenantId,
      project_id: projectId,
      export_type: deckExportType
    });
    addLog({
      id: result.deck_id,
      action: `deck:${result.export_type}`,
      status: result.status,
      artifact_uri: result.artifact_uri,
      timestamp: nowIso()
    });
  }

  async function onManageConsortium(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const result: ConsortiumMembershipResponse = await manageConsortium({
      tenant_id: tenantId,
      action: consortiumAction
    });
    addLog({
      id: result.id,
      action: `consortium:${consortiumAction}`,
      status: result.status,
      tier: result.tier,
      timestamp: result.updated_at
    });
  }

  async function onLoadDashboard(): Promise<void> {
    const result = await getConsortiumDashboard(tenantId);
    setDashboard(result);
  }

  const isForbidden = apiError?.status === 403;

  return (
    <LayoutShell
      title="Governance Command Surface"
      subtitle="Generate compliance dossiers, export investor decks, and control consortium membership with auditable enterprise actions."
    >
      <CinematicScene
        tone="finale"
        sceneLabel="Scene 6 / Final Act"
        narrative="You are now part of the Planetary Intelligence Order. Consortium emblems pulse as governance authority is established."
      >
        <div className="grid gap-2 text-xs text-softwhite/80 md:grid-cols-3">
          <HudBadge label="Planetary Utility Guild" tone="primary" />
          <HudBadge label="Elite Intelligence Order" tone="support" />
          <HudBadge label="Planetary Club Consortium" tone="alert" />
        </div>
      </CinematicScene>

      <section className="panel mb-6 grid gap-4 p-6 lg:grid-cols-3">
        <form className="grid gap-3 rounded-lg border border-lagoon/30 bg-slatewash/35 p-4" onSubmit={(event) => void onGenerateDossier(event)}>
          <ChapterHeader eyebrow="Governance Module" title="Dossier Generation" />
          <label className="grid gap-1 text-sm">
            Tenant ID
            <input className="glass-input rounded-md p-2" value={tenantId} onChange={(event) => setTenantId(event.target.value)} />
          </label>
          <label className="grid gap-1 text-sm">
            Simulation ID
            <input className="glass-input rounded-md p-2" value={simulationId} onChange={(event) => setSimulationId(event.target.value)} />
          </label>
          <label className="grid gap-1 text-sm">
            Format
            <select
              className="glass-input rounded-md p-2"
              value={dossierFormat}
              onChange={(event) => setDossierFormat(event.target.value as "pdf" | "json" | "xml")}
            >
              <option value="pdf">pdf</option>
              <option value="json">json</option>
              <option value="xml">xml</option>
            </select>
          </label>
          <label className="grid gap-1 text-sm">
            Industry Module
            <input className="glass-input rounded-md p-2" value={industryModule} onChange={(event) => setIndustryModule(event.target.value)} />
          </label>
          <TacticalButton type="submit">Generate Dossier</TacticalButton>
        </form>

        <form className="grid gap-3 rounded-lg border border-neoviolet/35 bg-slatewash/35 p-4" onSubmit={(event) => void onExportDeck(event)}>
          <ChapterHeader eyebrow="Investor Module" title="Investor Deck Export" />
          <label className="grid gap-1 text-sm">
            Tenant ID
            <input className="glass-input rounded-md p-2" value={tenantId} onChange={(event) => setTenantId(event.target.value)} />
          </label>
          <label className="grid gap-1 text-sm">
            Project ID
            <input className="glass-input rounded-md p-2" value={projectId} onChange={(event) => setProjectId(event.target.value)} />
          </label>
          <label className="grid gap-1 text-sm">
            Export Type
            <select
              className="glass-input rounded-md p-2"
              value={deckExportType}
              onChange={(event) => setDeckExportType(event.target.value as "pptx" | "pdf" | "mp4")}
            >
              <option value="pptx">pptx</option>
              <option value="pdf">pdf</option>
              <option value="mp4">mp4</option>
            </select>
          </label>
          <TacticalButton type="submit" tone="support">Export Deck</TacticalButton>
        </form>

        <form className="grid gap-3 rounded-lg border border-signal/35 bg-slatewash/35 p-4" onSubmit={(event) => void onManageConsortium(event)}>
          <ChapterHeader eyebrow="Consortium Module" title="Consortium Membership" />
          <label className="grid gap-1 text-sm">
            Tenant ID
            <input className="glass-input rounded-md p-2" value={tenantId} onChange={(event) => setTenantId(event.target.value)} />
          </label>
          <label className="grid gap-1 text-sm">
            Action
            <select
              className="glass-input rounded-md p-2"
              value={consortiumAction}
              onChange={(event) => setConsortiumAction(event.target.value as "join" | "upgrade" | "downgrade")}
            >
              <option value="join">join</option>
              <option value="upgrade">upgrade</option>
              <option value="downgrade">downgrade</option>
            </select>
          </label>
          <TacticalButton type="submit" tone="alert">Apply Membership Action</TacticalButton>
          <TacticalButton type="button" tone="support" onClick={() => void onLoadDashboard()}>
            Load Dashboard
          </TacticalButton>
        </form>
      </section>

      {dashboard && (
        <section className="panel mb-6 grid gap-3 p-5 text-sm md:grid-cols-4">
          <TelemetryCard label="Tier" value={dashboard.tier} tone="primary" />
          <TelemetryCard label="Compliance" value={dashboard.compliance_status} tone="support" />
          <TelemetryCard label="Foresight Index" value={dashboard.foresight_index.toFixed(2)} tone="alert" />
          <TelemetryCard label="Recent Activity" value={`Dossiers ${dashboard.active_dossiers_30d} | Decks ${dashboard.active_decks_30d}`} tone="support" />
        </section>
      )}

      <TableShell
        title="Governance Action Log"
        items={actionLog}
        total={actionLog.length}
        page={1}
        pageSize={actionLog.length || 10}
        loading={loading}
        error={isForbidden ? "Admin or engineer role required for governance manage actions." : error}
        emptyMessage="No governance actions executed in this session."
        onPageChange={() => undefined}
        onPageSizeChange={() => undefined}
      >
        {(items) => (
          <div className="overflow-x-auto rounded-lg border border-lagoon/35 bg-slatewash/30">
            <table className="min-w-full divide-y divide-softwhite/10 text-sm text-softwhite/90">
              <thead className="bg-black/20 text-left text-xs uppercase tracking-wide text-softwhite/70">
                <tr>
                  <th className="px-3 py-2">Action</th>
                  <th className="px-3 py-2">Status</th>
                  <th className="px-3 py-2">Tier</th>
                  <th className="px-3 py-2">Artifact</th>
                  <th className="px-3 py-2">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-softwhite/10">
                {items.map((item) => (
                  <tr key={item.id} className="hover:bg-white/5">
                    <td className="px-3 py-2">{item.action}</td>
                    <td className="px-3 py-2">{item.status}</td>
                    <td className="px-3 py-2">{item.tier ?? "-"}</td>
                    <td className="px-3 py-2 text-xs">{item.artifact_uri ?? "-"}</td>
                    <td className="px-3 py-2 text-xs">{new Date(item.timestamp).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </TableShell>
    </LayoutShell>
  );
}
