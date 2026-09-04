import React from "react";
import { formatCurrency } from "@/utils/formatters";
import { Scale, Info } from "lucide-react";

export default function CaseDecisionTab({ caseData }: { caseData: any }) {
  const decision = caseData.decision_artifact;

  return (
    <div className="bg-white shadow rounded-lg border border-gray-200 overflow-hidden">
      <div className="px-6 py-5 border-b border-gray-200 bg-slate-50 flex items-center justify-between">
        <div className="flex items-center">
          <Scale className="w-6 h-6 text-blue-600 mr-3" />
          <h2 className="text-lg font-medium text-gray-900">Decision Rationale</h2>
        </div>
        <span className={`inline-flex items-center rounded-md px-3 py-1 text-sm font-bold ${
          decision?.decision === "CONTEST" ? "bg-indigo-100 text-indigo-800" :
          decision?.decision === "REVIEW" ? "bg-amber-100 text-amber-800" :
          "bg-gray-100 text-gray-800"
        }`}>
          {decision?.decision || "PENDING"}
        </span>
      </div>

      <div className="p-6">
        <div className="prose prose-blue max-w-none text-gray-700">
          <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wider mb-2">Explanation</h3>
          <p className="text-base leading-relaxed bg-gray-50 p-4 rounded-md border border-gray-100 whitespace-pre-wrap">
            {decision?.rationale || "No rationale provided."}
          </p>
        </div>

        <div className="mt-8 grid grid-cols-2 md:grid-cols-4 gap-6">
          <div className="bg-slate-50 p-4 rounded-lg border border-slate-100">
            <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Confidence</p>
            <p className="text-lg font-semibold text-gray-900">{(decision?.confidence * 100).toFixed(1)}%</p>
          </div>
          <div className="bg-slate-50 p-4 rounded-lg border border-slate-100">
            <p className="text-xs text-gray-500 uppercase tracking-wider mb-1">Case Strength</p>
            <p className="text-lg font-semibold text-gray-900">{(decision?.case_strength * 10).toFixed(1)} / 10</p>
          </div>
          <div className="bg-emerald-50 p-4 rounded-lg border border-emerald-100">
            <p className="text-xs text-emerald-700 uppercase tracking-wider mb-1">Net Expected Value</p>
            <p className="text-lg font-bold text-emerald-800">{formatCurrency(decision?.net_expected_value || 0)}</p>
          </div>
          <div className="bg-blue-50 p-4 rounded-lg border border-blue-100">
            <p className="text-xs text-blue-700 uppercase tracking-wider mb-1">Success Likelihood</p>
            <p className="text-lg font-bold text-blue-800">{(decision?.success_likelihood * 100).toFixed(1)}%</p>
          </div>
        </div>

        <div className="mt-8">
          <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wider mb-3">Reason Codes</h3>
          <div className="flex flex-wrap gap-2">
            {decision?.reason_codes?.map((code: string) => (
              <span key={code} className="inline-flex items-center rounded-full bg-slate-100 px-3 py-1 text-sm font-medium text-slate-800 border border-slate-200">
                {code}
              </span>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
}
