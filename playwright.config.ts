import { PlaywrightTestConfig } from '@playwright/test';

const config: PlaywrightTestConfig = {
  testDir: './tests/e2e',
  webServer: {
    command: 'npm run dev --prefix client',
    port: 3000,
    timeout: 120000,
  },
};
export default config;
