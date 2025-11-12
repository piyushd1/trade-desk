/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  // API calls go through Nginx proxy, no rewrite needed
};

module.exports = nextConfig;

