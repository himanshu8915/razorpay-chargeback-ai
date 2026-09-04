import React from "react";
import { formatCurrency } from "@/utils/formatters";
import { ArrowDown } from "lucide-react";

export default function RecoveryOutlook({ metrics, deadlines }: { metrics: any, deadlines: any }) {
  const total = metrics?.total_disputed_value || 0;
  const recoverable = metrics?.recoverable_opportunity || 0;
  const expected = metrics?.expected_recovery || 0;
  const atRisk = (deadlines?.under_12h?.value || 0) + (deadlines?.under_24h?.value || 0);

  const getWidth = (val: number) => {
    if (!total || total === 0) return "0%";
    return `${Math.max(5, (val / total) * 100)}%`;
  };

  return (
    <div className="bg-white shadow rounded-lg border border-gray-200 p-6">
      <h2 className="text-lg font-medium text-gray-900 mb-6">Recovery Outlook</h2>
      
      <div className="space-y-4">
        {/* Total */}
        <div>
          <div className="flex justify-between items-end mb-1">
            <span className="text-sm font-semibold text-gray-700">Total Disputed Value</span>
            <span className="text-lg font-bold text-gray-900">{formatCurrency(total)}</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-3">
            <div className="bg-gray-400 h-3 rounded-full" style={{ width: "100%" }}></div>
          </div>
        </div>

        <div className="flex justify-center -my-2">
          <ArrowDown className="h-5 w-5 text-gray-300" />
        </div>

        {/* Recoverable */}
        <div>
          <div className="flex justify-between items-end mb-1">
            <span className="text-sm font-semibold text-blue-700">Recoverable Opportunity</span>
            <span className="text-lg font-bold text-blue-800">{formatCurrency(recoverable)}</span>
          </div>
          <div className="w-full bg-gray-100 rounded-full h-3">
            <div className="bg-blue-500 h-3 rounded-full transition-all duration-1000" style={{ width: getWidth(recoverable) }}></div>
          </div>
          <p className="text-xs text-gray-500 mt-1 text-right">Potentially valid to contest</p>
        </div>

        <div className="flex justify-center -my-2">
          <ArrowDown className="h-5 w-5 text-blue-200" />
        </div>

        {/* Expected */}
        <div>
          <div className="flex justify-between items-end mb-1">
            <span className="text-sm font-semibold text-emerald-700">Expected Recovery</span>
            <span className="text-lg font-bold text-emerald-800">{formatCurrency(expected)}</span>
          </div>
          <div className="w-full bg-gray-100 rounded-full h-3">
            <div className="bg-emerald-500 h-3 rounded-full transition-all duration-1000" style={{ width: getWidth(expected) }}></div>
          </div>
          <p className="text-xs text-gray-500 mt-1 text-right">Adjusted for win probability & fight cost</p>
        </div>

        <div className="flex justify-center -my-2">
          <ArrowDown className="h-5 w-5 text-emerald-200" />
        </div>

        {/* At Risk */}
        <div>
          <div className="flex justify-between items-end mb-1">
            <span className="text-sm font-semibold text-red-700">At-Risk Value (&lt; 24h Deadline)</span>
            <span className="text-lg font-bold text-red-800">{formatCurrency(atRisk)}</span>
          </div>
          <div className="w-full bg-gray-100 rounded-full h-3">
            <div className="bg-red-500 h-3 rounded-full transition-all duration-1000" style={{ width: getWidth(atRisk) }}></div>
          </div>
          <p className="text-xs text-gray-500 mt-1 text-right">Immediate action required to preserve recovery</p>
        </div>
      </div>
    </div>
  );
}
