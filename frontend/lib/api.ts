import axios from 'axios';

let API_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:5001/api';

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
