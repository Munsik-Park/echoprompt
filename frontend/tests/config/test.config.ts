export interface TestConfig {
  baseUrl: string;
  apiVersion: string;
  timeout: number;
  retries: number;
  screenshotOnFailure: boolean;
  videoRecording: boolean;
  logLevel: 'debug' | 'info' | 'warn' | 'error';
}

const defaultConfig: TestConfig = {
  baseUrl: process.env.VITE_FRONTEND_URL || 'http://localhost:3000',
  apiVersion: process.env.VITE_API_VERSION || 'v1',
  timeout: 30000,
  retries: 2,
  screenshotOnFailure: true,
  videoRecording: false,
  logLevel: 'info'
};

export const testConfig: TestConfig = {
  ...defaultConfig,
  ...(process.env.TEST_CONFIG ? JSON.parse(process.env.TEST_CONFIG) : {})
}; 