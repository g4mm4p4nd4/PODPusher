import { defineConfig } from '@playwright/test';

export default defineConfig({
webServer: {
    command: 'npm run dev --prefix client',
    port: 3000,
    timeout: 120 * 1000,
    reuseExistingServer: true,
  },
  testDir: './tests/e2e',
  use: {
    baseURL: 'http://localhost:3000',
    headless: true,
  },
});
