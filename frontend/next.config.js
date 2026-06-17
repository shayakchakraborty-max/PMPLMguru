/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: "standalone", // self-contained server bundle for containerized AWS deploy
};

module.exports = nextConfig;
