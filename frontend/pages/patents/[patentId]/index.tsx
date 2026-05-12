// Patent dashboard showing status, audit trail, and application information.

import { useEffect, useState } from "react";
import { useRouter } from "next/router";

interface Patent {
  id: string;
  title: string;
  abstract: string;
  status: string;
  jurisdictions: string[];
  filed_at: string | null;
  uspto_application_number: string | null;
  indian_ipo_application_number: string | null;
  claims_count: number;
  progress: number;
}

interface AuditEntry {
  timestamp: string;
  action: string;
  actor: string;
  details: Record<string, any>;
}

export default function PatentDashboard() {
  const router = useRouter();
  const { patentId } = router.query;
  const [patent, setPatent] = useState<Patent | null>(null);
  const [auditTrail, setAuditTrail] = useState<AuditEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!patentId) return;

    const fetchPatentData = async () => {
      try {
        setLoading(true);
        const [patentRes, auditRes] = await Promise.all([
          fetch(`/api/patents/${patentId}/status`),
          fetch(`/api/patents/${patentId}/audit-trail`),
        ]);

        if (!patentRes.ok || !auditRes.ok) throw new Error("Failed to load patent data");

        const patentData = await patentRes.json();
        const auditData = await auditRes.json();

        setPatent(patentData);
        setAuditTrail(auditData.audit_entries || []);
      } catch (err) {
        setError((err as Error).message);
      } finally {
        setLoading(false);
      }
    };

    fetchPatentData();
  }, [patentId]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-8 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mb-4"></div>
          <p className="text-gray-600">Loading patent...</p>
        </div>
      </div>
    );
  }

  if (error || !patent) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-8">
        <div className="max-w-4xl mx-auto">
          <button
            onClick={() => router.back()}
            className="text-blue-600 hover:text-blue-700 font-semibold text-sm mb-4"
          >
            ← Back
          </button>
          <div className="bg-red-100 border border-red-400 text-red-700 p-4 rounded">
            {error || "Patent not found"}
          </div>
        </div>
      </div>
    );
  }

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      DRAFT: "bg-yellow-100 text-yellow-800",
      READY_FOR_FILING: "bg-blue-100 text-blue-800",
      FILED: "bg-green-100 text-green-800",
      REJECTED: "bg-red-100 text-red-800",
      ABANDONED: "bg-gray-100 text-gray-800",
    };
    return colors[status] || "bg-gray-100 text-gray-800";
  };

  const getStatusLabel = (status: string) => {
    return status.replace(/_/g, " ");
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => router.push("/patents")}
            className="text-blue-600 hover:text-blue-700 font-semibold text-sm mb-4"
          >
            ← Back to Patents
          </button>
          <h1 className="text-3xl font-bold text-gray-900">{patent.title}</h1>
          <p className="text-gray-600 mt-2">Application ID: {patent.id.substring(0, 8)}</p>
        </div>

        {/* Status Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-gray-600 text-sm">Status</p>
            <div className={`mt-2 px-3 py-1 rounded-full text-xs font-semibold w-fit ${getStatusColor(patent.status)}`}>
              {getStatusLabel(patent.status)}
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-gray-600 text-sm">Claims</p>
            <p className="text-2xl font-bold text-gray-900 mt-2">{patent.claims_count}</p>
          </div>

          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-gray-600 text-sm">Jurisdictions</p>
            <p className="text-lg font-semibold text-gray-900 mt-2">{patent.jurisdictions.length}</p>
          </div>

          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-gray-600 text-sm">Completion</p>
            <p className="text-2xl font-bold text-blue-600 mt-2">{patent.progress}%</p>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="bg-white rounded-lg shadow p-6 mb-8">
          <h2 className="font-semibold text-gray-900 mb-4">Filing Progress</h2>
          <div className="space-y-4">
            {[
              { label: "Draft", completed: patent.status !== "DRAFT" },
              {
                label: "Ready for Filing",
                completed: patent.status !== "DRAFT" && patent.status !== "READY_FOR_FILING",
              },
              { label: "Filed", completed: patent.status === "FILED" },
            ].map((step, idx) => (
              <div key={idx} className="flex items-center">
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center mr-3 ${
                    step.completed
                      ? "bg-green-500 text-white"
                      : "bg-gray-300 text-gray-600"
                  }`}
                >
                  {step.completed ? "✓" : idx + 1}
                </div>
                <span className="text-gray-700">{step.label}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Filing Information */}
        {patent.status === "FILED" && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-6 mb-8">
            <h2 className="font-semibold text-green-900 mb-4">Filing Information</h2>
            <div className="grid gap-4">
              {patent.uspto_application_number && (
                <div className="flex justify-between">
                  <span className="text-green-800">USPTO Application Number</span>
                  <span className="font-mono font-semibold text-green-900">
                    {patent.uspto_application_number}
                  </span>
                </div>
              )}
              {patent.indian_ipo_application_number && (
                <div className="flex justify-between">
                  <span className="text-green-800">Indian IPO Application Number</span>
                  <span className="font-mono font-semibold text-green-900">
                    {patent.indian_ipo_application_number}
                  </span>
                </div>
              )}
              {patent.filed_at && (
                <div className="flex justify-between">
                  <span className="text-green-800">Filed Date</span>
                  <span className="font-semibold text-green-900">
                    {new Date(patent.filed_at).toLocaleDateString()}
                  </span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Abstract */}
        <div className="bg-white rounded-lg shadow p-6 mb-8">
          <h2 className="font-semibold text-gray-900 mb-4">Abstract</h2>
          <p className="text-gray-700 leading-relaxed">{patent.abstract}</p>
        </div>

        {/* Action Buttons */}
        {patent.status === "DRAFT" && (
          <div className="bg-white rounded-lg shadow p-6 mb-8">
            <h2 className="font-semibold text-gray-900 mb-4">Next Steps</h2>
            <button
              onClick={() => router.push(`/patents/${patent.id}/submit`)}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 rounded-lg"
            >
              → Submit for Filing
            </button>
          </div>
        )}

        {/* Audit Trail */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="font-semibold text-gray-900 mb-4">Audit Trail</h2>
          <div className="space-y-4">
            {auditTrail.length === 0 ? (
              <p className="text-gray-600 text-sm">No audit entries yet</p>
            ) : (
              auditTrail.map((entry, idx) => (
                <div
                  key={idx}
                  className="flex gap-4 pb-4 border-b border-gray-200 last:border-b-0"
                >
                  <div className="flex-shrink-0">
                    <div className="w-2 h-2 rounded-full bg-blue-600 mt-2"></div>
                  </div>
                  <div className="flex-grow">
                    <div className="flex justify-between items-start">
                      <div>
                        <p className="font-semibold text-gray-900">{entry.action}</p>
                        <p className="text-sm text-gray-600">by {entry.actor}</p>
                      </div>
                      <time className="text-sm text-gray-500">
                        {new Date(entry.timestamp).toLocaleDateString()} at{" "}
                        {new Date(entry.timestamp).toLocaleTimeString()}
                      </time>
                    </div>
                    {entry.details && Object.keys(entry.details).length > 0 && (
                      <p className="text-xs text-gray-600 mt-2">
                        {JSON.stringify(entry.details)}
                      </p>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="mt-8 text-center text-sm text-gray-600">
          <p>Patent Data Encrypted • Audit Trail Recorded • Secure Filing</p>
        </div>
      </div>
    </div>
  );
}
