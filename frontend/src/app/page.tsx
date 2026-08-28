"use client";

import { useEffect, useState } from "react";

type SystemStatus = "checking" | "ready" | "error";

interface ServiceStatus {
  backend: SystemStatus;
  database: SystemStatus;
}

export default function Home() {
  const [status, setStatus] = useState<ServiceStatus>({
    backend: "checking",
    database: "checking",
  });

  useEffect(() => {
    async function checkStatus() {
      try {
        const res = await fetch("/api/v1/ready");
        if (res.ok) {
          const data = await res.json();
          setStatus({
            backend: "ready",
            database: data.database === "ok" ? "ready" : "error",
          });
        } else {
          setStatus({ backend: "ready", database: "error" });
        }
      } catch {
        setStatus({ backend: "error", database: "error" });
      }
    }

    checkStatus();
    const interval = setInterval(checkStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const allReady = status.backend === "ready" && status.database === "ready";

  const icon = (s: SystemStatus) => {
    if (s === "ready") return "✓";
    if (s === "error") return "✗";
    return "○";
  };

  const color = (s: SystemStatus) => {
    if (s === "ready") return "text-emerald-400";
    if (s === "error") return "text-red-400";
    return "text-amber-400";
  };

  return (
    <main className="min-h-screen bg-slate-950 flex items-center justify-center font-mono">
      <div className="border border-slate-700 rounded-lg p-10 w-96 bg-slate-900 shadow-2xl">
        <h1 className="text-slate-100 text-xl font-bold tracking-widest mb-8 text-center">
          CHARGEBACK INTELLIGENCE
        </h1>

        <div className="space-y-3 mb-8">
          <div className="flex justify-between items-center">
            <span className="text-slate-400 text-sm">Backend</span>
            <span className={`text-sm font-bold ${color(status.backend)}`}>
              {icon(status.backend)}
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-slate-400 text-sm">Database</span>
            <span className={`text-sm font-bold ${color(status.database)}`}>
              {icon(status.database)}
            </span>
          </div>
        </div>

        <div
          className={`text-center text-sm font-bold tracking-wider py-2 rounded ${
            allReady
              ? "text-emerald-400 bg-emerald-950"
              : "text-amber-400 bg-amber-950"
          }`}
        >
          {allReady ? "Project Foundation Ready" : "Initializing..."}
        </div>

        <p className="text-slate-600 text-xs text-center mt-6">Phase 0</p>
      </div>
    </main>
  );
}
