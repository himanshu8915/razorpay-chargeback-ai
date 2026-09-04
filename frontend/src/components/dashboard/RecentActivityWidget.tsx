import React from "react";
import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import { useMerchant } from "@/app/MerchantContext";
import { formatDistanceToNow } from "date-fns";
import { CheckCircle2, ShieldAlert } from "lucide-react";

export default function RecentActivityWidget() {
  const { activeMerchantId } = useMerchant();

  const { data, isLoading } = useQuery({
    queryKey: ["dashboard-activity", activeMerchantId],
    queryFn: async () => {
      if (!activeMerchantId) return null;
      const res = await axios.get(`/api/v1/dashboard/activity?merchant_id=${activeMerchantId}`);
      return res.data;
    },
    enabled: !!activeMerchantId,
  });

  if (isLoading) {
    return <div className="space-y-4 animate-pulse">
      {[1, 2, 3].map(i => <div key={i} className="h-12 bg-gray-100 rounded"></div>)}
    </div>;
  }

  if (!data || data.length === 0) {
    return <p className="text-sm text-gray-500 italic">No recent activity.</p>;
  }

  return (
    <ul className="space-y-4">
      {data.map((item: any) => (
        <li key={item.id} className="flex items-start">
          <div className="flex-shrink-0 mt-0.5">
            {item.type === "DECISION_READY" ? (
              <CheckCircle2 className="h-5 w-5 text-emerald-500" />
            ) : (
              <ShieldAlert className="h-5 w-5 text-blue-500" />
            )}
          </div>
          <div className="ml-3 flex-1">
            <p className="text-sm font-medium text-gray-900">{item.title}</p>
            {item.timestamp && (
              <p className="text-xs text-gray-500 mt-1">
                {formatDistanceToNow(new Date(item.timestamp), { addSuffix: true })}
              </p>
            )}
          </div>
        </li>
      ))}
    </ul>
  );
}
