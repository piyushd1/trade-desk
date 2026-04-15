/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Standalone output: produces a minimal self-contained server bundle at
  // .next/standalone/ with its own server.js and a pruned node_modules.
  // Required by deployment/docker/Dockerfile.frontend which copies from
  // .next/standalone to build a slim runtime image.
  // See https://nextjs.org/docs/app/api-reference/config/next-config-js/output
  output: 'standalone',
  // NOTE: API routing is handled by `tailscale serve` on the Pi host:
  //   /api/*  -> backend (localhost:8000)
  //   /       -> frontend (localhost:3001)
  // No Next.js rewrites needed. `NEXT_PUBLIC_API_URL=/api/v1` is a relative
  // URL that the browser resolves against the current page origin.
};

module.exports = nextConfig;
