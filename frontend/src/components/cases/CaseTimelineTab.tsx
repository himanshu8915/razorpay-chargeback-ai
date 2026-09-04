import React from "react";
import { CheckCircle2, Clock, Check, FileText } from "lucide-react";
import { formatDate } from "@/utils/formatters";

export default function CaseTimelineTab({ caseData }: { caseData: any }) {
  const dispute = caseData?.case?.dispute || {};
  const decision = caseData?.decision_artifact || {};

  // Build a synthetic timeline using actual data from the backend
  const timeline = [];
  
  if (dispute.dispute_opened_at) {
    timeline.push({
      title: "Dispute Received",
      description: `Dispute ${dispute.dispute_id} was opened.`,
      date: formatDate(dispute.dispute_opened_at),
      icon: Clock,
      status: "complete",
      color: "text-gray-500",
      bgColor: "bg-gray-100"
    });
  }

  if (decision.created_at) {
    timeline.push({
      title: "Analysis Complete",
      description: `Automated decision engine recommended ${decision.decision}.`,
      date: formatDate(decision.created_at),
      icon: CheckCircle2,
      status: "complete",
      color: "text-blue-500",
      bgColor: "bg-blue-100"
    });
  }

  // Pending action step
  if (decision.decision === "CONTEST") {
    timeline.push({
      title: "Generate Representment",
      description: "Awaiting merchant action to generate and review the representment package.",
      date: "Pending",
      icon: FileText,
      status: "current",
      color: "text-indigo-600",
      bgColor: "bg-indigo-100"
    });
    timeline.push({
      title: "Submit to Issuer",
      description: "Submit the generated package to the issuing bank before the deadline.",
      date: "Pending",
      icon: Check,
      status: "upcoming",
      color: "text-gray-400",
      bgColor: "bg-gray-100"
    });
  } else {
    timeline.push({
      title: "Merchant Review",
      description: "Awaiting merchant action.",
      date: "Pending",
      icon: Clock,
      status: "current",
      color: "text-amber-600",
      bgColor: "bg-amber-100"
    });
  }

  return (
    <div className="bg-white p-6 shadow rounded-lg border border-gray-200">
      <h2 className="text-lg font-medium text-gray-900 mb-6">Case Workflow History</h2>
      
      <div className="flow-root">
        <ul role="list" className="-mb-8">
          {timeline.map((event, eventIdx) => (
            <li key={eventIdx}>
              <div className="relative pb-8">
                {eventIdx !== timeline.length - 1 ? (
                  <span className="absolute left-4 top-4 -ml-px h-full w-0.5 bg-gray-200" aria-hidden="true" />
                ) : null}
                <div className="relative flex space-x-3">
                  <div>
                    <span className={`h-8 w-8 rounded-full flex items-center justify-center ring-8 ring-white ${event.bgColor}`}>
                      <event.icon className={`h-5 w-5 ${event.color}`} aria-hidden="true" />
                    </span>
                  </div>
                  <div className="flex min-w-0 flex-1 justify-between space-x-4 pt-1.5">
                    <div>
                      <p className="text-sm text-gray-900 font-medium">{event.title}</p>
                      <p className="text-sm text-gray-500 mt-1">{event.description}</p>
                    </div>
                    <div className="whitespace-nowrap text-right text-sm text-gray-500">
                      <time>{event.date}</time>
                    </div>
                  </div>
                </div>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
