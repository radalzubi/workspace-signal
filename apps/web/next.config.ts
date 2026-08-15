import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  agentRules: false,
  ...(process.env.VERCEL ? {} : { output: "standalone" }),
  poweredByHeader: false,
  reactStrictMode: true,
};

export default nextConfig;
