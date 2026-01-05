import axios from 'axios';

const api = axios.create({
  baseURL: 'http://backend:5000/api',
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

export default api;
