"use client";

import React, { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import { useMerchant } from "@/app/MerchantContext";
import { formatCurrency, formatDate } from "@/utils/formatters";
import { ChevronLeft, FileText, CheckCircle2, ShieldAlert, AlertTriangle } from "lucide-react";
import Link from "next/link";
import CaseOverviewTab from "@/components/cases/CaseOverviewTab";
import CaseEvidenceTab from "@/components/cases/CaseEvidenceTab";
import CaseDecisionTab from "@/components/cases/CaseDecisionTab";
import CaseRepresentmentTab from "@/components/cases/CaseRepresentmentTab";
import CaseTimelineTab from "@/components/cases/CaseTimelineTab";
import HumanReviewModal from "@/components/review/HumanReviewModal";

export default function CaseWorkspace() {
  const { caseId } = useParams();
  const { activeMerchantId } = useMerchant();
  const router = useRouter();
  const [activeTab, setActiveTab] = useState("overview");
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isReviewOpen, setIsReviewOpen] = useState(false);

  const { data: caseData, isLoading, refetch } = useQuery({
    queryKey: ["dispute", caseId],
    queryFn: async () => {
      const res = await axios.get(`/api/v1/disputes/${caseId}`);
      return res.data;
    },
    refetchInterval: isAnalyzing ? 3000 : false,
  });

  const handleRunAnalysis = async () => {
    try {
      setIsAnalyzing(true);
      await axios.post(`/api/v1/decision/${caseId}/analyze`);
    } catch (error) {
      console.error("Failed to start analysis", error);
      setIsAnalyzing(false);
      // In a real app we'd show a toast notification here
    }
  };

  // If caseData updates and decisionArtifact appears, stop analyzing
  React.useEffect(() => {
    if (caseData?.decision_artifact) {
      setIsAnalyzing(false);
    }
  }, [caseData?.decision_artifact]);

  React.useEffect(() => {
    if (typeof window !== "undefined") {
      const params = new URLSearchParams(window.location.search);
      if (params.get("analyze") === "true" && !caseData?.decision_artifact) {
        setIsAnalyzing(true);
      }
    }
  }, [caseData?.decision_artifact]);

  // Poll real execution state
  const { data: progressData } = useQuery({
    queryKey: ["dispute_progress", caseId],
    queryFn: async () => {
      const res = await axios.get(`/api/v1/decision/${caseId}/progress`);
      return res.data;
    },
    refetchInterval: isAnalyzing ? 2000 : false,
  });

  // Automatically transition based on status
  React.useEffect(() => {
    if (progressData?.status === "COMPLETED") {
      setIsAnalyzing(false);
      refetch(); // Fetch full decision artifact
    } else if (progressData?.status === "FAILED" || progressData?.status === "TIMEOUT") {
      // Don't auto-reset isAnalyzing, we want to show the error card
    }
  }, [progressData, refetch]);

  const { data: representmentData } = useQuery({
    queryKey: ["representment", caseId],
    queryFn: async () => {
      try {
        const res = await axios.get(`/api/v1/disputes/${caseId}/representment`);
        return res.data;
      } catch (e) {
        return null;
      }
    },
    retry: false
  });

  const decisionArtifact = caseData?.decision_artifact || null; 
  
  if (isLoading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="flex flex-col items-center space-y-4">
          <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
          <div className="text-gray-500 font-medium animate-pulse">Retrieving case information...</div>
        </div>
      </div>
    );
  }

  if (!caseData) {
    return (
      <div className="text-center py-12">
        <h3 className="mt-2 text-sm font-semibold text-gray-900">Case not found</h3>
        <p className="mt-1 text-sm text-gray-500">Could not retrieve case {caseId}.</p>
        <div className="mt-6">
          <button onClick={() => router.back()} className="text-blue-600 hover:text-blue-900">Go back</button>
        </div>
      </div>
    );
  }

  const dispute = caseData.case.dispute;
  
  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="bg-white shadow rounded-lg border border-gray-200 overflow-hidden">
        <div className="p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button onClick={() => router.back()} className="p-2 -ml-2 text-gray-400 hover:text-gray-600 rounded-full hover:bg-gray-100">
                <ChevronLeft className="w-6 h-6" />
              </button>
              <div>
                <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-3">
                  {dispute.dispute_id}
                  <span className="inline-flex items-center rounded-md bg-blue-50 px-2 py-1 text-xs font-medium text-blue-700 ring-1 ring-inset ring-blue-700/10">
                    {formatCurrency(dispute.dispute_amount)}
                  </span>
                  {decisionArtifact && (
                    <span className={`inline-flex items-center rounded-md px-2 py-1 text-xs font-medium ring-1 ring-inset ${
                      decisionArtifact.decision === 'CONTEST' ? 'bg-indigo-50 text-indigo-700 ring-indigo-600/20' : 
                      decisionArtifact.decision === 'REVIEW' ? 'bg-amber-50 text-amber-700 ring-amber-600/20' : 
                      'bg-gray-50 text-gray-600 ring-gray-500/10'
                    }`}>
                      {decisionArtifact.decision}
                    </span>
                  )}
                </h1>
                <p className="text-sm text-gray-500 mt-1">
                  {dispute.dispute_type} • Opened {formatDate(dispute.dispute_opened_at)}
                </p>
              </div>
            </div>
            
            {/* Right side header metrics & HITL action */}
            {decisionArtifact && (
              <div className="flex items-center space-x-6 text-sm">
                <div>
                  <p className="text-gray-500 font-medium">Case Strength</p>
                  <p className="font-bold text-gray-900">{Math.round((decisionArtifact.case_strength || 0) * 100)}/100</p>
                </div>
                <div>
                  <p className="text-gray-500 font-medium">Confidence</p>
                  <p className="font-bold text-gray-900">{decisionArtifact.confidence}</p>
                </div>
                <div>
                  <p className="text-gray-500 font-medium">Deadline Risk</p>
                  <p className={`font-bold ${decisionArtifact.deadline_risk === 'HIGH' ? 'text-red-600' : 'text-gray-900'}`}>
                    {decisionArtifact.deadline_risk}
                  </p>
                </div>

                {(decisionArtifact.decision === "REVIEW" || decisionArtifact.workflow_status === "NEEDS_REVIEW") && (
                  <button
                    onClick={() => setIsReviewOpen(true)}
                    className="inline-flex items-center rounded-md bg-amber-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-amber-500 animate-pulse"
                  >
                    Human Review Required
                  </button>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Tabs */}
        {decisionArtifact ? (
          <div className="border-t border-gray-200 bg-gray-50 px-6">
            <nav className="-mb-px flex space-x-8" aria-label="Tabs">
              {[
                { id: "overview", name: "Overview" },
                { id: "evidence", name: "Evidence Explorer" },
                { id: "decision", name: "Decision Analysis" },
                { id: "representment", name: "Representment & Submission" },
                { id: "timeline", name: "Timeline" },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`
                    whitespace-nowrap border-b-2 py-3 px-1 text-sm font-medium transition-colors
                    ${activeTab === tab.id
                      ? "border-blue-500 text-blue-600"
                      : "border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700"
                    }
                  `}
                >
                  {tab.name}
                </button>
              ))}
            </nav>
          </div>
        ) : null}
      </div>

      {/* Tab Content / Hero Action */}
      <div className="mt-6">
        {!decisionArtifact ? (
          <div className="bg-white shadow rounded-lg border border-gray-200 p-12">
            {isAnalyzing ? (
              <div className="max-w-2xl mx-auto">
                {progressData?.status === "FAILED" || progressData?.status === "TIMEOUT" ? (
                  <div className="text-center space-y-6 py-6">
                    <div className="w-16 h-16 bg-red-100 text-red-600 rounded-full flex items-center justify-center mx-auto">
                      <AlertTriangle className="w-8 h-8" />
                    </div>
                    <div>
                      <h3 className="text-xl font-bold text-red-700">
                        {progressData?.status === "TIMEOUT" ? "ANALYSIS TIMED OUT" : "ANALYSIS FAILED"}
                      </h3>
                      <p className="text-gray-600 mt-2 max-w-md mx-auto">
                        {progressData?.error_message || "The analysis could not be completed."}
                      </p>
                      {progressData?.active_agent && (
                        <p className="text-xs text-gray-500 mt-2">Failed at agent: {progressData.active_agent}</p>
                      )}
                    </div>
                    <button
                      onClick={handleRunAnalysis}
                      className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700"
                    >
                      Retry Analysis
                    </button>
                  </div>
                ) : (
                  <div className="space-y-8">
                    <div className="text-center">
                      <h3 className="text-xl font-bold text-gray-900 flex items-center justify-center gap-3">
                        <div className="w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                        ANALYSIS IN PROGRESS
                      </h3>
                      <p className="text-gray-500 mt-2 text-sm">
                        Case analysis is being orchestrated across the evidence and decision agents.
                      </p>
                    </div>
                    
                    {/* Real-time Execution Timeline */}
                    <div className="bg-gray-50 rounded-lg border border-gray-100 p-6 font-mono text-sm shadow-inner">
                      {progressData?.nodes?.length > 0 ? (
                        <div className="space-y-0 relative before:absolute before:inset-0 before:ml-4 before:-translate-x-px md:before:mx-auto md:before:translate-x-0 before:h-full before:w-0.5 before:bg-gradient-to-b before:from-transparent before:via-gray-200 before:to-transparent">
                          {progressData.nodes.map((node: any, idx: number) => {
                            const isCompleted = node.status === "completed";
                            const isActive = node.status === "running";
                            
                            return (
                              <div key={node.id} className="relative flex items-center py-3 group">
                                <div className={`flex items-center justify-center w-8 h-8 rounded-full z-10 shrink-0 ${
                                  isCompleted ? "bg-green-100 text-green-600" :
                                  isActive ? "bg-blue-600 text-white animate-pulse shadow-lg shadow-blue-500/30" :
                                  "bg-gray-200 text-gray-400"
                                }`}>
                                  {isCompleted ? <CheckCircle2 className="w-5 h-5" /> :
                                   isActive ? <div className="w-2.5 h-2.5 bg-white rounded-full"></div> :
                                   <div className="w-1.5 h-1.5 bg-gray-400 rounded-full"></div>}
                                </div>
                                
                                <div className={`ml-4 ${isActive ? 'text-gray-900 font-bold' : isCompleted ? 'text-gray-500' : 'text-gray-400'}`}>
                                  <div className="flex items-center gap-2">
                                    <span>{node.label}</span>
                                    {isActive && <span className="text-[10px] uppercase tracking-wider bg-blue-100 text-blue-700 px-2 py-0.5 rounded font-semibold">ACTIVE</span>}
                                    {!isActive && !isCompleted && <span className="text-[10px] uppercase tracking-wider text-gray-400">WAITING</span>}
                                  </div>
                                  {isActive && progressData.message && (
                                    <div className="text-xs text-blue-600 mt-1 font-sans">{progressData.message}</div>
                                  )}
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      ) : (
                        <div className="text-center text-gray-400 py-4 animate-pulse">Initializing execution graph...</div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="space-y-6 text-center">
                <div className="mx-auto w-16 h-16 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center">
                  <ShieldAlert className="w-8 h-8" />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-gray-900">Unanalyzed Dispute</h3>
                  <p className="text-gray-500 mt-2 max-w-md mx-auto">
                    This dispute has not yet been processed by the AI agent. Run the analysis to discover evidence, assess policy compliance, and calculate the net expected value.
                  </p>
                </div>
                <button
                  onClick={handleRunAnalysis}
                  className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  Run Analysis
                </button>
              </div>
            )}
          </div>
        ) : (
          <>
            {activeTab === "overview" && <CaseOverviewTab caseData={caseData} />}
            {activeTab === "evidence" && <CaseEvidenceTab caseData={caseData} />}
            {activeTab === "decision" && <CaseDecisionTab caseData={caseData} />}
            {activeTab === "representment" && <CaseRepresentmentTab caseData={caseData} representmentData={representmentData} />}
            {activeTab === "timeline" && <CaseTimelineTab caseData={caseData} />}
          </>
        )}
      </div>

      {isReviewOpen && (
        <HumanReviewModal
          disputeId={caseId as string}
          currentDecision={decisionArtifact?.decision || "REVIEW"}
          decisionArtifact={decisionArtifact}
          onSuccess={() => refetch()}
          onClose={() => setIsReviewOpen(false)}
        />
      )}
    </div>
  );
}
