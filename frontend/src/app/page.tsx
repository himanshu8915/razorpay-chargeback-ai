"use client";

import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMerchant } from "@/app/MerchantContext";
import { formatCurrency } from "@/utils/formatters";
import { ArrowRight } from "lucide-react";

export default function DashboardPage() {
  const { activeMerchantId } = useMerchant();
  const router = useRouter();
  const [analyzingId, setAnalyzingId] = useState<string | null>(null);

  // 1. High-level dashboard metrics
  const { data: metrics, isLoading: metricsLoading } = useQuery({
    queryKey: ["dashboard-metrics", activeMerchantId],
    queryFn: async () => {
      if (!activeMerchantId) return null;
      const res = await axios.get(`/api/v1/dashboard/metrics?merchant_id=${activeMerchantId}`);
      return res.data;
    },
    enabled: !!activeMerchantId,
  });

  // 2. Deadline exposure buckets
  const { data: deadlines, isLoading: deadlinesLoading } = useQuery({
    queryKey: ["dashboard-deadlines", activeMerchantId],
    queryFn: async () => {
      if (!activeMerchantId) return null;
      const res = await axios.get(`/api/v1/dashboard/deadlines?merchant_id=${activeMerchantId}`);
      return res.data;
    },
    enabled: !!activeMerchantId,
  });

  // 3. Unanalyzed cases (up to 5 for Needs Attention)
  const { data: unanalyzed, isLoading: unanalyzedLoading } = useQuery({
    queryKey: ["unanalyzed-cases", activeMerchantId],
    queryFn: async () => {
      if (!activeMerchantId) return null;
      const res = await axios.get(`/api/v1/disputes/unanalyzed?merchant_id=${activeMerchantId}&page=1&size=5`);
      return res.data;
    },
    enabled: !!activeMerchantId,
  });

  // 4. Pending Review cases (up to 5 for Needs Attention)
  const { data: reviewCases } = useQuery({
    queryKey: ["review-cases", activeMerchantId],
    queryFn: async () => {
      if (!activeMerchantId) return null;
      const res = await axios.get(`/api/v1/disputes?merchant_id=${activeMerchantId}&decision=REVIEW&size=5`);
      return res.data;
    },
    enabled: !!activeMerchantId,
  });

  const handleAnalyze = async (caseId: string) => {
    try {
      setAnalyzingId(caseId);
      // Trigger actual backend decision pipeline
      await axios.post(`/api/v1/decision/${caseId}/analyze`);
      router.push(`/case/${caseId}?analyze=true`);
    } catch (err) {
      console.error("Failed to start analysis:", err);
      // Navigate to case workspace anyway so polling can catch ongoing analysis
      router.push(`/case/${caseId}?analyze=true`);
    }
  };

  if (!activeMerchantId) {
    return (
      <div className="flex h-[50vh] items-center justify-center">
        <div className="text-stone-500 font-medium text-sm">Please select a merchant to view the Command Center.</div>
      </div>
    );
  }

  if (metricsLoading || deadlinesLoading || unanalyzedLoading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-7 bg-stone-200 rounded w-1/4"></div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map(i => <div key={i} className="h-28 bg-stone-200 rounded-lg"></div>)}
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="h-44 bg-stone-200 rounded-lg"></div>
          <div className="h-44 bg-stone-200 rounded-lg"></div>
        </div>
      </div>
    );
  }

  // Combine review cases and unanalyzed cases for "Needs Attention" (top 5 max)
  const reviewItems = (reviewCases?.items || []).map((c: any) => ({
    dispute_id: c.dispute_id,
    dispute_amount: c.dispute_amount,
    dispute_type: c.dispute_type,
    statusType: "HUMAN_REVIEW",
    statusLabel: "HUMAN REVIEW",
    deadlineLabel: c.deadline_risk || (c.deadline ? new Date(c.deadline).toLocaleDateString("en-US", { month: "short", day: "numeric" }) : "—"),
    actionType: "REVIEW",
    actionLabel: "Review",
    actionHref: `/case/${c.dispute_id}`,
  }));

  const unanalyzedItems = (unanalyzed?.items || []).map((c: any) => {
    let dl = "—";
    if (c.dispute_opened_at) {
      const d = new Date(c.dispute_opened_at);
      d.setDate(d.getDate() + 30);
      dl = d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
    }
    return {
      dispute_id: c.dispute_id,
      dispute_amount: c.dispute_amount,
      dispute_type: c.dispute_type,
      statusType: "UNANALYZED",
      statusLabel: "UNANALYZED",
      deadlineLabel: dl,
      actionType: "ANALYZE",
      actionLabel: "Analyze",
      actionHref: `/case/${c.dispute_id}`,
    };
  });

  const needsAttentionList = [...reviewItems, ...unanalyzedItems].slice(0, 5);

  return (
    <div className="space-y-8 pb-12">
      
      {/* HERO SECTION */}
      <section className="relative overflow-hidden rounded-2xl bg-[#FBFBF9] px-6 sm:px-8 py-12 sm:py-16 lg:py-20 border border-stone-200 shadow-sm mb-6 sm:mb-10">
        <div className="max-w-4xl">
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-stone-900 tracking-tight mb-4 sm:mb-6">
            Every dispute.<br className="sm:hidden" /> One clear decision.
          </h1>
          <p className="text-base sm:text-lg lg:text-xl text-stone-600 mb-10 sm:mb-12 font-medium max-w-3xl leading-relaxed">
            Stop guessing on chargebacks. We analyze every case instantly to give you the exact answers you need to protect your revenue.
          </p>
        </div>
        
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
          {/* Question 1 */}
          <div className="bg-white px-5 py-6 rounded-xl border border-stone-200 shadow-2xs hover:border-stone-300 transition-colors">
            <div className="text-[10px] font-bold uppercase tracking-widest text-stone-400 mb-3 flex items-center">
              <span className="w-4 h-[1px] bg-stone-300 mr-2"></span>
              Decision
            </div>
            <h3 className="font-bold text-stone-900 leading-snug">Should I fight this?</h3>
          </div>
          {/* Question 2 */}
          <div className="bg-white px-5 py-6 rounded-xl border border-stone-200 shadow-2xs hover:border-stone-300 transition-colors">
            <div className="text-[10px] font-bold uppercase tracking-widest text-stone-400 mb-3 flex items-center">
              <span className="w-4 h-[1px] bg-stone-300 mr-2"></span>
              Reasoning
            </div>
            <h3 className="font-bold text-stone-900 leading-snug">Why do we believe we can win?</h3>
          </div>
          {/* Question 3 */}
          <div className="bg-white px-5 py-6 rounded-xl border border-stone-200 shadow-2xs hover:border-stone-300 transition-colors">
            <div className="text-[10px] font-bold uppercase tracking-widest text-stone-400 mb-3 flex items-center">
              <span className="w-4 h-[1px] bg-stone-300 mr-2"></span>
              Evidence
            </div>
            <h3 className="font-bold text-stone-900 leading-snug">What evidence proves or contradicts the claim?</h3>
          </div>
          {/* Question 4 */}
          <div className="bg-white px-5 py-6 rounded-xl border border-stone-200 shadow-2xs hover:border-stone-300 transition-colors">
            <div className="text-[10px] font-bold uppercase tracking-widest text-stone-400 mb-3 flex items-center">
              <span className="w-4 h-[1px] bg-stone-300 mr-2"></span>
              Action
            </div>
            <h3 className="font-bold text-stone-900 leading-snug">What happens next, and who needs to act before the deadline?</h3>
          </div>
        </div>
      </section>

      {/* 1. TITLE */}
      <div className="flex items-end justify-between border-b border-stone-200 pb-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-stone-900 uppercase">
            Command Center
          </h2>
          <p className="mt-1 text-xs text-stone-500 font-medium">
            Operational snapshot for {activeMerchantId}
          </p>
        </div>
      </div>

      {/* 2. ATTENTION (Work Queue Entry Points) */}
      <section>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-xs font-bold uppercase tracking-wider text-stone-500">Attention</h2>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          
          {/* Unanalyzed */}
          <div className="bg-white rounded-lg border border-stone-200 p-4 shadow-2xs flex flex-col justify-between hover:border-stone-300 transition-colors">
            <div>
              <p className="text-xs font-bold text-stone-500 uppercase tracking-wider">Unanalyzed</p>
              <p className="text-3xl font-extrabold text-stone-900 mt-2 tracking-tight">{metrics?.queues?.unanalyzed || 0}</p>
              <p className="text-xs text-stone-400 mt-1">Needs analysis</p>
            </div>
            <div className="mt-4 pt-3 border-t border-stone-100">
              <Link href="/queues/unanalyzed" className="text-xs font-semibold text-stone-700 hover:text-stone-900 inline-flex items-center">
                View cases <ArrowRight className="ml-1 h-3 w-3" />
              </Link>
            </div>
          </div>

          {/* Human Review */}
          <div className="bg-white rounded-lg border border-stone-200 p-4 shadow-2xs flex flex-col justify-between hover:border-amber-300 transition-colors">
            <div>
              <p className="text-xs font-bold text-stone-500 uppercase tracking-wider">Human Review</p>
              <p className="text-3xl font-extrabold text-amber-700 mt-2 tracking-tight">{metrics?.queues?.review || 0}</p>
              <p className="text-xs text-stone-400 mt-1">Needs decision</p>
            </div>
            <div className="mt-4 pt-3 border-t border-stone-100">
              <Link href="/queues/review" className="text-xs font-semibold text-amber-700 hover:text-amber-900 inline-flex items-center">
                Review <ArrowRight className="ml-1 h-3 w-3" />
              </Link>
            </div>
          </div>

          {/* Contest / Fight */}
          <div className="bg-white rounded-lg border border-stone-200 p-4 shadow-2xs flex flex-col justify-between hover:border-indigo-300 transition-colors">
            <div>
              <p className="text-xs font-bold text-stone-500 uppercase tracking-wider">Contest / Fight</p>
              <p className="text-3xl font-extrabold text-stone-900 mt-2 tracking-tight">{metrics?.queues?.contest || 0}</p>
              <p className="text-xs text-stone-400 mt-1">Ready to fight</p>
            </div>
            <div className="mt-4 pt-3 border-t border-stone-100">
              <Link href="/queues/contest" className="text-xs font-semibold text-indigo-700 hover:text-indigo-900 inline-flex items-center">
                View cases <ArrowRight className="ml-1 h-3 w-3" />
              </Link>
            </div>
          </div>

          {/* Accept */}
          <div className="bg-white rounded-lg border border-stone-200 p-4 shadow-2xs flex flex-col justify-between hover:border-stone-300 transition-colors">
            <div>
              <p className="text-xs font-bold text-stone-500 uppercase tracking-wider">Accept</p>
              <p className="text-3xl font-extrabold text-stone-900 mt-2 tracking-tight">{metrics?.queues?.accept || 0}</p>
              <p className="text-xs text-stone-400 mt-1">No contest</p>
            </div>
            <div className="mt-4 pt-3 border-t border-stone-100">
              <Link href="/queues/accept" className="text-xs font-semibold text-stone-700 hover:text-stone-900 inline-flex items-center">
                View cases <ArrowRight className="ml-1 h-3 w-3" />
              </Link>
            </div>
          </div>

        </div>
      </section>

      {/* 3. RECOVERY & DEADLINES */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        
        {/* RECOVERY */}
        <section>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-xs font-bold uppercase tracking-wider text-stone-500">Recovery</h2>
          </div>
          <div className="bg-white rounded-lg border border-stone-200 shadow-2xs overflow-hidden">
            <ul className="divide-y divide-stone-100 text-sm">
              <li className="flex justify-between items-center px-4 py-3">
                <span className="font-medium text-stone-500">Total Disputed</span>
                <span className="font-bold text-stone-900">{formatCurrency(metrics?.total_disputed_value || 0)}</span>
              </li>
              <li className="flex justify-between items-center px-4 py-3 bg-stone-50/50">
                <span className="font-medium text-stone-500">Recoverable</span>
                <span className="font-bold text-stone-900">{formatCurrency(metrics?.recoverable_opportunity || 0)}</span>
              </li>
              <li className="flex justify-between items-center px-4 py-3">
                <span className="font-medium text-stone-500">Expected Recovery</span>
                <span className="font-bold text-emerald-700">{formatCurrency(metrics?.expected_recovery || 0)}</span>
              </li>
              <li className="flex justify-between items-center px-4 py-3 bg-red-50/20">
                <span className="font-medium text-stone-500">At Risk</span>
                <span className="font-bold text-red-700">{formatCurrency((deadlines?.under_12h?.value || 0) + (deadlines?.under_24h?.value || 0))}</span>
              </li>
            </ul>
          </div>
        </section>

        {/* DEADLINES */}
        <section>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-xs font-bold uppercase tracking-wider text-stone-500">Deadlines</h2>
          </div>
          <div className="bg-white rounded-lg border border-stone-200 shadow-2xs overflow-hidden flex flex-col justify-between h-[calc(100%-27px)]">
            <ul className="divide-y divide-stone-100 text-sm flex-1">
              <li className="flex items-center justify-between px-4 py-3">
                <div className="flex items-center space-x-2.5">
                  <span className="w-2 h-2 rounded-full bg-red-500"></span>
                  <span className="font-medium text-stone-700">Critical (&lt; 12h)</span>
                </div>
                <div className="text-right font-bold text-stone-900">
                  {deadlines?.under_12h?.count || 0} / {formatCurrency(deadlines?.under_12h?.value || 0)}
                </div>
              </li>
              <li className="flex items-center justify-between px-4 py-3">
                <div className="flex items-center space-x-2.5">
                  <span className="w-2 h-2 rounded-full bg-orange-400"></span>
                  <span className="font-medium text-stone-700">Urgent (12–24h)</span>
                </div>
                <div className="text-right font-bold text-stone-900">
                  {deadlines?.under_24h?.count || 0} / {formatCurrency(deadlines?.under_24h?.value || 0)}
                </div>
              </li>
              <li className="flex items-center justify-between px-4 py-3">
                <div className="flex items-center space-x-2.5">
                  <span className="w-2 h-2 rounded-full bg-blue-400"></span>
                  <span className="font-medium text-stone-700">Upcoming (Next 2 days)</span>
                </div>
                <div className="text-right font-bold text-stone-900">
                  {deadlines?.next_2_days?.count || 0} / {formatCurrency(deadlines?.next_2_days?.value || 0)}
                </div>
              </li>
            </ul>
            <div className="px-4 py-2.5 bg-stone-50 border-t border-stone-100 flex items-center justify-end">
              <Link href="/deadlines" className="text-xs font-semibold text-stone-600 hover:text-stone-900 inline-flex items-center">
                View all deadlines <ArrowRight className="ml-1 h-3 w-3" />
              </Link>
            </div>
          </div>
        </section>

      </div>

      {/* 4. NEEDS ATTENTION */}
      <section>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-xs font-bold uppercase tracking-wider text-stone-500">Needs Attention</h2>
        </div>
        <div className="bg-white rounded-lg border border-stone-200 shadow-2xs overflow-hidden">
          {needsAttentionList.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-stone-100 text-left text-xs">
                <thead>
                  <tr className="bg-stone-50 text-stone-400 font-semibold uppercase tracking-wider">
                    <th scope="col" className="px-4 py-2.5">Case</th>
                    <th scope="col" className="px-4 py-2.5">Amount</th>
                    <th scope="col" className="px-4 py-2.5">Status</th>
                    <th scope="col" className="px-4 py-2.5">Deadline</th>
                    <th scope="col" className="px-4 py-2.5 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-stone-100 text-stone-700 font-medium">
                  {needsAttentionList.map((caseItem: any) => (
                    <tr key={caseItem.dispute_id} className="hover:bg-stone-50/60 transition-colors">
                      <td className="px-4 py-3 font-bold text-stone-900">
                        <Link href={`/case/${caseItem.dispute_id}`} className="hover:underline">
                          {caseItem.dispute_id}
                        </Link>
                      </td>
                      <td className="px-4 py-3 font-semibold text-stone-900">
                        {formatCurrency(caseItem.dispute_amount)}
                      </td>
                      <td className="px-4 py-3">
                        {caseItem.statusType === "HUMAN_REVIEW" ? (
                          <span className="inline-flex items-center rounded-sm bg-amber-50 px-1.5 py-0.5 text-[10px] font-bold text-amber-800 ring-1 ring-inset ring-amber-600/20">
                            HUMAN REVIEW
                          </span>
                        ) : (
                          <span className="inline-flex items-center rounded-sm bg-stone-100 px-1.5 py-0.5 text-[10px] font-bold text-stone-600">
                            UNANALYZED
                          </span>
                        )}
                      </td>
                      <td className="px-4 py-3 text-stone-500 font-medium">
                        {caseItem.deadlineLabel === "CRITICAL" ? (
                          <span className="font-bold text-red-600">CRITICAL</span>
                        ) : (
                          caseItem.deadlineLabel
                        )}
                      </td>
                      <td className="px-4 py-3 text-right">
                        {caseItem.actionType === "ANALYZE" ? (
                          <button
                            onClick={() => handleAnalyze(caseItem.dispute_id)}
                            disabled={analyzingId === caseItem.dispute_id}
                            className="inline-flex items-center justify-center px-3 py-1.5 text-xs font-semibold rounded-md bg-stone-900 text-white hover:bg-stone-800 disabled:opacity-50 transition-colors shadow-2xs cursor-pointer"
                          >
                            {analyzingId === caseItem.dispute_id ? "Starting..." : "Analyze"}
                          </button>
                        ) : (
                          <Link
                            href={caseItem.actionHref}
                            className="inline-flex items-center justify-center px-3 py-1.5 text-xs font-semibold rounded-md bg-amber-600 text-white hover:bg-amber-700 transition-colors shadow-2xs"
                          >
                            Review
                          </Link>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="p-8 text-center text-stone-400 text-xs font-medium">
              No disputes requiring immediate attention.
            </div>
          )}
        </div>
      </section>

    </div>
  );
}
