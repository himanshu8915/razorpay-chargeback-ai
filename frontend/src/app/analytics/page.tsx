'use client';
import Shell from "@/components/layout/Shell";
import AnalyticsPanel from "@/components/dashboard/AnalyticsPanel";

export default function AnalyticsPage() {
  return (
    <Shell>
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-neutral-900 dark:text-neutral-100">
            Portfolio Analytics
          </h1>
          <p className="text-sm text-neutral-500 dark:text-neutral-400 mt-1">
            Comprehensive portfolio distribution, dispute types, and financial exposure across merchants.
          </p>
        </div>

        <AnalyticsPanel />
      </div>
    </Shell>
  );
}
