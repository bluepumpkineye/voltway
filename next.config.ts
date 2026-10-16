import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  transpilePackages: ['three'],
  // The site used to have a vehicle list, a page per car and a comparison table; the showroom is now the whole site.
  async redirects() {
    return [
      { source: '/vehicles', destination: '/', permanent: true },
      { source: '/vehicles/:slug', destination: '/showroom/:slug', permanent: true },
      { source: '/compare', destination: '/', permanent: true },
    ];
  },
};

export default nextConfig;
