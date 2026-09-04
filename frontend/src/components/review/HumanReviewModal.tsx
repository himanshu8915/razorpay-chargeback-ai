"use client";

import React, { useState } from "react";
import axios from "axios";
import { UserCheck, ShieldAlert, CheckCircle, XCircle } from "lucide-react";

interface HumanReviewModalProps {
  disputeId: string;
  currentDecision: string;
  decisionArtifact: any;
  onSuccess: () => void;
  onClose: () => void;
}

export default function HumanReviewModal({
  disputeId,
  currentDecision,
  decisionArtifact,
  onSuccess,
  onClose,
}: HumanReviewModalProps) {
  const [selectedAction, setSelectedAction] = useState<"CONTEST" | "ACCEPT">("CONTEST");
  const [reason, setReason] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      await axios.post(`/api/v1/decision/${disputeId}/review`, {
        action: "EDIT",
        reviewer_id: "human_agent_1",
        reason: reason || "Manual human override based on merchant evidence review.",
        edited_decision: selectedAction,
      });

      onSuccess();
      onClose();
    } catch (error) {
      console.error("Failed to submit human review", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="bg-white dark:bg-neutral-900 rounded-xl shadow-xl border border-neutral-200 dark:border-neutral-800 w-full max-w-lg overflow-hidden">
        <div className="px-6 py-4 border-b border-neutral-200 dark:border-neutral-800 bg-neutral-50 dark:bg-neutral-800/50 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <UserCheck className="w-6 h-6 text-amber-600" />
            <h3 className="font-semibold text-neutral-900 dark:text-neutral-100">
              Human-in-the-Loop Review
            </h3>
          </div>
          <button
            onClick={onClose}
            className="text-neutral-400 hover:text-neutral-600 text-sm font-medium"
          >
            ✕
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          <div>
            <p className="text-sm text-neutral-600 dark:text-neutral-400">
              Case <span className="font-semibold text-neutral-900 dark:text-neutral-100">{disputeId}</span> requires human verification. You can override or confirm the AI recommendation.
            </p>
          </div>

          <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 space-y-3">
            <h4 className="font-semibold text-amber-900 text-sm">AI Recommendation: {decisionArtifact?.decision}</h4>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-amber-700 block text-xs uppercase">Confidence</span>
                <span className="font-medium text-amber-900">{(decisionArtifact?.confidence * 100).toFixed(1)}%</span>
              </div>
              <div>
                <span className="text-amber-700 block text-xs uppercase">Policy Context</span>
                <span className="font-medium text-amber-900">{decisionArtifact?.reason_codes?.join(", ") || "None"}</span>
              </div>
            </div>
            
            <div className="pt-2 border-t border-amber-200/50">
              <span className="text-amber-700 block text-xs uppercase mb-1">Reasoning</span>
              <p className="text-sm text-amber-900">{decisionArtifact?.rationale}</p>
            </div>
            
            {(decisionArtifact?.missing_evidence?.length > 0) && (
              <div className="pt-2 border-t border-amber-200/50">
                <span className="text-red-600 block text-xs uppercase mb-1 flex items-center">
                  <XCircle className="w-3 h-3 mr-1" /> Missing Evidence Flag
                </span>
                <ul className="text-sm text-red-800 list-disc list-inside">
                  {decisionArtifact.missing_evidence.map((item: string, i: number) => (
                    <li key={i}>{item}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-2">
              Set Manual Final Decision
            </label>
            <div className="grid grid-cols-2 gap-4">
              <button
                type="button"
                onClick={() => setSelectedAction("CONTEST")}
                className={`flex items-center justify-center p-3 rounded-lg border text-sm font-semibold transition-all ${
                  selectedAction === "CONTEST"
                    ? "border-indigo-600 bg-indigo-50 text-indigo-700 dark:bg-indigo-950/40 dark:text-indigo-400"
                    : "border-neutral-200 dark:border-neutral-800 hover:bg-neutral-50 dark:hover:bg-neutral-800"
                }`}
              >
                <ShieldAlert className="w-4 h-4 mr-2" />
                CONTEST (Fight)
              </button>

              <button
                type="button"
                onClick={() => setSelectedAction("ACCEPT")}
                className={`flex items-center justify-center p-3 rounded-lg border text-sm font-semibold transition-all ${
                  selectedAction === "ACCEPT"
                    ? "border-gray-600 bg-gray-100 text-gray-800 dark:bg-neutral-800 dark:text-neutral-300"
                    : "border-neutral-200 dark:border-neutral-800 hover:bg-neutral-50 dark:hover:bg-neutral-800"
                }`}
              >
                <CheckCircle className="w-4 h-4 mr-2" />
                ACCEPT (No Contest)
              </button>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-1">
              Review Rationale / Notes
            </label>
            <textarea
              rows={3}
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="e.g. Additional evidence verified manually, overriding AI missing evidence flag."
              className="w-full rounded-md border border-neutral-300 dark:border-neutral-700 bg-white dark:bg-neutral-900 p-2.5 text-sm text-neutral-900 dark:text-neutral-100 focus:ring-2 focus:ring-amber-500 focus:outline-none"
            />
          </div>

          <div className="flex justify-end space-x-3 pt-2 border-t border-neutral-100 dark:border-neutral-800">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-neutral-700 dark:text-neutral-300 hover:bg-neutral-100 dark:hover:bg-neutral-800 rounded-md"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 text-sm font-medium text-white bg-amber-600 hover:bg-amber-700 disabled:opacity-50 rounded-md shadow-sm"
            >
              {isSubmitting ? "Submitting..." : "Confirm Decision"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
