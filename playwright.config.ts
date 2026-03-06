import { defineConfig } from '@playwright/test';

export default defineConfig({
  webServer: {
    command: 'cd client && npm run build && npm run start -- --port 3100',
    port: 3100,
    timeout: 120 * 1000,
    reuseExistingServer: false,
    env: { NEXT_DISABLE_VERSION_CHECK: '1' },
  },
  testDir: './tests/e2e',
  use: {
    baseURL: 'http://localhost:3100',
    headless: true,
  },
});
