"use client";

import React, { useState } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MerchantProvider } from "./MerchantContext";

export default function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => new QueryClient());

  return (
    <QueryClientProvider client={queryClient}>
      <MerchantProvider>
        {children}
      </MerchantProvider>
    </QueryClientProvider>
  );
}
