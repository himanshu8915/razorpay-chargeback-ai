import React from "react";
import { useQuery } from "@tanstack/react-query";
import axios from "axios";
import { useMerchant } from "@/app/MerchantContext";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Legend } from "recharts";
import { formatCurrency } from "@/utils/formatters";

const COLORS = {
  CONTEST: "#4f46e5",
  REVIEW: "#f59e0b",
  ACCEPT: "#9ca3af"
};

export default function AnalyticsPanel() {
  const { activeMerchantId } = useMerchant();

  const { data, isLoading } = useQuery({
    queryKey: ["dashboard-analytics", activeMerchantId],
    queryFn: async () => {
      if (!activeMerchantId) return null;
      const res = await axios.get(`/api/v1/dashboard/analytics?merchant_id=${activeMerchantId}`);
      return res.data;
    },
    enabled: !!activeMerchantId,
  });

  if (isLoading) {
    return <div className="h-64 bg-gray-50 animate-pulse rounded-lg border border-gray-100"></div>;
  }

  if (!data) return null;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      
      {/* Dispute Distribution */}
      <div>
        <h3 className="text-sm font-semibold text-gray-700 mb-4">Dispute Distribution</h3>
        <div className="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data.dispute_distribution}
                cx="50%"
                cy="50%"
                innerRadius={50}
                outerRadius={70}
                paddingAngle={2}
                dataKey="value"
              >
                {data.dispute_distribution.map((entry: any, index: number) => (
                  <Cell key={`cell-${index}`} fill={COLORS[entry.name as keyof typeof COLORS] || "#gray"} />
                ))}
              </Pie>
              <Tooltip 
                formatter={(value: any) => [value, "Cases"]}
              />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Value by Type */}
      <div>
        <h3 className="text-sm font-semibold text-gray-700 mb-4">Value by Dispute Type</h3>
        <div className="h-48">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data.type_distribution}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} />
              <XAxis dataKey="name" tick={{fontSize: 10}} interval={0} angle={-30} textAnchor="end" height={60} />
              <YAxis 
                tickFormatter={(value) => `₹${(value / 1000).toFixed(0)}k`} 
                width={60}
                tick={{fontSize: 10}}
              />
              <Tooltip 
                formatter={(value: any) => [formatCurrency(value), "Exposure"]}
                cursor={{fill: "#f3f4f6"}}
              />
              <Bar dataKey="value" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

    </div>
  );
}
