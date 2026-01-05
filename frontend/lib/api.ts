import axios from 'axios';

let API_URL = process.env.NEXT_PUBLIC_BACKEND_URL || '/api';

// Prefer same-origin `/api` in the browser for local/dev to ensure auth cookies are sent.
if (typeof window !== 'undefined') {
  const isLocalHost =
    API_URL.startsWith('backend:') ||
    API_URL.includes('localhost:5001') ||
    API_URL.includes('127.0.0.1:5001');

  if (isLocalHost) {
    console.warn(`Frontend: Using same-origin '/api' for '${API_URL}' to preserve auth cookies.`);
    API_URL = '/api';
  }
}

// Normalize URL: remove trailing slash
API_URL = API_URL.replace(/\/$/, "");

// Ensure it ends with /api (unless it's already there)
// This fixes the issue where the env var is http://localhost:5001 but endpoints expect /api/...
if (!API_URL.endsWith('/api')) {
  API_URL += '/api';
}

const api = axios.create({
  baseURL: API_URL,
  withCredentials: true, // Important for cookies
  headers: {
    'Content-Type': 'application/json',
  },
});

export default api;
