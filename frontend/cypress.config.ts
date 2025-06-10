import { defineConfig } from 'cypress';

if (!process.env.VITE_FRONTEND_PORT) {
  throw new Error('VITE_FRONTEND_PORT environment variable is not set');
}

if (!process.env.VITE_API_URL) {
  throw new Error('VITE_API_URL environment variable is not set');
}

export default defineConfig({
  e2e: {
    baseUrl: `http://localhost:${process.env.VITE_FRONTEND_PORT}`,
    supportFile: 'cypress/support/e2e.ts',
    specPattern: 'cypress/e2e/**/*.cy.{js,jsx,ts,tsx}',
    video: false,
    screenshotOnRunFailure: false,
    defaultCommandTimeout: 10000,
    requestTimeout: 10000,
    responseTimeout: 10000,
    pageLoadTimeout: 30000,
    env: {
      apiUrl: process.env.VITE_API_URL,
      apiVersion: process.env.VITE_API_VERSION
    }
  },
}); 