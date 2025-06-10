import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
  // 환경 변수 로드
  const env = loadEnv(mode, process.cwd(), '');
  
  // 필수 환경 변수 확인
  if (!env.VITE_FRONTEND_HOST || !env.VITE_FRONTEND_PORT) {
    throw new Error('VITE_FRONTEND_HOST and VITE_FRONTEND_PORT environment variables are required');
  }

  return {
    plugins: [react()],
    server: {
      port: parseInt(env.VITE_FRONTEND_PORT, 10),
    },
  };
});
