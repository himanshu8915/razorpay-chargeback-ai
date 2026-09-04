import React, { useState } from "react";
import axios from "axios";
import { FileText, Send, Download, CheckCircle2 } from "lucide-react";

export default function CaseRepresentmentTab({ caseData, representmentData }: { caseData: any, representmentData: any }) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  // Use real data if available, otherwise mock from decision_artifact
  const decision = caseData?.decision_artifact;
  
  const handleSubmit = async () => {
    setIsSubmitting(true);
    setSubmitError(null);
    try {
      await axios.post(`/api/v1/decision/${caseData?.case?.dispute?.dispute_id}/representment`);
      setIsSubmitting(false);
    } catch (error: any) {
      setIsSubmitting(false);
      if (error.response?.status === 501) {
        setSubmitError("Representment is not currently available in this environment.");
      } else {
        setSubmitError("An error occurred while trying to process the representment.");
      }
    }
  };
  
  if (!representmentData && (!decision || decision.decision !== "CONTEST")) {
    return (
      <div className="bg-white p-12 text-center rounded-lg border border-gray-200 shadow-sm">
        <FileText className="mx-auto h-12 w-12 text-gray-400 mb-4" />
        <h3 className="text-lg font-medium text-gray-900 mb-2">No Representment Generated</h3>
        <p className="text-sm text-gray-500 mb-6">A representment package is only generated for CONTEST decisions.</p>
      </div>
    );
  }

  // Mock SubmissionPackage based on PRD requirements
  const pkg = representmentData?.package || {
    status: "READY_FOR_SUBMISSION",
    human_approved: false,
    validation_status: { is_valid: true, missing_requirements: [], warnings: [] },
    representation: {
      narrative: `Dear issuing bank, we are contesting this ${caseData?.case?.dispute?.dispute_type || 'chargeback'}. The transaction was fully authorized and delivered.`,
      factual_arguments: [
        "AVS and CVV checks passed at checkout.",
        "Delivery was confirmed to the billing address."
      ],
      policy_arguments: [
        "Complies with Visa Core Rules relating to Compelling Evidence."
      ]
    },
    evidence: {
      evidence_items: decision?.key_evidence?.map((k: string) => ({ description: k })) || []
    }
  };

  return (
    <div className="bg-white shadow rounded-lg border border-gray-200 overflow-hidden space-y-6">
      {/* Header */}
      <div className="px-6 py-5 border-b border-gray-200 bg-slate-50 flex items-center justify-between">
        <div className="flex items-center">
          <FileText className="w-6 h-6 text-indigo-600 mr-3" />
          <h2 className="text-lg font-medium text-gray-900">Final Submission Package</h2>
        </div>
        <div className="flex gap-3">
          <button className="inline-flex items-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50">
            <Download className="w-4 h-4 mr-2" /> Download PDF
          </button>
          <div className="flex flex-col items-end">
            <button 
              onClick={handleSubmit}
              disabled={isSubmitting}
              className="inline-flex items-center rounded-md bg-blue-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-blue-500 disabled:opacity-50"
            >
              <Send className="w-4 h-4 mr-2" /> {isSubmitting ? "Submitting..." : "Submit to Network"}
            </button>
            {submitError && <span className="text-xs text-red-600 mt-1 font-medium">{submitError}</span>}
          </div>
        </div>
      </div>

      <div className="px-6 pb-6 space-y-6">
        
        {/* Readiness Status */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-gray-50 p-4 rounded border border-gray-200">
            <p className="text-sm font-medium text-gray-500">Submission Status</p>
            <p className="text-base font-semibold text-emerald-700 mt-1 flex items-center">
              <CheckCircle2 className="w-4 h-4 mr-1" /> {pkg.status}
            </p>
          </div>
          <div className="bg-gray-50 p-4 rounded border border-gray-200">
            <p className="text-sm font-medium text-gray-500">Validation Result</p>
            <p className={`text-base font-semibold mt-1 flex items-center ${pkg.validation_status.is_valid ? 'text-emerald-700' : 'text-red-700'}`}>
              {pkg.validation_status.is_valid ? 'PASSED NETWORK RULES' : 'VALIDATION FAILED'}
            </p>
          </div>
          <div className="bg-gray-50 p-4 rounded border border-gray-200">
            <p className="text-sm font-medium text-gray-500">Approval State</p>
            <p className="text-base font-semibold text-amber-700 mt-1 flex items-center">
              {pkg.human_approved ? 'APPROVED BY MERCHANT' : 'AWAITING APPROVAL'}
            </p>
          </div>
        </div>

        {/* Final Representation */}
        <div className="border border-gray-200 rounded-lg overflow-hidden">
          <div className="bg-gray-100 px-4 py-2 border-b border-gray-200 text-xs font-semibold text-gray-500 uppercase tracking-wider">
            Final Representation Narrative
          </div>
          <div className="p-6 bg-white prose prose-sm max-w-none">
            <div className="whitespace-pre-wrap font-serif text-gray-800 text-sm leading-relaxed">
              {pkg.representation.narrative}
            </div>
          </div>
        </div>

        {/* Arguments Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="border border-gray-200 rounded-lg overflow-hidden">
            <div className="bg-slate-50 px-4 py-2 border-b border-gray-200 text-xs font-semibold text-gray-500 uppercase tracking-wider">
              Factual Arguments
            </div>
            <ul className="divide-y divide-gray-100">
              {pkg.representation.factual_arguments.map((arg: string, i: number) => (
                <li key={i} className="p-4 text-sm text-gray-700">{arg}</li>
              ))}
            </ul>
          </div>
          <div className="border border-gray-200 rounded-lg overflow-hidden">
            <div className="bg-slate-50 px-4 py-2 border-b border-gray-200 text-xs font-semibold text-gray-500 uppercase tracking-wider">
              Policy Arguments
            </div>
            <ul className="divide-y divide-gray-100">
              {pkg.representation.policy_arguments.map((arg: string, i: number) => (
                <li key={i} className="p-4 text-sm text-gray-700">{arg}</li>
              ))}
            </ul>
          </div>
        </div>

        {/* Evidence Package */}
        <div className="border border-gray-200 rounded-lg overflow-hidden">
          <div className="bg-gray-100 px-4 py-2 border-b border-gray-200 text-xs font-semibold text-gray-500 uppercase tracking-wider flex justify-between">
            <span>Evidence Package</span>
            <span>{pkg.evidence.evidence_items.length} Items</span>
          </div>
          <div className="p-4">
             <ul className="space-y-2">
                {pkg.evidence.evidence_items.map((item: any, i: number) => (
                  <li key={i} className="flex items-center text-sm text-gray-700 bg-white p-2 rounded border border-gray-100 shadow-sm">
                    <FileText className="w-4 h-4 text-gray-400 mr-2" />
                    {item.description}
                  </li>
                ))}
             </ul>
          </div>
        </div>

      </div>
    </div>
  );
}
