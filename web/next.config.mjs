/** @type {import('next').NextConfig} */

const nextConfig = {
  typescript: {
    ignoreBuildErrors: false,
  },
  images: {
    unoptimized: true,
  },
  output: 'export',
  distDir: 'dist',
  // FastAPI StaticFiles(html=True) serves <dir>/index.html, not <name>.html
  trailingSlash: true,
}

export default nextConfig
