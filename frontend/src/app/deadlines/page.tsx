"use client";

import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import { useMerchant } from "@/app/MerchantContext";
import { formatCurrency, formatDate } from "@/utils/formatters";
import { Clock, AlertTriangle } from "lucide-react";
import Link from "next/link";

export default function DeadlinesPage() {
  const { activeMerchantId } = useMerchant();

  const { data: deadlines, isLoading: deadlinesLoading } = useQuery({
    queryKey: ["dashboard-deadlines", activeMerchantId],
    queryFn: async () => {
      if (!activeMerchantId) return null;
      const res = await axios.get(`/api/v1/dashboard/deadlines?merchant_id=${activeMerchantId}`);
      return res.data;
    },
    enabled: !!activeMerchantId,
  });

  const { data: cases, isLoading: casesLoading } = useQuery({
    queryKey: ["disputes-urgent", activeMerchantId],
    queryFn: async () => {
      if (!activeMerchantId) return null;
      const res = await axios.get(
        `/api/v1/disputes?merchant_id=${activeMerchantId}&sort_by=deadline&sort_desc=false&size=15`
      );
      return res.data;
    },
    enabled: !!activeMerchantId,
  });

  if (!activeMerchantId) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-gray-500">Please select a merchant.</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="sm:flex sm:items-center">
        <div className="sm:flex-auto">
          <h1 className="text-2xl font-bold leading-7 text-gray-900 sm:truncate sm:text-3xl sm:tracking-tight">
            Deadline Command Center
          </h1>
          <p className="mt-2 text-sm text-gray-700">Urgency overview and immediate action required cases.</p>
        </div>
      </div>

      {deadlinesLoading ? (
        <div className="h-48 bg-gray-100 animate-pulse rounded-lg"></div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-red-50 p-6 rounded-lg border border-red-200">
            <h3 className="text-red-800 font-bold mb-2 flex items-center">
              <span className="w-3 h-3 rounded-full bg-red-600 mr-2 animate-pulse"></span>
              Under 12 Hours
            </h3>
            <p className="text-3xl font-black text-red-900">{deadlines?.under_12h?.count || 0}</p>
            <p className="text-sm text-red-700 mt-1 font-medium">{formatCurrency(deadlines?.under_12h?.value || 0)} Exposure</p>
          </div>
          
          <div className="bg-orange-50 p-6 rounded-lg border border-orange-200">
            <h3 className="text-orange-800 font-bold mb-2 flex items-center">
              <span className="w-3 h-3 rounded-full bg-orange-500 mr-2"></span>
              12 - 24 Hours
            </h3>
            <p className="text-3xl font-black text-orange-900">{deadlines?.under_24h?.count || 0}</p>
            <p className="text-sm text-orange-700 mt-1 font-medium">{formatCurrency(deadlines?.under_24h?.value || 0)} Exposure</p>
          </div>

          <div className="bg-blue-50 p-6 rounded-lg border border-blue-200">
            <h3 className="text-blue-800 font-bold mb-2 flex items-center">
              <span className="w-3 h-3 rounded-full bg-blue-500 mr-2"></span>
              Next 48 Hours
            </h3>
            <p className="text-3xl font-black text-blue-900">{deadlines?.next_2_days?.count || 0}</p>
            <p className="text-sm text-blue-700 mt-1 font-medium">{formatCurrency(deadlines?.next_2_days?.value || 0)} Exposure</p>
          </div>
          
          <div className="bg-gray-50 p-6 rounded-lg border border-gray-200">
            <h3 className="text-gray-800 font-bold mb-2 flex items-center">
              <span className="w-3 h-3 rounded-full bg-gray-400 mr-2"></span>
              Later
            </h3>
            <p className="text-3xl font-black text-gray-900">{deadlines?.later?.count || 0}</p>
            <p className="text-sm text-gray-600 mt-1 font-medium">{formatCurrency(deadlines?.later?.value || 0)} Exposure</p>
          </div>
        </div>
      )}

      <h2 className="text-lg font-bold text-gray-900 mt-8 mb-4 flex items-center">
        <Clock className="h-5 w-5 mr-2 text-gray-500" />
        Most Urgent Cases
      </h2>

      <div className="bg-white shadow-sm ring-1 ring-gray-900/5 sm:rounded-xl overflow-hidden">
        {casesLoading ? (
           <div className="p-10 text-center animate-pulse">Loading urgent cases...</div>
        ) : (
          <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th scope="col" className="py-3.5 pl-4 pr-3 text-left text-sm font-semibold text-gray-900 sm:pl-6">Case ID</th>
                  <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Deadline</th>
                  <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Time Remaining</th>
                  <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Amount</th>
                  <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">Recommended Action</th>
                  <th scope="col" className="relative py-3.5 pl-3 pr-4 sm:pr-6">
                    <span className="sr-only">Action</span>
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 bg-white">
                {cases?.items?.map((item: any) => {
                  const deadlineDate = new Date(item.deadline);
                  const now = new Date();
                  const diffHours = (deadlineDate.getTime() - now.getTime()) / (1000 * 60 * 60);
                  
                  let colorClass = "text-gray-500";
                  if (diffHours < 12) colorClass = "text-red-600 font-bold";
                  else if (diffHours < 24) colorClass = "text-orange-600 font-bold";
                  
                  return (
                  <tr key={item.dispute_id} className="hover:bg-gray-50">
                    <td className="whitespace-nowrap py-4 pl-4 pr-3 text-sm font-medium text-gray-900 sm:pl-6">
                      {item.dispute_id}
                    </td>
                    <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                      {formatDate(item.deadline)}
                    </td>
                    <td className={`whitespace-nowrap px-3 py-4 text-sm ${colorClass}`}>
                      {diffHours > 0 ? `${diffHours.toFixed(1)} hrs` : "OVERDUE"}
                    </td>
                    <td className="whitespace-nowrap px-3 py-4 text-sm font-semibold text-gray-900">
                      {formatCurrency(item.dispute_amount)}
                    </td>
                    <td className="whitespace-nowrap px-3 py-4 text-sm">
                      <span className={`inline-flex items-center rounded-md px-2 py-1 text-xs font-medium ring-1 ring-inset ${
                        item.decision === 'CONTEST' ? 'bg-indigo-50 text-indigo-700 ring-indigo-600/20' : 
                        item.decision === 'REVIEW' ? 'bg-amber-50 text-amber-700 ring-amber-600/20' : 
                        'bg-gray-50 text-gray-600 ring-gray-500/10'
                      }`}>
                        {item.decision}
                      </span>
                    </td>
                    <td className="relative whitespace-nowrap py-4 pl-3 pr-4 text-right text-sm font-medium sm:pr-6">
                      <Link href={`/case/${item.dispute_id}`} className="text-blue-600 hover:text-blue-900">
                        View<span className="sr-only">, {item.dispute_id}</span>
                      </Link>
                    </td>
                  </tr>
                  );
                })}
              </tbody>
            </table>
        )}
      </div>
    </div>
  );
}
