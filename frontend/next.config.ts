import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // API routes now handle proxying to Django backend
  // See app/api/tailor-resume/route.ts and app/api/upload-resume/route.ts
  turbopack: {
    root: __dirname,
  },
};

export default nextConfig;
