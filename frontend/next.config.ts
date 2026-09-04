import type { NextConfig } from "next";

const BACKEND_URL = process.env.NODE_ENV === 'production' ? "http://backend:8000" : "http://localhost:8000";

const nextConfig: NextConfig = {
  output: "standalone",
  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: `${BACKEND_URL}/api/v1/:path*`,
      },
    ];
  },
};

export default nextConfig;
