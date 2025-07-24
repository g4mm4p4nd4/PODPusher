import { defineConfig } from '@playwright/test';

export default defineConfig({
  webServer: {
    command: 'npm run start --prefix client',
    port: 3000,
    timeout: 120 * 1000,
  },
  testDir: './tests/e2e',
  use: {
    baseURL: 'http://localhost:3000',
    headless: true,
  },
});
