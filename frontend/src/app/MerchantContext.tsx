"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import axios from "axios";

interface MerchantInfo {
  merchant_id: string;
  merchant_name: string;
  statistics: any;
  total_demo_cases: number;
}

interface MerchantContextType {
  activeMerchantId: string | null;
  setActiveMerchantId: (id: string) => void;
  merchants: MerchantInfo[];
  loading: boolean;
}

const MerchantContext = createContext<MerchantContextType | undefined>(undefined);

export function MerchantProvider({ children }: { children: React.ReactNode }) {
  const [activeMerchantId, setActiveMerchantId] = useState<string | null>(null);
  const [merchants, setMerchants] = useState<MerchantInfo[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Load manifest
    axios.get("/api/v1/merchants/portfolio")
      .then(res => {
        const manifest = res.data;
        if (manifest && manifest.merchants) {
          setMerchants(manifest.merchants);
          if (manifest.merchants.length > 0) {
            setActiveMerchantId(manifest.merchants[0].merchant_id);
          }
        }
      })
      .catch(err => {
        console.error("Failed to load merchant manifest", err);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  return (
    <MerchantContext.Provider value={{ activeMerchantId, setActiveMerchantId, merchants, loading }}>
      {children}
    </MerchantContext.Provider>
  );
}

export function useMerchant() {
  const context = useContext(MerchantContext);
  if (context === undefined) {
    throw new Error("useMerchant must be used within a MerchantProvider");
  }
  return context;
}
