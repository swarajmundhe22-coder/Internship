// Patent creation and filing workflow page.

import { useState } from "react";
import { useRouter } from "next/router";

interface PatentFormData {
  title: string;
  abstract: string;
  technicalField: string;
  embodiments: string[];
  claimsSummary: string;
}

export default function PatentFilingPage() {
  const router = useRouter();
  const [step, setStep] = useState<"basic" | "embodiments" | "claims" | "review">("basic");
  const [loading, setLoading] = useState(false);
  const [patentId, setPatentId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [formData, setFormData] = useState<PatentFormData>({
    title: "",
    abstract: "",
    technicalField: "",
    embodiments: [""],
    claimsSummary: "",
  });

  // Step 1: Create initial patent
  const handleCreatePatent = async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch("/api/patents/create", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: formData.title,
          abstract: formData.abstract,
          technical_field: formData.technicalField,
        }),
      });

      if (!response.ok) throw new Error("Failed to create patent");

      const patent = await response.json();
      setPatentId(patent.id);
      setStep("embodiments");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  // Step 2: Add embodiments
  const handleAddEmbodiments = async () => {
    if (!patentId) return;
    setLoading(true);
    setError(null);

    try {
      const embodiments = formData.embodiments.filter((e) => e.trim().length > 0);
      if (embodiments.length === 0) throw new Error("At least one embodiment required");

      const response = await fetch(`/api/patents/${patentId}/embodiments`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ embodiments }),
      });

      if (!response.ok) throw new Error("Failed to add embodiments");

      setStep("claims");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  // Step 3: Set claims
  const handleSetClaims = async () => {
    if (!patentId) return;
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/patents/${patentId}/claims`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ claims_summary: formData.claimsSummary }),
      });

      if (!response.ok) throw new Error("Failed to set claims");

      setStep("review");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  // Progress indicator
  const getProgress = () => {
    const steps = ["basic", "embodiments", "claims", "review"];
    return ((steps.indexOf(step) + 1) / steps.length) * 100;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-8">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900">Patent Filing Platform</h1>
          <p className="text-gray-600 mt-2">Phase 0 MVP - Mechanical Patents (US & India)</p>
        </div>

        {/* Progress bar */}
        <div className="mb-8">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>Step {["basic", "embodiments", "claims", "review"].indexOf(step) + 1} of 4</span>
            <span>{Math.round(getProgress())}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-lg h-2 overflow-hidden">
            <div
              className="bg-blue-600 h-full transition-all duration-300"
              style={{ width: `${getProgress()}%` }}
            />
          </div>
        </div>

        {/* Error message */}
        {error && (
          <div className="mb-6 p-4 bg-red-100 border border-red-400 text-red-700 rounded">
            {error}
          </div>
        )}

        {/* Form */}
        <div className="bg-white rounded-lg shadow-lg p-8">
          {/* Step 1: Basic Information */}
          {step === "basic" && (
            <div className="space-y-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">
                Step 1: Patent Basics
              </h2>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Patent Title *
                </label>
                <input
                  type="text"
                  maxLength={500}
                  placeholder="e.g., Novel Corrosion-Resistant Coating Method"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={formData.title}
                  onChange={(e) =>
                    setFormData({ ...formData, title: e.target.value })
                  }
                />
                <p className="text-xs text-gray-500 mt-1">
                  {formData.title.length}/500 characters
                </p>
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Abstract *
                </label>
                <textarea
                  maxLength={5000}
                  placeholder="Brief description of the invention..."
                  rows={4}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={formData.abstract}
                  onChange={(e) =>
                    setFormData({ ...formData, abstract: e.target.value })
                  }
                />
                <p className="text-xs text-gray-500 mt-1">
                  {formData.abstract.length}/5000 characters
                </p>
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Technical Field *
                </label>
                <input
                  type="text"
                  placeholder="e.g., Materials Science, Electrochemistry, Mechanical Engineering"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={formData.technicalField}
                  onChange={(e) =>
                    setFormData({ ...formData, technicalField: e.target.value })
                  }
                />
              </div>

              <button
                onClick={handleCreatePatent}
                disabled={!formData.title || !formData.abstract || !formData.technicalField || loading}
                className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold py-3 rounded-lg transition"
              >
                {loading ? "Creating..." : "Continue to Embodiments"}
              </button>
            </div>
          )}

          {/* Step 2: Technical Embodiments */}
          {step === "embodiments" && (
            <div className="space-y-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">
                Step 2: Technical Embodiments
              </h2>
              <p className="text-gray-600">
                List key technical features and variations of your invention.
              </p>

              {formData.embodiments.map((embodiment, idx) => (
                <div key={idx}>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    Embodiment {idx + 1}
                  </label>
                  <input
                    type="text"
                    placeholder={`e.g., Using stainless steel 316L for corrosion resistance`}
                    maxLength={500}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    value={embodiment}
                    onChange={(e) => {
                      const newEmbodiments = [...formData.embodiments];
                      newEmbodiments[idx] = e.target.value;
                      setFormData({ ...formData, embodiments: newEmbodiments });
                    }}
                  />
                </div>
              ))}

              <button
                onClick={() =>
                  setFormData({
                    ...formData,
                    embodiments: [...formData.embodiments, ""],
                  })
                }
                className="text-blue-600 hover:text-blue-700 font-semibold text-sm"
              >
                + Add Another Embodiment
              </button>

              <div className="flex gap-4 pt-4">
                <button
                  onClick={() => setStep("basic")}
                  className="flex-1 border border-gray-300 text-gray-700 font-semibold py-3 rounded-lg hover:bg-gray-50"
                >
                  Back
                </button>
                <button
                  onClick={handleAddEmbodiments}
                  disabled={!formData.embodiments.some((e) => e.trim().length > 0) || loading}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold py-3 rounded-lg"
                >
                  {loading ? "Saving..." : "Continue to Claims"}
                </button>
              </div>
            </div>
          )}

          {/* Step 3: Claims */}
          {step === "claims" && (
            <div className="space-y-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">
                Step 3: Patent Claims
              </h2>
              <p className="text-gray-600">
                Define the scope of your patent claims. A basic claim template will be generated
                from your embodiments.
              </p>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Claims Summary *
                </label>
                <textarea
                  maxLength={2000}
                  placeholder="Describe what specific claims you want to protect..."
                  rows={6}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={formData.claimsSummary}
                  onChange={(e) =>
                    setFormData({ ...formData, claimsSummary: e.target.value })
                  }
                />
                <p className="text-xs text-gray-500 mt-1">
                  {formData.claimsSummary.length}/2000 characters
                </p>
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded p-4">
                <p className="text-sm text-blue-900">
                  <strong>Note:</strong> The initial claim will be reviewed by a patent attorney
                  before filing. We'll generate dependent claims from your embodiments.
                </p>
              </div>

              <div className="flex gap-4 pt-4">
                <button
                  onClick={() => setStep("embodiments")}
                  className="flex-1 border border-gray-300 text-gray-700 font-semibold py-3 rounded-lg hover:bg-gray-50"
                >
                  Back
                </button>
                <button
                  onClick={handleSetClaims}
                  disabled={!formData.claimsSummary || formData.claimsSummary.length < 20 || loading}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold py-3 rounded-lg"
                >
                  {loading ? "Saving..." : "Review & File"}
                </button>
              </div>
            </div>
          )}

          {/* Step 4: Review & File */}
          {step === "review" && patentId && (
            <div className="space-y-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">
                Step 4: Review & Submit for Filing
              </h2>

              <div className="bg-green-50 border border-green-200 rounded p-4 mb-6">
                <p className="text-green-900">
                  ✓ Patent drafted and ready for filing
                </p>
              </div>

              <div className="space-y-4 bg-gray-50 p-4 rounded">
                <h3 className="font-semibold text-gray-900">Patent Summary</h3>
                <div className="grid gap-4 text-sm">
                  <div>
                    <p className="text-gray-600">Title</p>
                    <p className="font-semibold text-gray-900">{formData.title}</p>
                  </div>
                  <div>
                    <p className="text-gray-600">Technical Field</p>
                    <p className="font-semibold text-gray-900">{formData.technicalField}</p>
                  </div>
                  <div>
                    <p className="text-gray-600">Embodiments</p>
                    <p className="font-semibold text-gray-900">
                      {formData.embodiments.filter((e) => e.trim()).length} defined
                    </p>
                  </div>
                </div>
              </div>

              <div className="bg-yellow-50 border border-yellow-200 rounded p-4">
                <p className="text-sm text-yellow-900">
                  <strong>Next Steps:</strong>
                  <ol className="list-decimal list-inside mt-2 space-y-1">
                    <li>Review the generated filing XML with a patent attorney</li>
                    <li>Select jurisdiction (USA/India)</li>
                    <li>Provide applicant information</li>
                    <li>Submit to USPTO or Indian Patent Office</li>
                  </ol>
                </p>
              </div>

              <button
                onClick={() => router.push(`/patents/${patentId}/submit`)}
                className="w-full bg-green-600 hover:bg-green-700 text-white font-semibold py-3 rounded-lg flex items-center justify-center gap-2"
              >
                <span>→</span> Continue to Filing Submission
              </button>

              <button
                onClick={() => router.push(`/patents/${patentId}`)}
                className="w-full border border-gray-300 text-gray-700 font-semibold py-3 rounded-lg hover:bg-gray-50"
              >
                View Patent Dashboard
              </button>
            </div>
          )}
        </div>

        {/* Footer info */}
        <div className="mt-8 text-center text-sm text-gray-600">
          <p>Phase 0 MVP • Mechanical Patents • Secure Filing</p>
          <p className="mt-2">
            Your patent data is encrypted at rest and access is fully audited.
          </p>
        </div>
      </div>
    </div>
  );
}
