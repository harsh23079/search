/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: 'http',
        hostname: 'localhost',
        port: '8000',
        pathname: '/**',
      },
      {
        protocol: 'https',
        hostname: 'cdn.shopify.com',
        pathname: '/**',
      },
      {
        protocol: 'https',
        hostname: '**.shopifycdn.com',
        pathname: '/**',
      },
      {
        protocol: 'https',
        hostname: '**.amazonaws.com',
        pathname: '/**',
      },
      {
        protocol: 'https',
        hostname: '**.cloudfront.net',
        pathname: '/**',
      },
      {
        protocol: 'https',
        hostname: 'image.goat.com',
        pathname: '/**',
      },
      {
        protocol: 'https',
        hostname: 'cdn1.ethoswatches.com',
        pathname: '/**',
      },
    ],
    // Allow images from any HTTPS domain (unoptimized)
    // Set to true if you need to load images from many unknown domains
    // Note: This disables Next.js image optimization
    unoptimized: false,
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
    ];
  },
};

export default nextConfig;

