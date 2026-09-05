import React, { useState } from "react";
import axios from "axios";
import { formatCurrency, formatDate } from "@/utils/formatters";
import { DollarSign, ShieldAlert, FileText, AlertTriangle, PlayCircle } from "lucide-react";

export default function CaseOverviewTab({ caseData }: { caseData: any }) {
  const dispute = caseData?.case?.dispute || {};
  const decision = caseData?.decision_artifact || {};
  const [hasAcknowledged, setHasAcknowledged] = useState(false);
  const [hasFought, setHasFought] = useState(false);
  
  const handleAction = () => {
    if (decision?.decision === "CONTEST") {
      setHasFought(true);
    } else {
      setHasAcknowledged(true);
    }
  };
  
  return (
    <div className="space-y-6">
      
      {/* 20-Metric Case Intelligence Panel Grouping */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        
        {/* Economics */}
        <div className="bg-white rounded-lg shadow border border-gray-200 overflow-hidden">
          <div className="px-4 py-3 bg-slate-50 border-b border-gray-200 flex items-center">
            <DollarSign className="w-5 h-5 text-emerald-600 mr-2" />
            <h3 className="text-sm font-semibold text-gray-900">Economics</h3>
          </div>
          <div className="p-4 space-y-4">
            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wider">Dispute Amount</p>
              <p className="font-semibold text-gray-900 text-lg">{formatCurrency(dispute.dispute_amount)}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wider">Recoverable Amount</p>
              <p className="font-medium text-blue-700">{formatCurrency(decision?.recoverable_amount || 0)}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wider">Expected Recovery</p>
              <p className="font-medium text-emerald-700">{formatCurrency(decision?.expected_recovery || 0)}</p>
            </div>
            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wider">Fight Cost (Est.)</p>
              <p className="font-medium text-red-600">{formatCurrency(decision?.estimated_operational_cost || 0)}</p>
            </div>
            <div className="pt-2 border-t border-gray-100">
              <p className="text-xs text-gray-500 uppercase tracking-wider">Net Expected Value</p>
              <p className={`font-bold text-lg ${decision?.net_expected_value > 0 ? "text-emerald-600" : "text-gray-900"}`}>
                {formatCurrency(decision?.net_expected_value || 0)}
              </p>
            </div>
          </div>
        </div>

        {/* Intelligence */}
        <div className="bg-white rounded-lg shadow border border-gray-200 overflow-hidden">
          <div className="px-4 py-3 bg-slate-50 border-b border-gray-200 flex items-center">
            <ShieldAlert className="w-5 h-5 text-indigo-600 mr-2" />
            <h3 className="text-sm font-semibold text-gray-900">Intelligence</h3>
          </div>
          <div className="p-4 space-y-4">
            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wider">Decision</p>
              <span className={`inline-flex mt-1 items-center rounded-md px-2.5 py-0.5 text-sm font-medium ${
                decision?.decision === "CONTEST" ? "bg-indigo-100 text-indigo-800" :
                decision?.decision === "REVIEW" ? "bg-amber-100 text-amber-800" :
                "bg-gray-100 text-gray-800"
              }`}>
                {decision?.decision || "PENDING"}
              </span>
            </div>
            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wider">Confidence</p>
              <p className="font-medium text-gray-900">{(decision?.confidence * 100).toFixed(1)}%</p>
            </div>
            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wider">Success Likelihood</p>
              <p className="font-medium text-gray-900">{(decision?.success_likelihood * 100).toFixed(1)}%</p>
            </div>
            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wider">Case Strength</p>
              <p className="font-medium text-gray-900">{(decision?.case_strength * 10).toFixed(1)} / 10</p>
            </div>
            <div className="pt-2 border-t border-gray-100">
              <p className="text-xs text-gray-500 uppercase tracking-wider">Reason Codes</p>
              <div className="flex flex-wrap gap-1 mt-1">
                {decision?.reason_codes?.map((code: string) => (
                  <span key={code} className="inline-flex items-center rounded bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-600">
                    {code}
                  </span>
                )) || <span className="text-sm text-gray-400">None</span>}
              </div>
            </div>
          </div>
        </div>

        {/* Risk & Workflow */}
        <div className="bg-white rounded-lg shadow border border-gray-200 overflow-hidden flex flex-col justify-between">
          <div>
            <div className="px-4 py-3 bg-slate-50 border-b border-gray-200 flex items-center">
              <AlertTriangle className="w-5 h-5 text-red-600 mr-2" />
              <h3 className="text-sm font-semibold text-gray-900">Risk & Workflow</h3>
            </div>
            <div className="p-4 space-y-4">
              <div>
                <p className="text-xs text-gray-500 uppercase tracking-wider">Deadline Risk</p>
                <p className={`font-medium ${decision?.deadline_risk === "HIGH" ? "text-red-600" : "text-gray-900"}`}>
                  {decision?.deadline_risk || "UNKNOWN"}
                </p>
              </div>
              <div>
                <p className="text-xs text-gray-500 uppercase tracking-wider">Workflow Status</p>
                <p className="font-medium text-gray-900">{decision?.workflow_status || "ANALYSIS_COMPLETE"}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500 uppercase tracking-wider">Next Action</p>
                <p className="font-medium text-gray-900">{decision?.next_action || "AWAITING_REVIEW"}</p>
              </div>
              <div>
                <p className="text-xs text-gray-500 uppercase tracking-wider">Risk Flags</p>
                <ul className="mt-1 space-y-1">
                  {decision?.risk_flags?.length > 0 ? decision.risk_flags.map((flag: string, i: number) => (
                    <li key={i} className="text-sm text-red-600 flex items-start">
                      <span className="mr-1.5">•</span> {flag}
                    </li>
                  )) : <li className="text-sm text-gray-500">No major risks identified.</li>}
                </ul>
              </div>
            </div>
          </div>
          
          <div className="p-4 bg-gray-50 border-t border-gray-200 mt-auto">
            <button 
              onClick={handleAction}
              disabled={hasFought || hasAcknowledged}
              className={`w-full flex items-center justify-center rounded-md px-3 py-2 text-sm font-bold shadow-sm transition-all ${
                decision?.decision === "CONTEST" 
                  ? "bg-indigo-600 text-white hover:bg-indigo-500" 
                  : "bg-gray-200 text-gray-700 hover:bg-gray-300"
              } disabled:opacity-50`}
            >
              <PlayCircle className="w-5 h-5 mr-2" /> 
              {decision?.decision === "CONTEST" 
                ? (hasFought ? "FIGHT ACKNOWLEDGED" : "FIGHT THIS CASE") 
                : (hasAcknowledged ? "ACKNOWLEDGED" : "ACKNOWLEDGE")}
            </button>
          </div>
        </div>

      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Rationale */}
        <div className="bg-white rounded-lg shadow border border-gray-200 overflow-hidden">
          <div className="px-4 py-3 bg-slate-50 border-b border-gray-200 flex items-center">
            <FileText className="w-5 h-5 text-blue-600 mr-2" />
            <h3 className="text-sm font-semibold text-gray-900">AI Rationale</h3>
          </div>
          <div className="p-4 prose prose-sm max-w-none">
            <p className="text-gray-800">{decision?.rationale || "No rationale provided."}</p>
          </div>
        </div>

        {/* Evidence Assessment Summary */}
        <div className="bg-white rounded-lg shadow border border-gray-200 overflow-hidden">
          <div className="px-4 py-3 bg-slate-50 border-b border-gray-200 flex items-center">
            <ShieldAlert className="w-5 h-5 text-purple-600 mr-2" />
            <h3 className="text-sm font-semibold text-gray-900">Evidence Assessment</h3>
          </div>
          <div className="p-4 space-y-4">
            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wider">Key Evidence</p>
              <ul className="mt-1 space-y-1">
                {decision?.key_evidence?.length > 0 ? decision.key_evidence.map((item: string, i: number) => (
                  <li key={i} className="text-sm text-gray-900">• {item}</li>
                )) : <li className="text-sm text-gray-400">None</li>}
              </ul>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-xs text-gray-500 uppercase tracking-wider">Supporting</p>
                <p className="mt-1 text-sm font-medium text-gray-900">{decision?.supporting_evidence?.length || 0} items</p>
              </div>
              <div>
                <p className="text-xs text-gray-500 uppercase tracking-wider">Contradicting</p>
                <p className="mt-1 text-sm font-medium text-gray-900">{decision?.contradicting_evidence?.length || 0} items</p>
              </div>
            </div>
            <div>
              <p className="text-xs text-gray-500 uppercase tracking-wider">Missing Evidence</p>
              <ul className="mt-1 space-y-1">
                {decision?.missing_evidence?.length > 0 ? decision.missing_evidence.map((item: string, i: number) => (
                  <li key={i} className="text-sm text-orange-600 flex items-start">
                    <span className="mr-1.5">-</span> {item}
                  </li>
                )) : <li className="text-sm text-gray-400">None</li>}
              </ul>
            </div>
          </div>
        </div>
      </div>

      {/* System Telemetry */}
      <div className="bg-white rounded-lg shadow border border-gray-200 overflow-hidden">
        <div className="px-4 py-3 bg-slate-50 border-b border-gray-200 flex items-center">
          <AlertTriangle className="w-5 h-5 text-gray-500 mr-2" />
          <h3 className="text-sm font-semibold text-gray-900">System Telemetry</h3>
        </div>
        <div className="p-4 grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-xs text-gray-500 uppercase tracking-wider">Token Usage</p>
            <p className="font-medium text-gray-900">{decision?.token_usage?.total_tokens ?? 0} tokens</p>
          </div>
          <div>
            <p className="text-xs text-gray-500 uppercase tracking-wider">Token Cost</p>
            <p className="font-medium text-gray-900">${(decision?.token_cost?.total_cost ?? 0).toFixed(4)}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500 uppercase tracking-wider">Model</p>
            <p className="font-medium text-gray-900">{decision?.llm_model || "gemini-3.5-flash-lite"}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500 uppercase tracking-wider">Pipeline Duration</p>
            <p className="font-medium text-gray-900">
              {decision?.created_at && decision?.updated_at
                ? `${((new Date(decision.updated_at).getTime() - new Date(decision.created_at).getTime()) / 1000).toFixed(1)}s`
                : "N/A"}
            </p>
          </div>
        </div>
      </div>

    </div>
  );
}
