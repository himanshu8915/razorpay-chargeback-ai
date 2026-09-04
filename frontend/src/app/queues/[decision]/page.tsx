"use client";

import React, { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import { useMerchant } from "@/app/MerchantContext";
import { formatCurrency, formatDate } from "@/utils/formatters";
import { ChevronLeft, ChevronRight, Search } from "lucide-react";
import Link from "next/link";

export default function QueuePage() {
  const { decision } = useParams();
  const { activeMerchantId } = useMerchant();
  const router = useRouter();
  const [page, setPage] = useState(1);
  const size = 25;
  
  const [sortBy, setSortBy] = useState("");
  const [sortDesc, setSortDesc] = useState(true);
  const [minAmount, setMinAmount] = useState("");
  const [maxAmount, setMaxAmount] = useState("");

  const decisionUpper = (decision as string).toUpperCase();

  const { data, isLoading } = useQuery({
    queryKey: ["disputes", activeMerchantId, decisionUpper, page, sortBy, sortDesc, minAmount, maxAmount],
    queryFn: async () => {
      if (!activeMerchantId) return null;
      let url = "";
      if (decisionUpper === "UNANALYZED") {
        url = `/api/v1/disputes/unanalyzed?merchant_id=${activeMerchantId}&page=${page}&size=${size}`;
      } else {
        url = `/api/v1/disputes?merchant_id=${activeMerchantId}&decision=${decisionUpper}&page=${page}&size=${size}`;
        if (sortBy) url += `&sort_by=${sortBy}&sort_desc=${sortDesc}`;
        if (minAmount) url += `&min_amount=${minAmount}`;
        if (maxAmount) url += `&max_amount=${maxAmount}`;
      }
      const res = await axios.get(url);
      return res.data;
    },
    enabled: !!activeMerchantId,
  });

  const getHeaderInfo = () => {
    switch (decisionUpper) {
      case "UNANALYZED":
        return {
          title: "Unanalyzed Disputes",
          description: "New disputes waiting for AI assessment and decision generation.",
          color: "bg-blue-50 text-blue-700 ring-blue-700/10",
        };
      case "CONTEST":
        return {
          title: "Contest / Fight",
          description: "Cases with a positive expected value. Action required to recover funds.",
          color: "bg-indigo-50 text-indigo-700 ring-indigo-700/10",
        };
      case "REVIEW":
        return {
          title: "Human Review",
          description: "Complex cases requiring human attention before submission.",
          color: "bg-amber-50 text-amber-700 ring-amber-700/10",
        };
      case "ACCEPT":
        return {
          title: "Accept / No Contest",
          description: "Cases where the evidence or economics do not justify a fight.",
          color: "bg-gray-50 text-gray-700 ring-gray-700/10",
        };
      default:
        return { title: "Queue", description: "", color: "" };
    }
  };

  const info = getHeaderInfo();

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
            {info.title}
          </h1>
          <p className="mt-2 text-sm text-gray-700">{info.description}</p>
        </div>
      </div>

      <div className="bg-white shadow-sm ring-1 ring-gray-900/5 sm:rounded-xl overflow-hidden mb-6 p-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Min Amount</label>
            <input 
              type="number" 
              value={minAmount} 
              onChange={e => setMinAmount(e.target.value)} 
              className="block w-full rounded-md border-0 py-1.5 text-gray-900 ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-blue-600 sm:text-sm sm:leading-6" 
              placeholder="e.g. 100" 
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Max Amount</label>
            <input 
              type="number" 
              value={maxAmount} 
              onChange={e => setMaxAmount(e.target.value)} 
              className="block w-full rounded-md border-0 py-1.5 text-gray-900 ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-blue-600 sm:text-sm sm:leading-6" 
              placeholder="e.g. 5000" 
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Sort By</label>
            <select 
              value={sortBy} 
              onChange={e => setSortBy(e.target.value)}
              className="block w-full rounded-md border-0 py-1.5 text-gray-900 ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-blue-600 sm:text-sm sm:leading-6"
            >
              <option value="">Default (Priority)</option>
              <option value="amount">Dispute Amount</option>
              <option value="net_value">Net Expected Value</option>
              <option value="deadline">Deadline</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Sort Order</label>
            <select 
              value={sortDesc ? "desc" : "asc"} 
              onChange={e => setSortDesc(e.target.value === "desc")}
              className="block w-full rounded-md border-0 py-1.5 text-gray-900 ring-1 ring-inset ring-gray-300 focus:ring-2 focus:ring-inset focus:ring-blue-600 sm:text-sm sm:leading-6"
              disabled={!sortBy}
            >
              <option value="desc">High to Low / Newest</option>
              <option value="asc">Low to High / Oldest</option>
            </select>
          </div>
        </div>
      </div>

      <div className="bg-white shadow-sm ring-1 ring-gray-900/5 sm:rounded-xl overflow-hidden">
        {isLoading ? (
          <div className="p-10 text-center animate-pulse space-y-4">
            <div className="h-4 bg-gray-200 rounded w-1/4 mx-auto"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2 mx-auto"></div>
            <div className="h-4 bg-gray-200 rounded w-1/3 mx-auto"></div>
          </div>
        ) : data?.items?.length === 0 ? (
          <div className="p-12 text-center">
            <h3 className="mt-2 text-sm font-semibold text-gray-900">You're all caught up.</h3>
            <p className="mt-1 text-sm text-gray-500">No {decisionUpper.toLowerCase()} cases are currently available.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th scope="col" className="py-3.5 pl-4 pr-3 text-left text-sm font-semibold text-gray-900 sm:pl-6">
                    Case ID
                  </th>
                  <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                    Amount
                  </th>
                  <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                    Type
                  </th>
                  <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                    Net Expected Value
                  </th>
                  <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                    Deadline
                  </th>
                  <th scope="col" className="px-3 py-3.5 text-left text-sm font-semibold text-gray-900">
                    Status
                  </th>
                  <th scope="col" className="relative py-3.5 pl-3 pr-4 sm:pr-6">
                    <span className="sr-only">Action</span>
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 bg-white">
                {data?.items.map((item: any) => (
                  <tr key={item.dispute_id} className="hover:bg-gray-50 cursor-pointer" onClick={() => router.push(`/case/${item.dispute_id}`)}>
                    <td className="whitespace-nowrap py-4 pl-4 pr-3 text-sm font-medium text-gray-900 sm:pl-6">
                      {item.dispute_id}
                    </td>
                    <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                      {formatCurrency(item.dispute_amount)}
                    </td>
                    <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                      <span className="inline-flex items-center rounded-md bg-gray-50 px-2 py-1 text-xs font-medium text-gray-600 ring-1 ring-inset ring-gray-500/10">
                        {item.dispute_type || "CHARGEBACK"}
                      </span>
                    </td>
                    <td className="whitespace-nowrap px-3 py-4 text-sm font-semibold text-gray-900">
                      {item.net_expected_value !== undefined && item.net_expected_value !== null ? formatCurrency(item.net_expected_value) : "-"}
                    </td>
                    <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                      {item.deadline ? formatDate(item.deadline) : "N/A"}
                    </td>
                    <td className="whitespace-nowrap px-3 py-4 text-sm text-gray-500">
                      <span className={`inline-flex items-center rounded-md px-2 py-1 text-xs font-medium ring-1 ring-inset ${
                        item.workflow_status === 'UNANALYZED' ? 'bg-blue-50 text-blue-700 ring-blue-600/20' : 'bg-gray-50 text-gray-600 ring-gray-500/10'
                      }`}>
                        {item.workflow_status}
                      </span>
                    </td>
                    <td className="relative whitespace-nowrap py-4 pl-3 pr-4 text-right text-sm font-medium sm:pr-6">
                      <Link href={`/case/${item.dispute_id}`} className="text-indigo-600 hover:text-indigo-900 font-bold bg-indigo-50 px-3 py-1.5 rounded-lg">
                        {decisionUpper === "UNANALYZED" ? "Run Analysis" : "View Details"}
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            
            {/* Pagination */}
            <div className="flex items-center justify-between border-t border-gray-200 bg-white px-4 py-3 sm:px-6">
              <div className="flex flex-1 justify-between sm:hidden">
                <button
                  onClick={() => setPage(p => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="relative inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                >
                  Previous
                </button>
                <button
                  onClick={() => setPage(p => p + 1)}
                  disabled={page * size >= (data?.total || 0)}
                  className="relative ml-3 inline-flex items-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                >
                  Next
                </button>
              </div>
              <div className="hidden sm:flex sm:flex-1 sm:items-center sm:justify-between">
                <div>
                  <p className="text-sm text-gray-700">
                    Showing <span className="font-medium">{(page - 1) * size + 1}</span> to <span className="font-medium">{Math.min(page * size, data?.total || 0)}</span> of{" "}
                    <span className="font-medium">{data?.total || 0}</span> results
                  </p>
                </div>
                <div>
                  <nav className="isolate inline-flex -space-x-px rounded-md shadow-sm" aria-label="Pagination">
                    <button
                      onClick={() => setPage(p => Math.max(1, p - 1))}
                      disabled={page === 1}
                      className="relative inline-flex items-center rounded-l-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0 disabled:opacity-50"
                    >
                      <span className="sr-only">Previous</span>
                      <ChevronLeft className="h-5 w-5" aria-hidden="true" />
                    </button>
                    <button
                      onClick={() => setPage(p => p + 1)}
                      disabled={page * size >= (data?.total || 0)}
                      className="relative inline-flex items-center rounded-r-md px-2 py-2 text-gray-400 ring-1 ring-inset ring-gray-300 hover:bg-gray-50 focus:z-20 focus:outline-offset-0 disabled:opacity-50"
                    >
                      <span className="sr-only">Next</span>
                      <ChevronRight className="h-5 w-5" aria-hidden="true" />
                    </button>
                  </nav>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
