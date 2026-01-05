/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/analytics/dashboard',
        destination: 'http://ai_service:8000/analytics/dashboard',
      },
      {
        source: '/api/analytics/sessions_list',
        destination: 'http://ai_service:8000/analytics/sessions_list',
      },
      {
        source: '/api/:path*',
        destination: 'http://backend:5000/api/:path*',
      },
    ];
  },
};

module.exports = nextConfig;
