import { useEffect, useState } from "react";

import { FilterBar } from "../../components/FilterBar";
import { LayoutShell } from "../../components/LayoutShell";
import { TableShell } from "../../components/TableShell";
import { useApi } from "../../hooks/useApi";
import { useUrlQueryState } from "../../hooks/useUrlQueryState";
import { AuditLogRecord, PaginatedResponse } from "../../types/domain";
import { buildQueryString, toDateTimeEnd, toDateTimeStart } from "../../utils/query";

function formatDateTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString();
}

export default function AdminAuditLogsPage() {
  const { run, loading, error, apiError } = useApi();
  const { state, setQuery, isReady } = useUrlQueryState({
    page: "1",
    page_size: "25",
    event_type: "",
    user_id: "",
    user_email: "",
    created_from: "",
    created_to: ""
  });

  const [pageData, setPageData] = useState<PaginatedResponse<AuditLogRecord>>({
    items: [],
    total: 0,
    page: 1,
    page_size: 25
  });

  const page = Number(state.page) || 1;
  const pageSize = Number(state.page_size) || 25;

  useEffect(() => {
    if (!isReady) {
      return;
    }

    const query = {
      page,
      page_size: pageSize,
      event_type: state.event_type || undefined,
      user_id: state.user_id || undefined,
      user_email: state.user_email || undefined,
      created_from: toDateTimeStart(state.created_from),
      created_to: toDateTimeEnd(state.created_to)
    };

    void run<PaginatedResponse<AuditLogRecord>>(`/audit-logs${buildQueryString(query)}`).then(setPageData);
  }, [
    isReady,
    state.page,
    state.page_size,
    state.event_type,
    state.user_id,
    state.user_email,
    state.created_from,
    state.created_to
  ]);

  const isForbidden = apiError?.status === 403;

  return (
    <LayoutShell
      title="Admin Audit Logs"
      subtitle="Inspect authentication and security events with server-side filtering and paginated query controls."
    >
      <TableShell
        title="Audit Event Stream"
        items={pageData.items}
        total={pageData.total}
        page={page}
        pageSize={pageSize}
        loading={loading}
        error={isForbidden ? "Admin role required to access audit logs." : error}
        emptyMessage="No audit events found for these filters."
        filters={
          <FilterBar
            fields={[
              { key: "event_type", label: "Event Type", type: "text", placeholder: "auth_login_success" },
              { key: "user_email", label: "User Email", type: "text", placeholder: "engineer@company.com" },
              { key: "user_id", label: "User ID", type: "text", placeholder: "UUID" },
              { key: "created_from", label: "From", type: "date" },
              { key: "created_to", label: "To", type: "date" }
            ]}
            values={state}
            onChange={(key, value) => setQuery({ [key]: value })}
            onReset={() =>
              setQuery({
                event_type: undefined,
                user_email: undefined,
                user_id: undefined,
                created_from: undefined,
                created_to: undefined,
                page: "1"
              })
            }
          />
        }
        onPageChange={(nextPage) => setQuery({ page: String(nextPage) }, { resetPage: false })}
        onPageSizeChange={(size) => setQuery({ page_size: String(size), page: "1" }, { resetPage: false })}
      >
        {(items) => (
          <div className="overflow-x-auto rounded-lg border border-lagoon/35 bg-slatewash/30">
            <table className="min-w-full divide-y divide-softwhite/10 text-sm text-softwhite/90">
              <thead className="bg-black/20 text-left text-xs uppercase tracking-wide text-softwhite/70">
                <tr>
                  <th className="px-3 py-2">Timestamp</th>
                  <th className="px-3 py-2">Event</th>
                  <th className="px-3 py-2">User</th>
                  <th className="px-3 py-2">Status</th>
                  <th className="px-3 py-2">Detail</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-softwhite/10">
                {items.map((item) => (
                  <tr key={item.id} className="hover:bg-white/5">
                    <td className="px-3 py-2 text-softwhite/80">{formatDateTime(item.created_at)}</td>
                    <td className="px-3 py-2 font-hud text-[11px] uppercase tracking-wide text-lagoon">{item.event_type}</td>
                    <td className="px-3 py-2 text-xs">
                      <div>{item.user_email ?? "-"}</div>
                      <div className="font-mono text-softwhite/65">{item.user_id ?? "-"}</div>
                    </td>
                    <td className="px-3 py-2">
                      <span
                        className={`rounded-full border px-2 py-1 text-[10px] uppercase tracking-wide ${
                          item.success
                            ? "border-emerald-400/70 bg-emerald-400/10 text-emerald-300"
                            : "border-signal/70 bg-signal/10 text-signal"
                        }`}
                      >
                        {item.success ? "Success" : "Failure"}
                      </span>
                    </td>
                    <td className="px-3 py-2 text-softwhite/75">{item.detail ?? "-"}</td>
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
