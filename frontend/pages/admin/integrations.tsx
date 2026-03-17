import { FormEvent, useEffect, useState } from "react";

import { FilterBar } from "../../components/FilterBar";
import { LayoutShell } from "../../components/LayoutShell";
import { TableShell } from "../../components/TableShell";
import { useApi } from "../../hooks/useApi";
import {
  ApiTokenCreateResponse,
  ApiTokenRecord,
  PaginatedResponse,
  WebhookDeliveryLogRecord,
  WebhookRecord
} from "../../types/domain";

function formatDateTime(value?: string | null): string {
  if (!value) {
    return "-";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString();
}

export default function AdminIntegrationsPage() {
  const { run, loading, error } = useApi();
  const [tokenName, setTokenName] = useState("SCADA Connector");
  const [tokenScopes, setTokenScopes] = useState("predictions:read,reports:read");
  const [latestToken, setLatestToken] = useState<ApiTokenCreateResponse | null>(null);
  const [tokens, setTokens] = useState<ApiTokenRecord[]>([]);

  const [webhookUrl, setWebhookUrl] = useState("https://example.com/hooks/report");
  const [webhooks, setWebhooks] = useState<WebhookRecord[]>([]);

  const [deliveryLogs, setDeliveryLogs] = useState<PaginatedResponse<WebhookDeliveryLogRecord>>({
    items: [],
    total: 0,
    page: 1,
    page_size: 25
  });
  const [logPage, setLogPage] = useState(1);
  const [logPageSize, setLogPageSize] = useState(25);
  const [logFilter, setLogFilter] = useState({ webhook_id: "", success: "" });

  async function loadAll() {
    const [tokenList, webhookList, logs] = await Promise.all([
      run<ApiTokenRecord[]>("/integrations/api-tokens"),
      run<WebhookRecord[]>("/integrations/webhooks"),
      run<PaginatedResponse<WebhookDeliveryLogRecord>>(
        `/integrations/webhooks/deliveries?page=${logPage}&page_size=${logPageSize}${
          logFilter.webhook_id ? `&webhook_id=${encodeURIComponent(logFilter.webhook_id)}` : ""
        }${logFilter.success ? `&success=${encodeURIComponent(logFilter.success)}` : ""}`
      )
    ]);

    setTokens(tokenList);
    setWebhooks(webhookList);
    setDeliveryLogs(logs);
  }

  useEffect(() => {
    void loadAll();
  }, [logFilter.webhook_id, logFilter.success, logPage, logPageSize]);

  async function createToken(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const payload = await run<ApiTokenCreateResponse>("/integrations/api-tokens", {
      method: "POST",
      body: JSON.stringify({
        name: tokenName,
        scopes: tokenScopes
          .split(",")
          .map((value) => value.trim())
          .filter(Boolean)
      })
    });
    setLatestToken(payload);
    await loadAll();
  }

  async function revokeToken(id: string) {
    await run(`/integrations/api-tokens/${id}`, { method: "DELETE" });
    await loadAll();
  }

  async function createWebhook(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await run<WebhookRecord>("/integrations/webhooks", {
      method: "POST",
      body: JSON.stringify({ event_type: "report.completed", target_url: webhookUrl })
    });
    await loadAll();
  }

  async function deactivateWebhook(id: string) {
    await run(`/integrations/webhooks/${id}`, { method: "DELETE" });
    await loadAll();
  }

  return (
    <LayoutShell
      title="Enterprise Integrations"
      subtitle="Manage API tokens, report webhooks, and delivery retry telemetry from a single command surface."
    >
      <section className="panel mb-6 grid gap-4 p-6 lg:grid-cols-2">
        <form className="grid gap-3 rounded-lg border border-lagoon/30 bg-slatewash/35 p-4" onSubmit={(event) => void createToken(event)}>
          <h3 className="font-hud text-sm text-softwhite">API Tokens</h3>
          <label className="grid gap-1 text-sm">
            Token Name
            <input className="glass-input rounded-md p-2" value={tokenName} onChange={(event) => setTokenName(event.target.value)} />
          </label>
          <label className="grid gap-1 text-sm">
            Scopes
            <input
              className="glass-input rounded-md p-2"
              value={tokenScopes}
              onChange={(event) => setTokenScopes(event.target.value)}
              placeholder="predictions:read,reports:read"
            />
          </label>
          <button type="submit" className="holo-btn rounded-md px-3 py-2 text-sm">Create Token</button>
          {latestToken && (
            <p className="rounded-md border border-signal/40 bg-signal/10 p-2 text-xs text-softwhite">
              Save token now: {latestToken.token}
            </p>
          )}
        </form>

        <form className="grid gap-3 rounded-lg border border-neoviolet/35 bg-slatewash/35 p-4" onSubmit={(event) => void createWebhook(event)}>
          <h3 className="font-hud text-sm text-softwhite">Report Webhooks</h3>
          <label className="grid gap-1 text-sm">
            Target URL
            <input className="glass-input rounded-md p-2" value={webhookUrl} onChange={(event) => setWebhookUrl(event.target.value)} />
          </label>
          <button type="submit" className="holo-btn rounded-md px-3 py-2 text-sm">Create Webhook</button>
        </form>
      </section>

      <TableShell
        title="API Token Registry"
        items={tokens}
        total={tokens.length}
        page={1}
        pageSize={tokens.length || 10}
        loading={loading}
        error={error}
        emptyMessage="No API tokens configured."
        onPageChange={() => undefined}
        onPageSizeChange={() => undefined}
      >
        {(items) => (
          <div className="overflow-x-auto rounded-lg border border-lagoon/30 bg-slatewash/30">
            <table className="min-w-full divide-y divide-softwhite/10 text-sm text-softwhite/90">
              <thead className="bg-black/20 text-left text-xs uppercase tracking-wide text-softwhite/70">
                <tr>
                  <th className="px-3 py-2">Name</th>
                  <th className="px-3 py-2">Prefix</th>
                  <th className="px-3 py-2">Scopes</th>
                  <th className="px-3 py-2">Status</th>
                  <th className="px-3 py-2">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-softwhite/10">
                {items.map((item) => (
                  <tr key={item.id} className="hover:bg-white/5">
                    <td className="px-3 py-2">{item.name}</td>
                    <td className="px-3 py-2 font-mono text-xs">{item.token_prefix}</td>
                    <td className="px-3 py-2">{item.scopes.join(", ") || "-"}</td>
                    <td className="px-3 py-2">{item.is_active ? "Active" : "Revoked"}</td>
                    <td className="px-3 py-2">
                      <button
                        type="button"
                        className="holo-btn rounded-md px-2 py-1 text-xs disabled:opacity-50"
                        onClick={() => void revokeToken(item.id)}
                        disabled={!item.is_active}
                      >
                        Revoke
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </TableShell>

      <TableShell
        title="Webhook Subscriptions"
        items={webhooks}
        total={webhooks.length}
        page={1}
        pageSize={webhooks.length || 10}
        loading={loading}
        error={error}
        emptyMessage="No webhook subscriptions configured."
        onPageChange={() => undefined}
        onPageSizeChange={() => undefined}
      >
        {(items) => (
          <div className="overflow-x-auto rounded-lg border border-neoviolet/35 bg-slatewash/30">
            <table className="min-w-full divide-y divide-softwhite/10 text-sm text-softwhite/90">
              <thead className="bg-black/20 text-left text-xs uppercase tracking-wide text-softwhite/70">
                <tr>
                  <th className="px-3 py-2">Event</th>
                  <th className="px-3 py-2">Target URL</th>
                  <th className="px-3 py-2">Status</th>
                  <th className="px-3 py-2">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-softwhite/10">
                {items.map((item) => (
                  <tr key={item.id} className="hover:bg-white/5">
                    <td className="px-3 py-2">{item.event_type}</td>
                    <td className="px-3 py-2 text-xs">{item.target_url}</td>
                    <td className="px-3 py-2">{item.is_active ? "Active" : "Disabled"}</td>
                    <td className="px-3 py-2">
                      <button
                        type="button"
                        className="holo-btn rounded-md px-2 py-1 text-xs disabled:opacity-50"
                        onClick={() => void deactivateWebhook(item.id)}
                        disabled={!item.is_active}
                      >
                        Disable
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </TableShell>

      <TableShell
        title="Webhook Delivery Logs"
        items={deliveryLogs.items}
        total={deliveryLogs.total}
        page={deliveryLogs.page}
        pageSize={deliveryLogs.page_size}
        loading={loading}
        error={error}
        emptyMessage="No delivery attempts recorded yet."
        filters={
          <FilterBar
            fields={[
              {
                key: "webhook_id",
                label: "Webhook",
                type: "select",
                options: webhooks.map((item) => ({ label: `${item.event_type} | ${item.id.slice(0, 8)}`, value: item.id }))
              },
              {
                key: "success",
                label: "Delivery",
                type: "select",
                options: [
                  { label: "Successful", value: "true" },
                  { label: "Failed", value: "false" }
                ]
              }
            ]}
            values={logFilter}
            onChange={(key, value) => setLogFilter((current) => ({ ...current, [key]: value ?? "" }))}
            onReset={() => {
              setLogFilter({ webhook_id: "", success: "" });
              setLogPage(1);
            }}
          />
        }
        onPageChange={(nextPage) => setLogPage(nextPage)}
        onPageSizeChange={(size) => {
          setLogPageSize(size);
          setLogPage(1);
        }}
      >
        {(items) => (
          <div className="overflow-x-auto rounded-lg border border-signal/35 bg-slatewash/30">
            <table className="min-w-full divide-y divide-softwhite/10 text-xs text-softwhite/90">
              <thead className="bg-black/20 text-left uppercase tracking-wide text-softwhite/70">
                <tr>
                  <th className="px-3 py-2">Event</th>
                  <th className="px-3 py-2">Webhook</th>
                  <th className="px-3 py-2">Attempts</th>
                  <th className="px-3 py-2">Status</th>
                  <th className="px-3 py-2">Last Attempt</th>
                  <th className="px-3 py-2">Error</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-softwhite/10">
                {items.map((item) => (
                  <tr key={item.id} className="hover:bg-white/5">
                    <td className="px-3 py-2">{item.event_type}</td>
                    <td className="px-3 py-2 font-mono">{item.webhook_subscription_id.slice(0, 8)}</td>
                    <td className="px-3 py-2">{item.attempt_count}/{item.max_attempts}</td>
                    <td className="px-3 py-2">{item.success ? "Delivered" : "Failed"}</td>
                    <td className="px-3 py-2">{formatDateTime(item.last_attempt_at)}</td>
                    <td className="px-3 py-2">{item.error_message ?? (item.http_status ? `HTTP ${item.http_status}` : "-")}</td>
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
