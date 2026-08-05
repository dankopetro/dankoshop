import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "**.railway.app",
      },
      {
        protocol: "https",
        hostname: "**.vercel.app",
      },
      {
        protocol: "http",
        hostname: "localhost",
      },
      {
        protocol: "https",
        hostname: "**.amazonaws.com",
      },
    ],
    unoptimized: true,
  },
};

export default nextConfig;