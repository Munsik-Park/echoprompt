import axiosInstance from './axios';

// 환경 변수 타입 정의
interface ViteEnv {
  VITE_API_URL: string;
  VITE_API_VERSION: string;
}

declare global {
  interface ImportMeta {
    env: ViteEnv;
  }
}

// 환경 변수 가져오기
const getEnvVar = (key: keyof ViteEnv): string => {
  // 테스트 환경 (Node.js)
  if (typeof process !== 'undefined' && process.env) {
    const value = process.env[key];
    if (!value) {
      throw new Error(`Missing required environment variable: ${key}`);
    }
    return value;
  }
  // 브라우저 환경 (Vite)
  if (typeof import.meta !== 'undefined' && import.meta.env) {
    const value = import.meta.env[key];
    if (!value) {
      throw new Error(`Missing required environment variable: ${key}`);
    }
    return value;
  }
  throw new Error('Environment variables are not available');
};

// 필수 환경 변수 가져오기
const API_URL = getEnvVar('VITE_API_URL');
const API_VERSION = getEnvVar('VITE_API_VERSION');

// API 클라이언트 생성
const api = axiosInstance.create({
  baseURL: `${API_URL}/api/${API_VERSION}`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 응답 인터셉터 설정
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// API 클라이언트 재사용
export default api;
