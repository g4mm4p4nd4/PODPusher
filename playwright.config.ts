import type { PlaywrightTestConfig } from '@playwright/test';

const config: PlaywrightTestConfig = {
  testDir: 'tests/e2e',
  webServer: {
    command: 'npm run dev --prefix client',
    port: 3000,
    timeout: 120 * 1000,
    reuseExistingServer: true,
  },
};
export default config;
