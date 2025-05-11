import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  output: "standalone",
  images: {
    unoptimized: true, // Cho phép tất cả các host, không tối ưu hóa
    // remotePatterns không còn cần thiết khi unoptimized là true
  },
};

export default nextConfig;
