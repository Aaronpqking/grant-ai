/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone',
  eslint: {
    // Disable ESLint during production builds
    ignoreDuringBuilds: true,
  },
  images: {
    domains: [
      'localhost',
      'vercel.app',
      'vercel.com'
      // Add any other domains you need to load images from
    ],
  },
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block',
          },
        ],
      },
    ];
  },
  // Uncomment if you need API routes to be proxied to your backend
  // async rewrites() {
  //   return [
  //     {
  //       source: '/api/:path*',
  //       destination: process.env.NEXT_PUBLIC_API_URL + '/:path*',
  //     },
  //   ];
  // },
};

module.exports = nextConfig; 