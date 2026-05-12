// Patent filing submission page for USPTO and Indian IPO.

import { useState } from "react";
import { useRouter } from "next/router";

interface FilingFormData {
  jurisdiction: "USPTO" | "INDIAN_IPO";
  applicantName: string;
  applicantAddress: string;
  applicantCity: string;
  applicantState: string;
  applicantZip: string;
}

interface FilingPreview {
  application_id: string;
  title: string;
  abstract: string;
  applicant: string;
  claims_count: number;
  filing_fee: number;
  estimated_processing_time_months?: number;
  jurisdiction?: string;
}

export default function PatentSubmitPage() {
  const router = useRouter();
  const { patentId } = router.query;
  const [step, setStep] = useState<"jurisdiction" | "applicant" | "preview" | "confirmation">("jurisdiction");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [preview, setPreview] = useState<FilingPreview | null>(null);
  const [applicationNumber, setApplicationNumber] = useState<string | null>(null);

  const [formData, setFormData] = useState<FilingFormData>({
    jurisdiction: "USPTO",
    applicantName: "",
    applicantAddress: "",
    applicantCity: "",
    applicantState: "",
    applicantZip: "",
  });

  // Get filing preview
  const handleGetPreview = async () => {
    if (!patentId) return;
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `/api/patents/${patentId}/filing-preview?jurisdiction=${formData.jurisdiction}&applicant_name=${encodeURIComponent(formData.applicantName)}`
      );

      if (!response.ok) throw new Error("Failed to generate preview");

      const data = await response.json();
      setPreview(data);
      setStep("preview");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  // Submit for filing
  const handleSubmitForFiling = async () => {
    if (!patentId) return;
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/patents/${patentId}/submit-for-filing`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          jurisdiction: formData.jurisdiction,
          applicant_name: formData.applicantName,
          applicant_address: formData.applicantAddress,
          applicant_city: formData.applicantCity,
          applicant_state: formData.applicantState,
          applicant_zip: formData.applicantZip,
        }),
      });

      if (!response.ok) throw new Error("Failed to submit for filing");

      const data = await response.json();
      setApplicationNumber(data.application_number || "PENDING");
      setStep("confirmation");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-8">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => router.back()}
            className="text-blue-600 hover:text-blue-700 font-semibold text-sm mb-4"
          >
            ← Back
          </button>
          <h1 className="text-3xl font-bold text-gray-900">Submit Patent for Filing</h1>
          <p className="text-gray-600 mt-2">Select jurisdiction and provide applicant information</p>
        </div>

        {/* Error message */}
        {error && (
          <div className="mb-6 p-4 bg-red-100 border border-red-400 text-red-700 rounded">
            {error}
          </div>
        )}

        <div className="bg-white rounded-lg shadow-lg p-8">
          {/* Step 1: Select Jurisdiction */}
          {step === "jurisdiction" && (
            <div className="space-y-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">
                Step 1: Select Jurisdiction
              </h2>

              <div className="grid gap-4">
                {[
                  {
                    value: "USPTO",
                    label: "United States Patent & Trademark Office (USPTO)",
                    fee: "$330 USD",
                    processingTime: "18-24 months",
                  },
                  {
                    value: "INDIAN_IPO",
                    label: "Indian Patent Office (IPO)",
                    fee: "₹1,600 INR",
                    processingTime: "18-24 months",
                  },
                ].map((option) => (
                  <div
                    key={option.value}
                    onClick={() =>
                      setFormData({
                        ...formData,
                        jurisdiction: option.value as "USPTO" | "INDIAN_IPO",
                      })
                    }
                    className={`p-4 border rounded-lg cursor-pointer transition ${
                      formData.jurisdiction === option.value
                        ? "border-blue-500 bg-blue-50"
                        : "border-gray-300 hover:border-blue-300"
                    }`}
                  >
                    <div className="flex items-center">
                      <input
                        type="radio"
                        name="jurisdiction"
                        value={option.value}
                        checked={formData.jurisdiction === option.value}
                        onChange={() => {}}
                        className="w-4 h-4 text-blue-600"
                      />
                      <div className="ml-4">
                        <p className="font-semibold text-gray-900">{option.label}</p>
                        <p className="text-sm text-gray-600 mt-1">
                          Filing Fee: {option.fee} • Processing: {option.processingTime}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>

              <button
                onClick={() => setStep("applicant")}
                className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 rounded-lg"
              >
                Continue to Applicant Information
              </button>
            </div>
          )}

          {/* Step 2: Applicant Information */}
          {step === "applicant" && (
            <div className="space-y-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">
                Step 2: Applicant Information
              </h2>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Full Name (Inventor/Applicant) *
                </label>
                <input
                  type="text"
                  placeholder="John Doe"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={formData.applicantName}
                  onChange={(e) =>
                    setFormData({ ...formData, applicantName: e.target.value })
                  }
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Street Address *
                </label>
                <input
                  type="text"
                  placeholder="123 Main Street"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={formData.applicantAddress}
                  onChange={(e) =>
                    setFormData({ ...formData, applicantAddress: e.target.value })
                  }
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    City *
                  </label>
                  <input
                    type="text"
                    placeholder="San Francisco"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    value={formData.applicantCity}
                    onChange={(e) =>
                      setFormData({ ...formData, applicantCity: e.target.value })
                    }
                  />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">
                    State/Province *
                  </label>
                  <input
                    type="text"
                    placeholder="CA"
                    maxLength={2}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    value={formData.applicantState}
                    onChange={(e) =>
                      setFormData({
                        ...formData,
                        applicantState: e.target.value.toUpperCase(),
                      })
                    }
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  ZIP/Postal Code *
                </label>
                <input
                  type="text"
                  placeholder="94105"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={formData.applicantZip}
                  onChange={(e) =>
                    setFormData({ ...formData, applicantZip: e.target.value })
                  }
                />
              </div>

              <div className="flex gap-4 pt-4">
                <button
                  onClick={() => setStep("jurisdiction")}
                  className="flex-1 border border-gray-300 text-gray-700 font-semibold py-3 rounded-lg hover:bg-gray-50"
                >
                  Back
                </button>
                <button
                  onClick={handleGetPreview}
                  disabled={
                    !formData.applicantName ||
                    !formData.applicantAddress ||
                    !formData.applicantCity ||
                    !formData.applicantState ||
                    !formData.applicantZip ||
                    loading
                  }
                  className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-semibold py-3 rounded-lg"
                >
                  {loading ? "Generating Preview..." : "Generate Filing Preview"}
                </button>
              </div>
            </div>
          )}

          {/* Step 3: Preview Filing */}
          {step === "preview" && preview && (
            <div className="space-y-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">
                Step 3: Review Filing Details
              </h2>

              <div className="bg-gray-50 p-6 rounded-lg space-y-4">
                <h3 className="font-semibold text-lg text-gray-900">Filing Summary</h3>

                <div className="grid gap-4 text-sm">
                  <div className="flex justify-between border-b border-gray-200 pb-2">
                    <span className="text-gray-600">Application ID</span>
                    <span className="font-semibold text-gray-900">{preview.application_id}</span>
                  </div>
                  <div className="flex justify-between border-b border-gray-200 pb-2">
                    <span className="text-gray-600">Title</span>
                    <span className="font-semibold text-gray-900 text-right">{preview.title}</span>
                  </div>
                  <div className="flex justify-between border-b border-gray-200 pb-2">
                    <span className="text-gray-600">Applicant</span>
                    <span className="font-semibold text-gray-900">{preview.applicant}</span>
                  </div>
                  <div className="flex justify-between border-b border-gray-200 pb-2">
                    <span className="text-gray-600">Claims Count</span>
                    <span className="font-semibold text-gray-900">{preview.claims_count}</span>
                  </div>
                  <div className="flex justify-between border-b border-gray-200 pb-2">
                    <span className="text-gray-600">Jurisdiction</span>
                    <span className="font-semibold text-gray-900">
                      {formData.jurisdiction === "USPTO" ? "United States" : "India"}
                    </span>
                  </div>
                  <div className="flex justify-between border-b border-gray-200 pb-2">
                    <span className="text-gray-600 font-semibold">Filing Fee</span>
                    <span className="font-bold text-gray-900">${preview.filing_fee}</span>
                  </div>
                </div>
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded p-4">
                <p className="text-sm text-blue-900">
                  <strong>Important:</strong> Before proceeding, ensure all information is correct.
                  This filing is final and will be submitted to the{" "}
                  {formData.jurisdiction === "USPTO"
                    ? "USPTO"
                    : "Indian Patent Office"}{" "}
                  for examination.
                </p>
              </div>

              <div className="flex gap-4 pt-4">
                <button
                  onClick={() => setStep("applicant")}
                  className="flex-1 border border-gray-300 text-gray-700 font-semibold py-3 rounded-lg hover:bg-gray-50"
                >
                  Back
                </button>
                <button
                  onClick={handleSubmitForFiling}
                  disabled={loading}
                  className="flex-1 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white font-semibold py-3 rounded-lg"
                >
                  {loading ? "Submitting..." : "Submit Filing"}
                </button>
              </div>
            </div>
          )}

          {/* Step 4: Confirmation */}
          {step === "confirmation" && (
            <div className="space-y-6 text-center">
              <div className="text-green-600 text-6xl mb-4">✓</div>
              <h2 className="text-2xl font-bold text-gray-900">
                Patent Submitted Successfully
              </h2>

              <div className="bg-green-50 border border-green-200 rounded-lg p-6">
                <p className="text-green-900 font-semibold">
                  Your patent application has been submitted to the{" "}
                  {formData.jurisdiction === "USPTO"
                    ? "USPTO"
                    : "Indian Patent Office"}.
                </p>
                {applicationNumber && (
                  <p className="text-green-800 mt-2">
                    Application Reference: <strong>{applicationNumber}</strong>
                  </p>
                )}
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded p-4">
                <p className="text-sm text-blue-900">
                  <strong>Next Steps:</strong>
                  <ol className="list-decimal list-inside mt-2 space-y-1 text-left">
                    <li>You will receive a filing receipt via email</li>
                    <li>Patent examination will begin in 18-24 months</li>
                    <li>You can track status in your dashboard</li>
                    <li>Correspond with the patent office through our platform</li>
                  </ol>
                </p>
              </div>

              <div className="flex gap-4 pt-4">
                <button
                  onClick={() => router.push(`/patents/${patentId}`)}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 rounded-lg"
                >
                  View Patent Dashboard
                </button>
                <button
                  onClick={() => router.push("/patents")}
                  className="flex-1 border border-gray-300 text-gray-700 font-semibold py-3 rounded-lg hover:bg-gray-50"
                >
                  My Patents
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
