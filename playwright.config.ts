import { defineConfig } from '@playwright/test';

const skipWebServer = process.env.PLAYWRIGHT_SKIP_WEB_SERVER === '1';

export default defineConfig({
  webServer: skipWebServer
    ? undefined
    : {
        command: 'cd client && npm run build && npm run start -- --port 3100',
        port: 3100,
        timeout: 300 * 1000,
        reuseExistingServer: !process.env.CI,
        env: { NEXT_DISABLE_VERSION_CHECK: '1' },
      },
  testDir: './tests/e2e',
  use: {
    baseURL: 'http://localhost:3100',
    headless: true,
  },
});
