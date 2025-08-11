/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    appDir: true,
  },
  output: 'export',
  distDir: 'out',
  images: {
    unoptimized: true
  },
  trailingSlash: true,
  basePath: process.env.NODE_ENV === 'production' ? '' : '',
}

module.exports = nextConfig
