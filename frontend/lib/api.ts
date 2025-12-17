import axios from 'axios';

let API_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:5001/api';

// --- Start of Fix ---
// Ensure the API_URL is always a valid HTTP/HTTPS URL when running in the browser
if (typeof window !== 'undefined' && API_URL.startsWith('backend:')) {
  console.warn(`Frontend: Correcting malformed NEXT_PUBLIC_BACKEND_URL from '${API_URL}' to 'http://localhost:5001/api' for browser access.`);
  API_URL = 'http://localhost:5001'; // Fallback to localhost for client-side
}
// --- End of Fix ---

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
