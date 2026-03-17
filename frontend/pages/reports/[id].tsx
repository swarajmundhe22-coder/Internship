import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/router";

import { ChapterHeader, HudBadge, TacticalButton, TelemetryCard } from "../../components/CinematicHud";
import { LayoutShell } from "../../components/LayoutShell";
import { useApi } from "../../hooks/useApi";
import { ApiError, ReportRecord } from "../../types/domain";

type ReportFormState = {
  status: string;
  report_uri: string;
};

export default function ReportDetailPage() {
  const router = useRouter();
  const { id } = router.query;
  const { run } = useApi();

  const [report, setReport] = useState<ReportRecord | null>(null);
  const [form, setForm] = useState<ReportFormState | null>(null);
  const [latest, setLatest] = useState<ReportRecord | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [conflict, setConflict] = useState<string | null>(null);
  const [showDiff, setShowDiff] = useState(false);

  async function fetchReport() {
    if (!id || typeof id !== "string") {
      return;
    }

    const data = await run<ReportRecord>(`/reports/${id}`);
    setReport(data);
    setForm({ status: data.status, report_uri: data.report_uri });
  }

  useEffect(() => {
    void fetchReport();
  }, [id]);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!report || !form || !id || typeof id !== "string") {
      return;
    }

    setMessage(null);
    setConflict(null);
    setShowDiff(false);

    try {
      const updated = await run<ReportRecord>(`/reports/${id}`, {
        method: "PUT",
        body: JSON.stringify({
          expected_version: report.version,
          status: form.status,
          report_uri: form.report_uri
        })
      });

      setReport(updated);
      setForm({ status: updated.status, report_uri: updated.report_uri });
      setLatest(null);
      setMessage("Report updated successfully.");
    } catch (err) {
      const apiError = err as ApiError;
      if (apiError.kind === "concurrency") {
        const fresh = await run<ReportRecord>(`/reports/${id}`);
        setLatest(fresh);
        setConflict("This report was modified by another process. Reload latest data or compare your edits.");
      }
    }
  }

  return (
    <LayoutShell title="Report Detail" subtitle="Edit report metadata with optimistic concurrency protection.">
      {!report || !form ? (
        <section className="panel p-6 type-body text-softwhite/70">Loading report...</section>
      ) : (
        <div className="grid gap-4 lg:grid-cols-2">
          <form className="panel grid gap-3 p-6" onSubmit={onSubmit}>
            <ChapterHeader eyebrow="Report Editor" title="Edit Report" />
            <div><HudBadge label={`Version: ${report.version}`} tone="support" /></div>

            <label className="grid gap-1 text-sm text-softwhite/85">
              Status
              <input
                className="glass-input rounded-md p-2"
                value={form.status}
                onChange={(event) => setForm((prev) => (prev ? { ...prev, status: event.target.value } : prev))}
              />
            </label>

            <label className="grid gap-1 text-sm text-softwhite/85">
              Report URI
              <input
                className="glass-input rounded-md p-2"
                value={form.report_uri}
                onChange={(event) => setForm((prev) => (prev ? { ...prev, report_uri: event.target.value } : prev))}
              />
            </label>

            <TacticalButton type="submit">Save Changes</TacticalButton>
            {message && <p className="text-sm text-lagoon">{message}</p>}
          </form>

          <section className="panel p-6">
            <ChapterHeader eyebrow="Consistency" title="Concurrency Status" />
            {!conflict && <p className="mt-2 type-body text-softwhite/70">No conflict detected for this record.</p>}
            {conflict && (
              <div className="mt-2 grid gap-3">
                <p className="text-sm text-red-600">{conflict}</p>
                <div className="flex gap-2">
                  <TacticalButton type="button" tone="support" onClick={() => void fetchReport()}>Reload Latest Data</TacticalButton>
                  <TacticalButton type="button" tone="alert" onClick={() => setShowDiff((prev) => !prev)}>View Diff</TacticalButton>
                </div>

                {showDiff && latest && (
                  <div className="hud-grid md:grid-cols-2">
                    <TelemetryCard label="Status" value={`you: ${form.status} | latest: ${latest.status}`} tone="alert" />
                    <TelemetryCard label="Report URI" value={`you: ${form.report_uri} | latest: ${latest.report_uri}`} tone="support" />
                  </div>
                )}
              </div>
            )}
          </section>
        </div>
      )}
    </LayoutShell>
  );
}
