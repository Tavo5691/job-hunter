import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  turbopack: {
    // Point to the monorepo root so Next.js resolves workspace packages correctly
    root: path.resolve(__dirname, "../.."),
  },
};

export default nextConfig;
