import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Allow external API calls
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${process.env.NEXT_PUBLIC_API_BASE_URL}/api/:path*`,
      },
    ];
  },

};

export default nextConfig;
