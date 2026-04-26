import { defineConfig } from '../../../tests/e2e/playwright';

export default defineConfig({
  testDir: '.',
  outputDir: './test-results',
  use: {
    baseURL: 'http://localhost:3100',
    headless: true,
  },
});
