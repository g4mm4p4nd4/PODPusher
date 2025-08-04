import { defineConfig } from '@playwright/test';

export default defineConfig({
  webServer: {
    command: 'npm run build --prefix client && npm run start --prefix client',
    port: 3000,
    timeout: 120 * 1000,
    reuseExistingServer: true,
    env: { NEXT_DISABLE_VERSION_CHECK: '1' },
  },
  testDir: './tests/e2e',
  use: {
    baseURL: 'http://localhost:3000',
    headless: true,
  },
});
