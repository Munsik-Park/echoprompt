import axios from 'axios';

if (!import.meta.env.VITE_API_VERSION) {
  throw new Error('VITE_API_VERSION environment variable is not set');
}

const API_VERSION = import.meta.env.VITE_API_VERSION;
const API_PATH = `/api/${API_VERSION}`;

const axiosInstance = axios.create({
  baseURL: API_PATH,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 응답 인터셉터 추가
axiosInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

export default axiosInstance; 