"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useMerchant } from "@/app/MerchantContext";
import { ShieldAlert } from "lucide-react";

export default function Shell({ children }: { children: React.ReactNode }) {
  const { activeMerchantId, setActiveMerchantId, merchants } = useMerchant();
  const pathname = usePathname();

  return (
    <div className="min-h-screen w-full bg-[#FAF9F6] flex flex-col font-sans">
      {/* Quiet, Professional Top Header */}
      <header className="sticky top-0 z-40 w-full border-b border-stone-200/80 bg-white/95 backdrop-blur-md shadow-xs">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-14">
            
            {/* LEFT: Logo & Brand */}
            <div className="flex items-center">
              <Link href="/" className="flex items-center space-x-2.5 group">
                <div className="w-8 h-8 rounded-lg bg-amber-500/10 flex items-center justify-center border border-amber-500/20 group-hover:border-amber-500/40 transition-colors">
                  <ShieldAlert className="h-4.5 w-4.5 text-amber-600" />
                </div>
                <span className="text-base font-bold text-stone-900 tracking-tight">Chargeback AI</span>
              </Link>
            </div>

            {/* CENTER / MAIN: Primary Navigation (Command Center only) */}
            <div className="flex items-center">
              <Link
                href="/"
                className={`px-3 py-1.5 text-xs font-semibold rounded-md tracking-wide transition-all ${
                  pathname === "/"
                    ? "bg-stone-900 text-white shadow-xs"
                    : "text-stone-600 hover:text-stone-900 hover:bg-stone-100"
                }`}
              >
                Command Center
              </Link>
            </div>

            {/* RIGHT: Active Merchant Selector */}
            <div className="flex items-center space-x-2">
              <span className="text-xs font-medium text-stone-400 hidden sm:inline-block">Active Merchant:</span>
              <select
                value={activeMerchantId || ""}
                onChange={(e) => setActiveMerchantId(e.target.value)}
                className="rounded-md border border-stone-200 py-1 pl-2.5 pr-7 text-xs font-semibold text-stone-800 bg-stone-50 hover:bg-stone-100 focus:ring-1 focus:ring-amber-500 focus:outline-none shadow-2xs cursor-pointer"
              >
                <option value="" disabled>Select Merchant...</option>
                {merchants.map(m => (
                  <option key={m.merchant_id} value={m.merchant_id}>
                    {m.merchant_name} ({m.merchant_id})
                  </option>
                ))}
              </select>
            </div>

          </div>
        </div>
      </header>

      {/* Main Content Area with Sidebar */}
      <div className="flex-1 flex w-full max-w-[1400px] mx-auto">
        {/* Sidebar */}
        <aside className="w-64 border-r border-stone-200/80 bg-[#FAF9F6] hidden md:block flex-shrink-0 py-8 px-6">
          <nav className="space-y-1">
            <div className="text-[10px] font-bold uppercase tracking-widest text-stone-400 mb-3 px-3">
              Overview
            </div>
            <Link
              href="/"
              className={`flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                pathname === "/" ? "bg-stone-200/50 text-stone-900" : "text-stone-600 hover:bg-stone-100 hover:text-stone-900"
              }`}
            >
              Command Center
            </Link>
            
            <div className="text-[10px] font-bold uppercase tracking-widest text-stone-400 mt-8 mb-3 px-3">
              Work Queues
            </div>
            <Link
              href="/queues/unanalyzed"
              className={`flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                pathname === "/queues/unanalyzed" ? "bg-stone-200/50 text-stone-900" : "text-stone-600 hover:bg-stone-100 hover:text-stone-900"
              }`}
            >
              Unanalyzed
            </Link>
            <Link
              href="/queues/review"
              className={`flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                pathname === "/queues/review" ? "bg-amber-100/50 text-amber-900" : "text-stone-600 hover:bg-stone-100 hover:text-stone-900"
              }`}
            >
              Human Review
            </Link>
            <Link
              href="/queues/contest"
              className={`flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                pathname === "/queues/contest" ? "bg-stone-200/50 text-stone-900" : "text-stone-600 hover:bg-stone-100 hover:text-stone-900"
              }`}
            >
              Contest / Fight
            </Link>
            <Link
              href="/queues/accept"
              className={`flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                pathname === "/queues/accept" ? "bg-stone-200/50 text-stone-900" : "text-stone-600 hover:bg-stone-100 hover:text-stone-900"
              }`}
            >
              Accept
            </Link>

            <div className="text-[10px] font-bold uppercase tracking-widest text-stone-400 mt-8 mb-3 px-3">
              Operations
            </div>
            <Link
              href="/deadlines"
              className={`flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                pathname === "/deadlines" ? "bg-red-50 text-red-900" : "text-stone-600 hover:bg-stone-100 hover:text-stone-900"
              }`}
            >
              Deadlines
            </Link>
          </nav>
        </aside>

        {/* Main Content */}
        <main className="flex-1 w-full max-w-5xl px-4 sm:px-6 lg:px-8 py-8 overflow-x-hidden">
          {children}
        </main>
      </div>
    </div>
  );
}
