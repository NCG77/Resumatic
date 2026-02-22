import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // API routes now handle proxying to Django backend
  // See app/api/tailor-resume/route.ts and app/api/upload-resume/route.ts
};

export default nextConfig;
